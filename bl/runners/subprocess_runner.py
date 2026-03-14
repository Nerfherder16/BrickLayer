"""
bl/runners/subprocess_runner.py — General subprocess command runner (C-08).

Executes arbitrary shell commands specified in the question's Test field.
Interprets exit codes and stdout patterns to determine verdict.

Handles questions with mode: subprocess

Test field syntax:
    {shell command}                   — run this command
    expect_exit: {N}                  — expected exit code (default 0)
    expect_stdout: {substring}        — stdout must contain this
    expect_not_stdout: {substring}    — stdout must NOT contain this
    timeout: {N}                      — timeout in seconds (default 30)

If the command outputs a JSON object with a "verdict" key, that verdict
takes precedence over exit-code interpretation.
"""

import json
import subprocess

from bl.config import cfg

# ---------------------------------------------------------------------------
# Directive prefixes — lines starting with these are config, not command
# ---------------------------------------------------------------------------

_DIRECTIVES = ("expect_exit:", "expect_stdout:", "expect_not_stdout:", "timeout:")
_CODE_FENCE = "```"


def _parse_subprocess_spec(test_field: str) -> dict:
    """Parse the Test field into a subprocess execution spec.

    Returns a dict with keys:
        command, expect_exit, expect_stdout, expect_not_stdout, timeout
    """
    spec = {
        "command": None,
        "expect_exit": 0,
        "expect_stdout": None,
        "expect_not_stdout": None,
        "timeout": 30,
    }

    command_lines = []

    for line in test_field.splitlines():
        stripped = line.strip()

        # Strip markdown code fences
        if stripped.startswith(_CODE_FENCE):
            continue

        if not stripped:
            continue

        low = stripped.lower()

        if low.startswith("expect_exit:"):
            try:
                spec["expect_exit"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        if low.startswith("expect_stdout:"):
            spec["expect_stdout"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("expect_not_stdout:"):
            spec["expect_not_stdout"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("timeout:"):
            try:
                spec["timeout"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        # Non-directive, non-empty line is part of the command
        command_lines.append(stripped)

    if command_lines:
        spec["command"] = " && ".join(command_lines)

    return spec


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_subprocess(question: dict) -> dict:
    """Execute shell command from Test field and return verdict envelope."""
    test_field = question.get("test", "") or question.get("Test", "")
    spec = _parse_subprocess_spec(test_field)

    command = spec["command"]
    expect_exit = spec["expect_exit"]
    expect_stdout = spec["expect_stdout"]
    expect_not_stdout = spec["expect_not_stdout"]
    timeout = spec["timeout"]

    if not command:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "No command found in Test field",
            "data": {"test_field": test_field[:200]},
            "details": "The Test field contained no executable command lines. "
            "Add a shell command before any expect_*/timeout: directives.",
        }

    # Execute
    returncode = -1
    stdout = ""
    stderr = ""

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.autosearch_root),
        )
        returncode = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""

    except subprocess.TimeoutExpired:
        return {
            "verdict": "FAILURE",
            "summary": f"Command timed out after {timeout}s: {command[:80]}",
            "data": {
                "command": command,
                "returncode": None,
                "exit_expected": expect_exit,
                "stdout_preview": "",
                "stderr_preview": "",
                "failure_type": "timeout",
            },
            "details": f"Command: {command}\nTimeout: {timeout}s exceeded",
            "failure_type": "timeout",
        }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Failed to run command: {exc}",
            "data": {"command": command, "error": str(exc)},
            "details": f"Command: {command}\nError: {exc}",
        }

    # Check if stdout is a JSON verdict envelope
    stdout_stripped = stdout.strip()
    if stdout_stripped.startswith("{"):
        try:
            parsed = json.loads(stdout_stripped)
            if "verdict" in parsed:
                parsed.setdefault(
                    "summary", f"exit={returncode}: {stdout_stripped[:100]}"
                )
                parsed.setdefault(
                    "data",
                    {
                        "command": command,
                        "returncode": returncode,
                        "exit_expected": expect_exit,
                        "stdout_preview": stdout[:500],
                        "stderr_preview": stderr[:200],
                    },
                )
                parsed.setdefault(
                    "details",
                    (
                        f"Command: {command}\n"
                        f"Exit: {returncode} (expected {expect_exit})\n"
                        f"Stdout:\n{stdout[:800]}\n"
                        f"Stderr:\n{stderr[:400]}"
                    ),
                )
                return parsed
        except json.JSONDecodeError:
            pass

    # Determine verdict from exit code and pattern checks
    verdict = "HEALTHY"
    failure_reasons = []

    if returncode != expect_exit:
        verdict = "FAILURE"
        failure_reasons.append(f"exit code {returncode} != expected {expect_exit}")

    if expect_stdout is not None and expect_stdout not in stdout:
        verdict = "FAILURE"
        failure_reasons.append(f"expected stdout substring '{expect_stdout}' not found")

    if expect_not_stdout is not None and expect_not_stdout in stdout:
        verdict = "FAILURE"
        failure_reasons.append(
            f"forbidden stdout substring '{expect_not_stdout}' was found"
        )

    one_line = (stdout[:100] or stderr[:100]).strip().replace("\n", " ")
    summary = f"exit={returncode}: {one_line}"
    if failure_reasons:
        summary += " | " + "; ".join(failure_reasons)

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "command": command,
            "returncode": returncode,
            "exit_expected": expect_exit,
            "stdout_preview": stdout[:500],
            "stderr_preview": stderr[:200],
        },
        "details": (
            f"Command: {command}\n"
            f"Exit: {returncode} (expected {expect_exit})\n"
            f"Stdout:\n{stdout[:800]}\n"
            f"Stderr:\n{stderr[:400]}"
        ),
    }
