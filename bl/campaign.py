"""
bl/campaign.py — Campaign orchestration loop.

Handles the outer loop: running and recording questions, sentinel checks
(Forge, Audit, OVERRIDE), peer-reviewer spawning, and end-of-run housekeeping.
"""

import json
import os
import re
import shutil
import subprocess
import sys

from bl.config import cfg
from bl.findings import classify_failure_type, update_results_tsv, write_finding
from bl.history import detect_regression, record_verdict
from bl.questions import get_question_by_id, get_next_pending, parse_questions
from bl.runners import run_question
from bl.runners.agent import _strip_frontmatter


# ---------------------------------------------------------------------------
# BL 2.0: Mode context loader
# ---------------------------------------------------------------------------


def _load_mode_context(operational_mode: str) -> str:
    """Load the mode program markdown for the given operational mode."""
    if not operational_mode:
        return ""
    modes_dir = cfg.project_root / "modes"
    mode_file = modes_dir / f"{operational_mode}.md"
    if mode_file.exists():
        return mode_file.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# Core run-and-record
# ---------------------------------------------------------------------------


def run_and_record(question: dict) -> dict:
    """Run a single question, write finding, update results.tsv, print JSON."""
    qid = question["id"]
    print(
        f"Running {qid} [{question['mode']}]: {question['title']}",
        file=sys.stderr,
    )
    # BL 2.0: inject operational mode context
    op_mode = question.get("operational_mode", "")
    if op_mode:
        mode_ctx = _load_mode_context(op_mode)
        if mode_ctx:
            question = dict(question)
            question["mode_context"] = mode_ctx

    # BL 2.0: inject session context from previous findings this session
    session_ctx_path = cfg.project_root / "session-context.md"
    session_context = ""
    if session_ctx_path.exists():
        text = session_ctx_path.read_text(encoding="utf-8")
        session_context = text[-2000:] if len(text) > 2000 else text
    if session_context:
        question = dict(question)
        question["session_context"] = session_context

    # BL 2.0: search Recall for relevant prior context (optional, graceful-fail)
    try:
        from bl.recall_bridge import search_before_question

        project_name = cfg.project_root.name
        recall_ctx = search_before_question(question, project_name)
        if recall_ctx:
            question = dict(question)  # may already be a copy from above
            existing_ctx = question.get("session_context", "")
            question["session_context"] = (recall_ctx + "\n" + existing_ctx).strip()
    except Exception:
        pass  # Recall bridge is optional — never block campaign on it

    result = run_question(question)
    failure_type = classify_failure_type(result, question["mode"])
    if failure_type:
        result["failure_type"] = failure_type
    finding_path = write_finding(question, result)
    update_results_tsv(qid, result["verdict"], result["summary"], failure_type)

    # Record to history ledger and check for regression
    record_verdict(
        qid,
        result["verdict"],
        summary=result.get("summary", ""),
        failure_type=failure_type,
    )
    regression = detect_regression(qid, result["verdict"])
    if regression:
        print(
            f"\n[REGRESSION] {qid}: {regression['previous_verdict']} → {result['verdict']}"
            f" (was: {regression['previous_timestamp']})",
            file=sys.stderr,
        )
        result["regression"] = regression

    # C-04: adaptive follow-up drill-down on FAILURE/WARNING
    if result.get("verdict") in ("FAILURE", "WARNING"):
        from bl.followup import generate_followup

        followup_ids = generate_followup(question, result, cfg.questions_md)
        if followup_ids:
            result["followup_questions"] = followup_ids

    # C-06: fix loop — attempt to repair FAILURE automatically (opt-in, BL 1.x)
    if (
        result.get("verdict") == "FAILURE"
        and os.environ.get("BRICKLAYER_FIX_LOOP") == "1"
    ):
        from bl.fixloop import run_fix_loop

        finding_path = cfg.findings_dir / f"{qid}.md"
        fixed_result = run_fix_loop(question, result, finding_path)
        if fixed_result.get("verdict") == "HEALTHY":
            update_results_tsv(
                qid, "HEALTHY", fixed_result.get("summary", "Fixed"), None
            )
            result = fixed_result

    # BL 2.0: self-healing loop — diagnose-analyst → fix-implementer → repeat (opt-in)
    if (
        result.get("verdict") in ("FAILURE", "DIAGNOSIS_COMPLETE")
        and os.environ.get("BRICKLAYER_HEAL_LOOP") == "1"
    ):
        from bl.healloop import run_heal_loop

        heal_finding_path = cfg.findings_dir / f"{qid}.md"
        healed_result = run_heal_loop(question, result, heal_finding_path)
        if (
            healed_result is not result
        ):  # F2.4: identity check — always propagate heal loop output
            result = healed_result

    # BL 2.0: append one-line insight to session-context.md
    insight_line = f"[{qid}] {result['verdict']} [{question.get('operational_mode', question['mode'])}]: {result['summary'][:120]}\n"
    with open(session_ctx_path, "a", encoding="utf-8") as f:
        f.write(insight_line)

    # BL 2.0: store significant findings to Recall
    try:
        from bl.recall_bridge import store_finding

        project_name = cfg.project_root.name
        store_finding(question, result, project_name)
    except Exception:
        pass  # optional — never block campaign on it

    print(json.dumps(result, indent=2))
    print(f"\nFinding written to: {finding_path}", file=sys.stderr)
    print(f"Verdict: {result['verdict']}", file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# End-of-run helpers
# ---------------------------------------------------------------------------


def print_handoff_reminder() -> None:
    """Print end-of-run cross-project handoff check."""
    handoffs_dir = cfg.autosearch_root / "handoffs"
    print("\n" + "=" * 60, file=sys.stderr)
    print("END-OF-RUN HANDOFF CHECK", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("Did this campaign find changes needed in another project?", file=sys.stderr)
    print(
        "  YES → Create autosearch/handoffs/handoff-{project}-{date}.md",
        file=sys.stderr,
    )
    print("  NO  → Session complete.", file=sys.stderr)
    existing = (
        sorted(handoffs_dir.glob("handoff-*.md")) if handoffs_dir.exists() else []
    )
    if existing:
        print(f"\nOpen handoffs ({len(existing)}):", file=sys.stderr)
        for h in existing:
            print(f"  {h.name}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


def run_retrospective() -> None:
    """Run the retrospective agent to improve BrickLayer from session learnings."""
    import datetime

    retro_path = cfg.agents_dir / "retrospective.md"
    if not retro_path.exists():
        print("retrospective.md not found in agents/")
        return

    body = _strip_frontmatter(retro_path.read_text(encoding="utf-8"))

    results_content = "(no results yet)"
    if cfg.results_tsv.exists():
        results_content = cfg.results_tsv.read_text(encoding="utf-8")

    project_cfg: dict = {}
    cfg_path = cfg.project_root / "project.json"
    if cfg_path.exists():
        project_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    project_display = project_cfg.get("display_name", "Unknown")

    questions = [
        "1. Verdict accuracy: Which verdicts were INCONCLUSIVE, wrong, or needed manual correction? Why?",
        "2. Agent output: Did any agent report DONE without a green test run? What broke?",
        "3. Question quality: Any vacuous results (0 assertions)? Questions too narrow or too broad?",
        "4. Coverage gaps: Any failure modes found with no agent to fix them?",
        "5. Parallelization: Which questions had no dependencies and could have run simultaneously?",
        "6. Fix quality: Any committed fix later found speculative or wrong?",
        "7. Highest-value finding this session?",
        "8. Biggest time sink with least value?",
    ]

    print("\n" + "=" * 60)
    print(f"BrickLayer Retrospective — {project_display}")
    print("=" * 60)
    print("Answer each question. Press Enter twice to move to the next.\n")

    answers = []
    for q in questions:
        print(f"\n{q}")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        answers.append("\n".join(lines).strip())

    reflection_text = "\n\n".join(
        f"**{questions[i]}**\n{answers[i]}" for i in range(len(questions))
    )

    prompt = f"""{body}

---

## Your Assignment

**Project**: {project_display}
**Autosearch root**: {cfg.autosearch_root}
**Session date**: {datetime.datetime.now().strftime("%Y-%m-%d")}

**Results TSV**:
{results_content}

**User Reflection**:
{reflection_text}

Review the session artifacts and reflection answers. Apply concrete improvements to BrickLayer. Commit to the autosearch repo if git is available. Output your Retrospective Report when done."""

    claude_bin = shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    print("\n" + "=" * 60)
    print("Running Retrospective agent...")
    print("=" * 60 + "\n")

    try:
        subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=False,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=600,
        )
    except FileNotFoundError:
        print("claude CLI not found — cannot run retrospective agent.")
    except subprocess.TimeoutExpired:
        print("Retrospective agent timed out after 10 minutes.")


# ---------------------------------------------------------------------------
# Sentinel / meta-agent helpers
# ---------------------------------------------------------------------------


def _spawn_agent_background(agent_name: str, context: str) -> None:
    """Spawn a meta-agent as a background subprocess. Non-blocking."""
    agent_path = cfg.agents_dir / f"{agent_name}.md"
    if not agent_path.exists():
        print(f"[campaign] {agent_name}.md not found — skipping", file=sys.stderr)
        return

    agent_prompt = _strip_frontmatter(agent_path.read_text(encoding="utf-8"))
    full_prompt = f"{agent_prompt}\n\n---\n\n## Your Assignment\n\n{context}"

    claude_bin = shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        proc = subprocess.Popen(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=child_env,
        )
        proc.stdin.write(full_prompt)
        proc.stdin.close()
        print(
            f"[campaign] {agent_name} spawned in background (pid={proc.pid})",
            file=sys.stderr,
        )
    except (FileNotFoundError, OSError) as e:
        print(f"[campaign] Failed to spawn {agent_name}: {e}", file=sys.stderr)


def _run_forge_blocking() -> None:
    """Run Forge synchronously when FORGE_NEEDED.md exists. Blocks until done."""
    forge_needed = cfg.agents_dir / "FORGE_NEEDED.md"
    if not forge_needed.exists():
        return

    agent_path = cfg.agents_dir / "forge.md"
    if not agent_path.exists():
        print("[campaign] forge.md not found — cannot fill gap", file=sys.stderr)
        return

    agent_prompt = _strip_frontmatter(agent_path.read_text(encoding="utf-8"))
    context = (
        f"**forge_needed_md**: {forge_needed}\n"
        f"**agents_dir**: {cfg.agents_dir}\n"
        f"**findings_dir**: {cfg.findings_dir}\n"
        f"**schema_md**: {cfg.agents_dir / 'SCHEMA.md'}\n\n"
        f"Read FORGE_NEEDED.md, build agents from the evidence findings, write them to "
        f"agents_dir, append to FORGE_LOG.md, then delete FORGE_NEEDED.md to unblock "
        f"the campaign loop."
    )
    full_prompt = f"{agent_prompt}\n\n---\n\n## Your Assignment\n\n{context}"

    claude_bin = shutil.which("claude") or "claude"
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    print(
        "\n[campaign] FORGE_NEEDED.md detected — running Forge (blocking)...",
        file=sys.stderr,
    )
    try:
        subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=full_prompt,
            capture_output=False,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=600,
        )
    except FileNotFoundError:
        print("[campaign] claude CLI not found — cannot run Forge", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("[campaign] Forge timed out — continuing campaign", file=sys.stderr)


def _inject_override_questions() -> None:
    """Scan findings for OVERRIDE peer review verdicts; inject re-exam PENDING questions."""
    if not cfg.findings_dir.exists():
        return
    if not cfg.questions_md.exists():
        return

    override_pattern = re.compile(
        r"## Peer Review.*?\*\*Verdict\*\*:\s*OVERRIDE", re.DOTALL
    )

    questions_text = cfg.questions_md.read_text(encoding="utf-8")

    injected = 0
    for finding_file in sorted(cfg.findings_dir.glob("Q*.md")):
        content = finding_file.read_text(encoding="utf-8")
        if not override_pattern.search(content):
            continue

        qid = finding_file.stem
        reexam_marker = f"Re-examine {qid}"
        if reexam_marker in questions_text:
            continue

        reexam_block = f"""
---

## {qid}.R [CORRECTNESS] Re-examine {qid}
**Mode**: agent
**Status**: PENDING
**Hypothesis**: Peer review returned OVERRIDE — the prior fix for {qid} is incomplete or incorrect.
**Test**: Re-run the original test command from {qid} and confirm the concern raised in the ## Peer Review section is resolved.
**Verdict threshold**:
- HEALTHY: Original test passes and peer-reviewer concern is addressed
- FAILURE: Test still fails or new issue confirmed
"""
        with open(cfg.questions_md, "a", encoding="utf-8") as f:
            f.write(reexam_block)

        questions_text += reexam_block

        print(
            f"[campaign] OVERRIDE in {finding_file.name} → injected {qid}.R re-exam question",
            file=sys.stderr,
        )
        injected += 1

    if injected:
        print(
            f"[campaign] {injected} re-exam question(s) added to questions.md",
            file=sys.stderr,
        )


def check_sentinels() -> None:
    """Wave-start check: FORGE_NEEDED (blocking) → AUDIT_REPORT (advisory) → OVERRIDE verdicts."""
    _run_forge_blocking()

    audit_report = cfg.agents_dir / "AUDIT_REPORT.md"
    if audit_report.exists():
        print(
            "\n[campaign] AUDIT_REPORT.md available — fleet recommendations:",
            file=sys.stderr,
        )
        print(audit_report.read_text(encoding="utf-8")[:1500], file=sys.stderr)
        print(
            "[campaign] Review and apply RETIRE/PROMOTE/UPDATE TRIGGERS manually, "
            "then delete AUDIT_REPORT.md to dismiss.",
            file=sys.stderr,
        )

    _inject_override_questions()


# ---------------------------------------------------------------------------
# Campaign loop
# ---------------------------------------------------------------------------


def _preflight_mode_check(pending: list[dict]) -> list[dict]:
    """Warn about unregistered modes or missing agent files; return questions that can run."""
    from bl.runners.base import registered_modes

    valid = set(registered_modes())
    skipped = []
    runnable = []
    for q in pending:
        if q["mode"] not in valid:
            skipped.append((q, "mode_missing", f"mode '{q['mode']}' not registered"))
        elif q["mode"] == "agent" and q.get("agent_name"):
            agent_file = cfg.agents_dir / f"{q['agent_name']}.md"
            if not agent_file.exists():
                available = [
                    f.stem for f in cfg.agents_dir.glob("*.md") if f.stem != "SCHEMA"
                ]
                skipped.append(
                    (
                        q,
                        "agent_missing",
                        f"agent file '{q['agent_name']}.md' not found — available: {available}",
                    )
                )
            else:
                runnable.append(q)
        else:
            runnable.append(q)
    if skipped:
        print(
            f"\n[C-28] Pre-flight: {len(skipped)} question(s) blocked — will record INCONCLUSIVE immediately:",
            file=sys.stderr,
        )
        for q, fail_class, reason in skipped:
            print(f"  {q['id']} [{fail_class}]: {reason}", file=sys.stderr)
            result = {
                "verdict": "INCONCLUSIVE",
                "summary": f"C-28 {fail_class}: {reason}",
                "data": {"registered_modes": sorted(valid), "fail_class": fail_class},
                "details": (
                    f"Pre-flight check blocked question '{q['id']}': {reason}. "
                    "Fix the question's Agent or Mode field to continue."
                ),
                "failure_type": "configuration",
                "confidence": "high",
            }
            write_finding(q, result)
            update_results_tsv(
                q["id"], result["verdict"], result["summary"], "configuration"
            )
        print(f"[C-28] {len(runnable)} question(s) will run normally.", file=sys.stderr)
    return runnable


def _reactivate_pending_external(questions: list[dict]) -> int:
    """
    Re-activate PENDING_EXTERNAL questions whose resume_after date has passed.
    Updates results.tsv to remove the row so the question becomes PENDING again.
    Returns count of reactivated questions.
    """
    from datetime import datetime, timezone

    if not cfg.results_tsv.exists():
        return 0

    now = datetime.now(timezone.utc)
    reactivated = 0

    lines = cfg.results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    new_lines = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip() == "PENDING_EXTERNAL":
            qid = parts[0]
            q = next((q for q in questions if q["id"] == qid), None)
            resume_after = q.get("resume_after", "") if q else ""
            reactivate = False
            if resume_after:
                try:
                    gate = datetime.fromisoformat(resume_after.replace("Z", "+00:00"))
                    reactivate = now >= gate
                except ValueError:
                    reactivate = True
            else:
                reactivate = True
            if reactivate:
                print(
                    f"[campaign] Re-activated {qid} (resume_after elapsed: {resume_after})",
                    file=sys.stderr,
                )
                reactivated += 1
                continue  # drop row → question becomes PENDING again
        new_lines.append(line)

    if reactivated:
        cfg.results_tsv.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return reactivated


def run_campaign() -> None:
    """Run all PENDING questions in sequence with sentinel checks."""
    questions = parse_questions()
    _reactivate_pending_external(questions)
    questions = parse_questions()  # re-parse after reactivation
    pending = [q for q in questions if q["status"] == "PENDING"]
    pending = _preflight_mode_check(pending)

    if not pending:
        print("No PENDING questions remain.", file=sys.stderr)
        print_handoff_reminder()
        return

    print(f"\nCampaign: {len(pending)} PENDING questions to run", file=sys.stderr)
    questions_done = 0

    for i, question in enumerate(pending, 1):
        check_sentinels()

        if questions_done > 0:
            refreshed = parse_questions()
            pending = [q for q in refreshed if q["status"] == "PENDING"]

        print(
            f"\n[{i}/{len(pending)}] {question['id']} — {question['title']}",
            file=sys.stderr,
        )
        run_and_record(question)
        questions_done += 1

        _spawn_agent_background(
            "peer-reviewer",
            f"primary_finding={cfg.findings_dir / (question['id'] + '.md')}\n"
            f"target_git={cfg.project_root.parent}\n"
            f"agents_dir={cfg.agents_dir}\n\n"
            f"Re-run the original test for {question['id']}, review the fix code, "
            f"and append a ## Peer Review section with verdict "
            f"CONFIRMED | CONCERNS | OVERRIDE to the finding file.",
        )

        if questions_done % 5 == 0:
            _spawn_agent_background(
                "forge-check",
                f"agents_dir={cfg.agents_dir}\n"
                f"findings_dir={cfg.findings_dir}\n"
                f"questions_md={cfg.questions_md}\n\n"
                f"Inventory the agent fleet, scan the 5 most recent findings, "
                f"check all PENDING questions for missing agents. "
                f"Write {cfg.agents_dir}/FORGE_NEEDED.md if gaps found, "
                f"otherwise output FLEET COMPLETE.",
            )

        if questions_done % 10 == 0:
            _spawn_agent_background(
                "agent-auditor",
                f"agents_dir={cfg.agents_dir}\n"
                f"findings_dir={cfg.findings_dir}\n"
                f"results_tsv={cfg.results_tsv}\n\n"
                f"Read all agents, findings, and results. "
                f"Write fleet health report to {cfg.agents_dir}/AUDIT_REPORT.md.",
            )

    print("\nCampaign complete.", file=sys.stderr)

    # Run synthesizer at end of each wave
    from bl.synthesizer import parse_recommendation, synthesize

    synthesis_result = synthesize(cfg.project_root, wave=None)
    if synthesis_result is not None:
        recommendation = parse_recommendation(
            synthesis_result.read_text(encoding="utf-8")
        )
        if recommendation == "STOP":
            print(
                "[campaign] Synthesizer recommends STOP — campaign complete",
                file=sys.stderr,
            )
            print_handoff_reminder()
            return
        if recommendation == "PIVOT":
            print(
                "[campaign] Synthesizer recommends PIVOT — see synthesis.md",
                file=sys.stderr,
            )

    # Auto-generate next wave if question bank is exhausted
    remaining = [q for q in parse_questions() if q["status"] == "PENDING"]
    if not remaining:
        print(
            "[campaign] Question bank exhausted — generating next wave hypotheses...",
            file=sys.stderr,
        )
        from bl.hypothesis import generate_hypotheses

        generate_hypotheses(cfg.questions_md, cfg.results_tsv)

    print_handoff_reminder()


def run_single(question_id: str | None, dry_run: bool = False) -> None:
    """Run a single question by ID, or the next PENDING if no ID given."""
    questions = parse_questions()

    if question_id:
        question = get_question_by_id(questions, question_id)
        if not question:
            print(
                json.dumps(
                    {
                        "error": f"Question {question_id} not found",
                        "available": [q["id"] for q in questions],
                    }
                )
            )
            sys.exit(1)
    else:
        question = get_next_pending(questions)
        if not question:
            print(
                json.dumps(
                    {
                        "verdict": "INCONCLUSIVE",
                        "summary": "No PENDING questions remain",
                        "data": {},
                        "details": "All questions answered. Generate new ones with forge.",
                    }
                )
            )
            return

    if dry_run:
        print(json.dumps(question, indent=2))
        return

    run_and_record(question)
    print_handoff_reminder()
