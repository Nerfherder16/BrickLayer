"""
bl/ci/run_campaign.py — CI campaign runner for GitHub Actions (3.07).

Reads questions.md from a BrickLayer project, runs PENDING questions (up to
--max-questions) using the registered runner registry, and writes a JSON
results file with a formatted pr_comment field for posting to GitHub PRs.

Usage:
    python -m bl.ci.run_campaign --project . --output bl-results.json --max-questions 10

Exit codes:
    0 — completed (even if findings contain FAILUREs — let the workflow decide)
    1 — unrecoverable setup error (should not block CI; catch and exit 0 externally)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# questions.md parser
# ---------------------------------------------------------------------------

# BL 2.0 block format: ## ID [MODE] Title
_BL2_BLOCK_RE = re.compile(
    r"^## ([\w][\w.-]*) \[(\w+)\] (.+?)$",
    re.MULTILINE,
)
_BL2_FIELD_RE = re.compile(
    r"^\*\*(Mode|Status|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source)\*\*:\s*(.+?)(?=\n\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)

# BL 2.0 table format: | ID | Mode | Status | Question |
_TABLE_ROW_4COL_RE = re.compile(
    r"^\|\s*([\w.-]+)\s*\|\s*([\w_-]+)\s*\|\s*([\w_]+)\s*\|(.+?)\|?\s*$",
    re.MULTILINE,
)
# Legacy 3-column table format: | ID | Status | Question |
_TABLE_ROW_RE = re.compile(
    r"^\|\s*([\w.]+)\s*\|\s*(PENDING|IN_PROGRESS|DONE|INCONCLUSIVE)\s*\|(.+?)\|?\s*$",
    re.MULTILINE,
)


def _parse_questions_bl2(text: str) -> list[dict]:
    """Parse BL 2.0 block-format questions.md."""
    matches = list(_BL2_BLOCK_RE.finditer(text))
    questions = []

    for i, m in enumerate(matches):
        qid = m.group(1)
        bracket_mode = m.group(2).lower()
        title = m.group(3).strip()

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        fields: dict[str, str] = {}
        for fm in _BL2_FIELD_RE.finditer(body):
            key = fm.group(1).lower().replace(" ", "_")
            fields[key] = fm.group(2).strip()

        # Explicit **Status** in body takes priority; fall back to PENDING
        # All BL 2.0 status values are preserved — only truly unknown values
        # default to PENDING.
        status = fields.get("status", "PENDING").upper()
        _KNOWN_STATUSES = (
            "PENDING",
            "IN_PROGRESS",
            "DONE",
            "INCONCLUSIVE",
            # BL 2.0 parked statuses
            "DIAGNOSIS_COMPLETE",
            "PENDING_EXTERNAL",
            "FIXED",
            "FIX_FAILED",
            "COMPLIANT",
            "NON_COMPLIANT",
            "CALIBRATED",
            "BLOCKED",
            "WARNING",
            "FAILURE",
            "HEALTHY",
        )
        if status not in _KNOWN_STATUSES:
            status = "PENDING"

        # Explicit **Mode** in body overrides the bracket tag
        mode = fields.get("mode", bracket_mode)

        questions.append(
            {
                "id": qid,
                "mode": mode,
                "title": title,
                "status": status,
                "target": fields.get("target", ""),
                "hypothesis": fields.get("hypothesis", ""),
                "test": fields.get("test", ""),
                "verdict_threshold": fields.get("verdict_threshold", ""),
                "agent_name": fields.get("agent", "").strip(),
            }
        )

    return questions


_TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        # BL 1.x
        "DONE",
        "INCONCLUSIVE",
        # BL 2.0 terminal verdicts that park a question
        "DIAGNOSIS_COMPLETE",
        "PENDING_EXTERNAL",
        "FIXED",
        "FIX_FAILED",
        "COMPLIANT",
        "NON_COMPLIANT",
        "CALIBRATED",
        "BLOCKED",
        "WARNING",
        "FAILURE",
        "HEALTHY",
    }
)


def _parse_questions_table(text: str) -> list[dict]:
    """Parse table-format questions.md.

    Supports both:
    - BL 2.0 four-column: | ID | Mode | Status | Question |
    - Legacy three-column: | ID | Status | Question |

    Four-column format is tried first. All BL 2.0 status values are preserved
    (not normalised to PENDING), so parked questions (PENDING_EXTERNAL,
    DIAGNOSIS_COMPLETE, BLOCKED, etc.) are not accidentally re-queued.
    """
    questions = []

    # Try 4-column BL 2.0 format first
    for m in _TABLE_ROW_4COL_RE.finditer(text):
        qid = m.group(1).strip()
        # Skip header separator rows (|----|-----|...)
        if re.match(r"^[-|: ]+$", qid):
            continue
        op_mode = m.group(2).strip().lower()
        status = m.group(3).strip().upper()
        title = m.group(4).strip()

        # Skip header rows (id/mode/status column names)
        if qid.lower() in ("id", "qid", "#"):
            continue

        questions.append(
            {
                "id": qid,
                "mode": "agent",  # BL 2.0 table questions use the agent runner
                "operational_mode": op_mode,
                "title": title,
                "status": status,
                "target": "",
                "hypothesis": "",
                "test": "",
                "verdict_threshold": "",
                "agent_name": "",
            }
        )

    if questions:
        return questions

    # Fall back to legacy 3-column format
    for m in _TABLE_ROW_RE.finditer(text):
        qid = m.group(1).strip()
        status = m.group(2).strip().upper()
        title = m.group(3).strip()
        questions.append(
            {
                "id": qid,
                "mode": "simulate",  # default for legacy projects
                "operational_mode": "",
                "title": title,
                "status": status,
                "target": "",
                "hypothesis": "",
                "test": "",
                "verdict_threshold": "",
                "agent_name": "",
            }
        )
    return questions


def parse_questions(project_path: Path) -> list[dict]:
    """
    Parse questions.md from the project directory.

    Tries BL 2.0 block format first (## ID [MODE] Title), then falls back
    to the legacy table format. Returns an empty list if no file is found.
    """
    questions_file = project_path / "questions.md"
    if not questions_file.exists():
        return []

    text = questions_file.read_text(encoding="utf-8")

    # Try BL 2.0 format first — it's the primary format
    bl2_questions = _parse_questions_bl2(text)
    if bl2_questions:
        return bl2_questions

    # Fall back to legacy table format
    return _parse_questions_table(text)


# ---------------------------------------------------------------------------
# Runner dispatch
# ---------------------------------------------------------------------------


def _load_mode_context(project_path: Path, operational_mode: str) -> str:
    """Load modes/{operational_mode}.md as loop context. Returns empty string if not found."""
    if not operational_mode:
        return ""
    mode_file = project_path / "modes" / f"{operational_mode}.md"
    if mode_file.exists():
        return mode_file.read_text(encoding="utf-8")
    return ""


def _dispatch(question: dict, project_path: Path | None = None) -> dict:
    """
    Run a question using the registered BrickLayer runner for its mode.

    Injects mode_context from modes/{operational_mode}.md when an operational_mode
    is set on the question, so agents receive mode program instructions.

    Returns a verdict envelope:
        {verdict, summary, data, details, question_id, mode}
    """
    from bl.runners import run_question  # type: ignore[import]

    # Inject mode context if operational_mode is set and not already present
    op_mode = question.get("operational_mode", "")
    if op_mode and not question.get("mode_context") and project_path is not None:
        ctx = _load_mode_context(project_path, op_mode)
        if ctx:
            question = dict(question)  # don't mutate the original
            question["mode_context"] = ctx

    try:
        return run_question(question)
    except Exception as exc:  # noqa: BLE001
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Runner error: {exc}",
            "data": {"error": str(exc)},
            "details": f"Unhandled exception in runner for mode '{question.get('mode', '?')}':\n{exc}",
            "question_id": question.get("id", "?"),
            "mode": question.get("mode", "?"),
        }


# ---------------------------------------------------------------------------
# PR comment formatter
# ---------------------------------------------------------------------------

_VERDICT_EMOJI = {
    "HEALTHY": "✅",
    "WARNING": "⚠️",
    "FAILURE": "❌",
    "INCONCLUSIVE": "❓",
}

_TERMINAL_VERDICTS = frozenset(("FAILURE", "WARNING", "HEALTHY", "INCONCLUSIVE"))


def _overall_verdict(results: list[dict]) -> str:
    """Return the worst-case verdict across all results."""
    if not results:
        return "INCONCLUSIVE"
    order = ["FAILURE", "WARNING", "HEALTHY", "INCONCLUSIVE"]
    for v in order:
        if any(r["verdict"] == v for r in results):
            return v
    return "INCONCLUSIVE"


def _format_pr_comment(
    results: list[dict],
    questions_run: int,
    questions_pending: int,
    overall_verdict: str,
    branch: str,
) -> str:
    """Build the markdown PR comment body."""
    emoji = _VERDICT_EMOJI.get(overall_verdict, "❓")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "## BrickLayer Campaign Results",
        "",
        f"**Branch:** `{branch}` | **Questions run:** {questions_run} | "
        f"**Status:** {emoji} {overall_verdict}",
        "",
    ]

    if results:
        lines += [
            "| Question | Verdict | Summary |",
            "|----------|---------|---------|",
        ]
        for r in results:
            qid = r.get("question_id", r.get("id", "?"))
            verdict = r.get("verdict", "INCONCLUSIVE")
            summary = r.get("summary", "")
            # Truncate long summaries for the table
            if len(summary) > 100:
                summary = summary[:97] + "..."
            v_emoji = _VERDICT_EMOJI.get(verdict, "❓")
            lines.append(f"| {qid} | {v_emoji} {verdict} | {summary} |")

        lines.append("")

        # Findings section — only failures and warnings
        notable = [r for r in results if r.get("verdict") in ("FAILURE", "WARNING")]
        if notable:
            lines.append("### Findings")
            lines.append("")
            for r in notable:
                qid = r.get("question_id", r.get("id", "?"))
                verdict = r.get("verdict", "?")
                v_emoji = _VERDICT_EMOJI.get(verdict, "❓")
                summary = r.get("summary", "")
                details = r.get("details", "")
                lines.append(f"**{v_emoji} {qid}**: {summary}")
                if details and details != summary:
                    # Show up to first 300 chars of details
                    excerpt = details[:300].strip()
                    if len(details) > 300:
                        excerpt += "..."
                    lines.append(f"```\n{excerpt}\n```")
                lines.append("")

    if questions_pending > 0:
        lines.append(
            f"> {questions_pending} question(s) not run (limit reached or not PENDING)."
        )
        lines.append("")

    lines += [
        "---",
        f"*Run by [BrickLayer 2.0](https://github.com/Nerfherder16/Bricklayer2.0) · {now}*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bl.ci.run_campaign",
        description="Run a BrickLayer campaign in CI and emit a JSON results file.",
    )
    parser.add_argument(
        "--project",
        default=".",
        help="Path to the BrickLayer project directory (default: current dir)",
    )
    parser.add_argument(
        "--output",
        default="bl-results.json",
        help="Path to write the JSON results file (default: bl-results.json)",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=10,
        help="Maximum number of PENDING questions to run (default: 10)",
    )
    args = parser.parse_args(argv)

    project_path = Path(args.project).resolve()
    output_path = Path(args.output)
    max_questions = args.max_questions

    # --- Graceful no-op if project has no questions.md ---
    questions_file = project_path / "questions.md"
    if not questions_file.exists():
        print(
            f"[bl-ci] No questions.md found at {questions_file} — skipping campaign.",
            file=sys.stderr,
        )
        _write_empty_results(output_path, "no questions.md found")
        return 0

    # --- Parse questions ---
    all_questions = parse_questions(project_path)
    if not all_questions:
        print(
            f"[bl-ci] questions.md at {questions_file} contains no parseable questions — skipping.",
            file=sys.stderr,
        )
        _write_empty_results(output_path, "no parseable questions found")
        return 0

    pending = [q for q in all_questions if q["status"] == "PENDING"]
    to_run = pending[:max_questions]
    remaining_pending = len(pending) - len(to_run)

    print(
        f"[bl-ci] Found {len(all_questions)} questions, "
        f"{len(pending)} PENDING, running {len(to_run)} (max={max_questions})",
        file=sys.stderr,
    )

    if not to_run:
        print("[bl-ci] No PENDING questions to run.", file=sys.stderr)
        _write_empty_results(output_path, "no PENDING questions")
        return 0

    # --- Point bl.config at this project so runners resolve paths correctly ---
    _init_bl_config(project_path)

    # --- Run questions ---
    results: list[dict] = []
    for q in to_run:
        qid = q["id"]
        print(
            f"[bl-ci] Running {qid} [{q['mode']}]: {q['title'][:60]}", file=sys.stderr
        )
        result = _dispatch(q, project_path=project_path)
        results.append(result)
        verdict = result.get("verdict", "?")
        summary = result.get("summary", "")[:80]
        print(f"[bl-ci]   → {verdict}: {summary}", file=sys.stderr)

    # --- Build output ---
    overall = _overall_verdict(results)
    branch = (
        os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or "unknown"
    )

    serialisable_results = []
    for r in results:
        serialisable_results.append(
            {
                "id": r.get("question_id", r.get("id", "?")),
                "verdict": r.get("verdict", "INCONCLUSIVE"),
                "summary": r.get("summary", ""),
                "details": r.get("details", ""),
                "mode": r.get("mode", ""),
                "data": r.get("data", {}),
            }
        )

    pr_comment = _format_pr_comment(
        results=serialisable_results,
        questions_run=len(to_run),
        questions_pending=remaining_pending,
        overall_verdict=overall,
        branch=branch,
    )

    output = {
        "questions_run": len(to_run),
        "questions_pending": remaining_pending,
        "overall_verdict": overall,
        "branch": branch,
        "results": serialisable_results,
        "pr_comment": pr_comment,
    }

    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[bl-ci] Results written to {output_path}", file=sys.stderr)
    print(f"[bl-ci] Overall verdict: {overall}", file=sys.stderr)

    return 0


def _init_bl_config(project_path: Path) -> None:
    """Point bl.config.cfg at the project directory so runners resolve paths correctly."""
    try:
        from bl.config import cfg  # type: ignore[import]

        cfg.project_root = project_path
        cfg.findings_dir = project_path / "findings"
        cfg.results_tsv = project_path / "results.tsv"
        cfg.questions_md = project_path / "questions.md"
        cfg.history_db = project_path / "history.db"
        cfg.agents_dir = project_path / ".claude" / "agents"
        cfg.findings_dir.mkdir(exist_ok=True)
    except ImportError:
        # bl not installed — runners that don't need cfg will still work
        pass


def _write_empty_results(output_path: Path, reason: str) -> None:
    """Write a zero-results JSON so downstream workflow steps don't fail on missing file."""
    branch = (
        os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or "unknown"
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pr_comment = (
        "## BrickLayer Campaign Results\n\n"
        f"No questions were run ({reason}).\n\n"
        "---\n"
        f"*Run by [BrickLayer 2.0](https://github.com/Nerfherder16/Bricklayer2.0) · {now}*"
    )
    output = {
        "questions_run": 0,
        "questions_pending": 0,
        "overall_verdict": "INCONCLUSIVE",
        "branch": branch,
        "results": [],
        "pr_comment": pr_comment,
    }
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
