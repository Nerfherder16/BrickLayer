"""
bl/fixloop.py — Fix loop integration (C-06).

After a FAILURE verdict, spawns a blocking Claude fix-agent subprocess that
reads the finding and repairs the target code. Then re-runs the question to
confirm HEALTHY. Max 2 attempts before giving up.

Only active when cfg.fix_loop_enabled = True (set by --fix-loop flag).
"""

import sys
from pathlib import Path

from bl.config import cfg
from bl.tmux import spawn_agent, wait_for_agent


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter between first two --- markers."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "".join(lines[i + 1 :])
    return text


def _append_fix_note(finding_path: Path, attempt: int, status: str, note: str) -> None:
    """Append a fix attempt section to the finding file."""
    section = f"\n## Fix Attempt {attempt} — {status}\n\n{note}\n"
    try:
        with open(finding_path, "a", encoding="utf-8") as f:
            f.write(section)
    except OSError as e:
        print(
            f"[fix-loop] Warning: could not append to {finding_path}: {e}",
            file=sys.stderr,
        )


def _spawn_fix_agent(question: dict, result: dict, finding_path: Path) -> bool:
    """Spawn the fix-agent as a blocking subprocess. Returns True if exit 0."""
    agent_path = cfg.autosearch_root / "agents" / "fix-agent.md"
    if not agent_path.exists():
        print(
            f"[fix-loop] fix-agent.md not found at {agent_path} — skipping",
            file=sys.stderr,
        )
        return False

    agent_body = _strip_frontmatter(agent_path.read_text(encoding="utf-8"))

    finding_content = ""
    try:
        finding_content = finding_path.read_text(encoding="utf-8")[:3000]
    except OSError:
        finding_content = "(finding file not readable)"

    assignment = f"""## Your Assignment

**question_id**: {question["id"]}
**question_title**: {question["title"]}
**question_mode**: {question["mode"]}
**test_command**: {question.get("test", "see finding")}
**target**: {question.get("target", "see finding")}
**failure_summary**: {result.get("summary", "")}
**failure_details**: {result.get("details", "")[:800]}
**failure_type**: {result.get("failure_type", "unknown")}

## Finding Content

{finding_content}"""

    full_prompt = f"{agent_body}\n\n---\n\n{assignment}"

    try:
        fix_spawn = spawn_agent(
            agent_name="fix-agent",
            prompt=full_prompt,
            dangerously_skip_permissions=True,
            capture_output=False,
            output_format=None,
        )
    except FileNotFoundError:
        print(
            "[fix-loop] claude CLI not found — cannot spawn fix agent", file=sys.stderr
        )
        return False

    fix_result = wait_for_agent(fix_spawn, timeout=600)

    if fix_result.exit_code == -1:
        print("[fix-loop] Fix agent timed out after 10 minutes", file=sys.stderr)
        return False

    return fix_result.exit_code == 0


def run_fix_loop(
    question: dict,
    result: dict,
    finding_path: Path,
    max_attempts: int = 2,
) -> dict:
    """
    Attempt to fix a FAILURE verdict by spawning a fix agent and re-running.

    Returns the final result dict — either a HEALTHY re-run result or the
    original result if all attempts are exhausted.
    """
    if result.get("verdict") != "FAILURE":
        return result

    from bl.runners import run_question

    for attempt in range(1, max_attempts + 1):
        print(
            f"[fix-loop] Attempt {attempt}/{max_attempts} for {question['id']}...",
            file=sys.stderr,
        )
        _append_fix_note(finding_path, attempt, "RUNNING", "Fix agent spawned")

        success = _spawn_fix_agent(question, result, finding_path)

        if not success:
            _append_fix_note(finding_path, attempt, "FAILED", "Agent exited non-zero")
            continue

        new_result = run_question(question)
        print(
            f"[fix-loop] Re-run verdict: {new_result['verdict']}",
            file=sys.stderr,
        )

        if new_result.get("verdict") == "HEALTHY":
            _append_fix_note(
                finding_path, attempt, "RESOLVED", new_result.get("summary", "")
            )
            print(
                f"[fix-loop] {question['id']} RESOLVED on attempt {attempt}",
                file=sys.stderr,
            )
            return new_result

        _append_fix_note(finding_path, attempt, "FAILED", new_result.get("summary", ""))

    _append_fix_note(
        finding_path,
        max_attempts,
        "EXHAUSTED",
        "Max attempts reached — human intervention required",
    )
    print(
        f"[fix-loop] {question['id']} exhausted {max_attempts} attempt(s) — still FAILURE",
        file=sys.stderr,
    )
    return result
