"""
bl/healloop.py — BrickLayer 2.0 self-healing loop.

Chains diagnose-analyst → fix-implementer → diagnose-analyst (on FIX_FAILED)
automatically, without human intervention between cycles.

State machine:
    FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer → FIXED  ✓
                                                                       → FIX_FAILED → (next cycle)
    DIAGNOSIS_COMPLETE → fix-implementer → FIXED  ✓
                                         → FIX_FAILED → diagnose-analyst → (next cycle)

Only active when BRICKLAYER_HEAL_LOOP=1 environment variable is set.
Max cycles default: 3. Override with BRICKLAYER_HEAL_MAX_CYCLES=N.

Distinct from the BL 1.x BRICKLAYER_FIX_LOOP — that still works for legacy projects.
"""

import os
import sys
from pathlib import Path

from bl.config import cfg
from bl.findings import update_results_tsv, write_finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_enabled() -> bool:
    return os.environ.get("BRICKLAYER_HEAL_LOOP") == "1"


def _max_cycles() -> int:
    try:
        return int(os.environ.get("BRICKLAYER_HEAL_MAX_CYCLES", "3"))
    except ValueError:
        return 3


def _agent_exists(agent_name: str) -> bool:
    return (cfg.agents_dir / f"{agent_name}.md").exists()


def _append_heal_note(finding_path: Path, cycle: int, status: str, note: str) -> None:
    """Append a heal cycle progress section to the original finding file."""
    section = f"\n## Heal Cycle {cycle} — {status}\n\n{note}\n"
    try:
        with open(finding_path, "a", encoding="utf-8") as f:
            f.write(section)
    except OSError as e:
        print(
            f"[heal-loop] Warning: could not append to {finding_path}: {e}",
            file=sys.stderr,
        )


def _synthetic_question(
    original_question: dict,
    agent_name: str,
    finding_id: str,
    cycle: int,
    operational_mode: str,
    extra_context: str = "",
) -> dict:
    """
    Build a synthetic question dict for run_agent() to consume.

    The synthetic question points to an existing finding file as its input context.
    The agent reads that finding, does its work, and returns a result dict.
    """
    q = dict(original_question)
    q["id"] = f"{original_question['id']}_heal{cycle}_{agent_name.split('-')[0]}"
    q["mode"] = "agent"
    q["agent_name"] = agent_name
    q["finding"] = finding_id
    q["operational_mode"] = operational_mode
    q["title"] = f"[Heal {cycle}] {agent_name} for {original_question['id']}"
    if extra_context:
        # Inject into session_context so agent sees it in the preamble
        existing = q.get("session_context", "")
        q["session_context"] = (extra_context + "\n\n" + existing).strip()
    return q


def _run_heal_agent(
    agent_name: str,
    synthetic_q: dict,
) -> dict:
    """
    Run a single heal agent (diagnose-analyst or fix-implementer) via run_agent().
    Returns the result dict.
    """
    from bl.runners.agent import run_agent

    if not _agent_exists(agent_name):
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"[heal-loop] {agent_name}.md not found in {cfg.agents_dir}",
            "data": {},
            "details": "Add the agent file to the project's .claude/agents/ directory.",
        }

    print(
        f"[heal-loop] Running {agent_name} for {synthetic_q['finding']}...",
        file=sys.stderr,
    )
    result = run_agent(synthetic_q)
    print(
        f"[heal-loop] {agent_name} → {result.get('verdict', 'UNKNOWN')}",
        file=sys.stderr,
    )
    return result


# ---------------------------------------------------------------------------
# Main heal loop
# ---------------------------------------------------------------------------


def run_heal_loop(
    original_question: dict,
    initial_result: dict,
    finding_path: Path,
) -> dict:
    """
    Run the BL 2.0 self-healing loop for a question that produced FAILURE
    or DIAGNOSIS_COMPLETE.

    Returns the final result dict (FIXED on success, or the last result on
    exhaustion).

    Writes intermediate findings to findings/{qid}_heal{n}_*.md and appends
    progress notes to the original finding file.
    """
    if not _is_enabled():
        return initial_result

    max_cycles = _max_cycles()
    original_qid = original_question["id"]
    current_verdict = initial_result.get("verdict")
    current_finding_id = original_qid  # the finding run_agent() will read

    # Only activate for FAILURE or DIAGNOSIS_COMPLETE
    if current_verdict not in ("FAILURE", "DIAGNOSIS_COMPLETE"):
        return initial_result

    print(
        f"\n[heal-loop] Starting heal loop for {original_qid} "
        f"(verdict={current_verdict}, max_cycles={max_cycles})",
        file=sys.stderr,
    )

    current_result = initial_result

    for cycle in range(1, max_cycles + 1):
        verdict = current_result.get("verdict")
        print(
            f"\n[heal-loop] Cycle {cycle}/{max_cycles} — current verdict: {verdict}",
            file=sys.stderr,
        )

        # ----------------------------------------------------------------
        # Phase 1: FAILURE → diagnose-analyst → DIAGNOSIS_COMPLETE
        # ----------------------------------------------------------------
        if verdict == "FAILURE":
            if not _agent_exists("diagnose-analyst"):
                print(
                    "[heal-loop] diagnose-analyst.md not found — cannot auto-diagnose",
                    file=sys.stderr,
                )
                _append_heal_note(
                    finding_path,
                    cycle,
                    "SKIPPED",
                    "diagnose-analyst.md missing — add it to .claude/agents/ to enable auto-diagnosis",
                )
                break

            diag_q = _synthetic_question(
                original_question,
                agent_name="diagnose-analyst",
                finding_id=current_finding_id,
                cycle=cycle,
                operational_mode="diagnose",
                extra_context=(
                    f"HEAL LOOP CONTEXT: This is cycle {cycle}/{max_cycles} of automated "
                    f"self-healing for question {original_qid}. "
                    f"The previous verdict was FAILURE. "
                    f"Read the finding at {current_finding_id}.md and identify the root cause. "
                    f"You MUST produce a DIAGNOSIS_COMPLETE verdict with a complete Fix Specification "
                    f"(target file, target location, concrete edit, verification command). "
                    f"Do not produce FAILURE — the goal is actionable root cause identification."
                ),
            )

            diag_result = _run_heal_agent("diagnose-analyst", diag_q)
            diag_verdict = diag_result.get("verdict")

            if diag_verdict != "DIAGNOSIS_COMPLETE":
                # Diagnose couldn't reach root cause — append and give up
                _append_heal_note(
                    finding_path,
                    cycle,
                    f"DIAGNOSE_{diag_verdict}",
                    f"diagnose-analyst could not reach DIAGNOSIS_COMPLETE (got {diag_verdict}): "
                    f"{diag_result.get('summary', '')}",
                )
                print(
                    f"[heal-loop] diagnose-analyst returned {diag_verdict} — cannot proceed",
                    file=sys.stderr,
                )
                break

            # Write the DIAGNOSIS_COMPLETE finding so fix-implementer can read it
            diag_q["id"] = f"{original_qid}_heal{cycle}_diag"
            write_finding(diag_q, diag_result)
            update_results_tsv(
                diag_q["id"],
                diag_result["verdict"],
                diag_result.get("summary", ""),
                None,
            )
            _append_heal_note(
                finding_path,
                cycle,
                "DIAGNOSIS_COMPLETE",
                f"diagnose-analyst identified root cause: {diag_result.get('summary', '')}",
            )

            # Advance state
            current_result = diag_result
            current_finding_id = diag_q["id"]
            verdict = "DIAGNOSIS_COMPLETE"

        # ----------------------------------------------------------------
        # Phase 2: DIAGNOSIS_COMPLETE → fix-implementer → FIXED / FIX_FAILED
        # ----------------------------------------------------------------
        if verdict == "DIAGNOSIS_COMPLETE":
            if not _agent_exists("fix-implementer"):
                print(
                    "[heal-loop] fix-implementer.md not found — cannot auto-fix",
                    file=sys.stderr,
                )
                _append_heal_note(
                    finding_path,
                    cycle,
                    "SKIPPED",
                    "fix-implementer.md missing — add it to .claude/agents/ to enable auto-fix",
                )
                break

            fix_q = _synthetic_question(
                original_question,
                agent_name="fix-implementer",
                finding_id=current_finding_id,
                cycle=cycle,
                operational_mode="fix",
                extra_context=(
                    f"HEAL LOOP CONTEXT: This is cycle {cycle}/{max_cycles} of automated "
                    f"self-healing for question {original_qid}. "
                    f"Read the DIAGNOSIS_COMPLETE finding at {current_finding_id}.md. "
                    f"Apply the specified fix exactly. Run the verification command. "
                    f"Output FIXED if the verification passes, FIX_FAILED if it does not. "
                    f"Include a Root Cause Update section on FIX_FAILED."
                ),
            )

            fix_result = _run_heal_agent("fix-implementer", fix_q)
            fix_verdict = fix_result.get("verdict")

            # Write fix finding
            fix_q["id"] = f"{original_qid}_heal{cycle}_fix"
            write_finding(fix_q, fix_result)
            update_results_tsv(
                fix_q["id"], fix_result["verdict"], fix_result.get("summary", ""), None
            )

            if fix_verdict == "FIXED":
                _append_heal_note(
                    finding_path,
                    cycle,
                    "FIXED",
                    f"fix-implementer resolved the issue: {fix_result.get('summary', '')}",
                )
                # Update original question status to FIXED in results.tsv
                update_results_tsv(
                    original_qid,
                    "FIXED",
                    f"Auto-healed in cycle {cycle}: {fix_result.get('summary', '')}",
                    None,
                )
                print(
                    f"\n[heal-loop] {original_qid} FIXED on cycle {cycle} ✓",
                    file=sys.stderr,
                )
                return fix_result

            # FIX_FAILED — loop back for next diagnose cycle
            _append_heal_note(
                finding_path,
                cycle,
                "FIX_FAILED",
                f"fix-implementer failed: {fix_result.get('summary', '')}. "
                f"Looping back to diagnose with updated hypothesis.",
            )
            current_result = fix_result
            # The FIX_FAILED finding contains the Root Cause Update — use it as input
            # for the next diagnose cycle
            current_finding_id = fix_q["id"]
            current_result["verdict"] = "FAILURE"  # re-enter as FAILURE next cycle

        # Any other verdict — bail
        else:
            print(
                f"[heal-loop] Unexpected verdict {verdict} — exiting heal loop",
                file=sys.stderr,
            )
            break

    _append_heal_note(
        finding_path,
        max_cycles,
        "EXHAUSTED",
        f"Self-healing exhausted {max_cycles} cycle(s) — human intervention required. "
        f"Review the heal cycle notes above for root cause history.",
    )
    print(
        f"[heal-loop] {original_qid} exhausted {max_cycles} cycle(s) — still unresolved",
        file=sys.stderr,
    )
    return current_result
