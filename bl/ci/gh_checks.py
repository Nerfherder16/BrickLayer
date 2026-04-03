"""bl/ci/gh_checks.py — CI gate: wait for GitHub PR checks to pass.

Usage (CLI):
    python -m bl.ci.gh_checks                    # wait for current branch PR
    python -m bl.ci.gh_checks --timeout 600      # custom timeout in seconds
    python -m bl.ci.gh_checks --branch feat/x    # explicit branch/PR ref
    python -m bl.ci.gh_checks --json             # machine-readable output

Exits 0 if all checks pass, 1 if any fail or timeout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


def get_pr_status(branch: str | None = None) -> dict[str, Any]:
    """Return current PR check statuses for the branch (or current branch)."""
    cmd = ["gh", "pr", "checks"]
    if branch:
        cmd.append(branch)
    cmd += ["--json", "name,state,conclusion,startedAt,completedAt"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "checks": []}

    try:
        checks = json.loads(result.stdout)
        return {"checks": checks, "error": None}
    except json.JSONDecodeError:
        return {"error": "Failed to parse gh output", "checks": []}


def wait_for_checks(
    branch: str | None = None,
    timeout: int = 300,
) -> tuple[bool, dict[str, Any]]:
    """Block until all PR checks pass or fail.

    Returns (passed, details) where details contains check names and conclusions.
    Uses `gh pr checks --watch` which polls until all checks complete.
    """
    cmd = ["gh", "pr", "checks", "--watch", "--interval", "10"]
    if branch:
        cmd.append(branch)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        status = get_pr_status(branch)
        return False, {"timeout": True, **status}

    passed = result.returncode == 0
    status = get_pr_status(branch)
    return passed, {
        "timeout": False,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        **status,
    }


def _summarise(details: dict[str, Any]) -> str:
    checks = details.get("checks", [])
    if not checks:
        return details.get("error") or details.get("stderr") or "No checks found"
    lines = []
    for c in checks:
        state = c.get("conclusion") or c.get("state") or "unknown"
        lines.append(f"  {c.get('name', '?')}: {state}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Wait for GitHub PR checks to pass.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--branch",
        default=None,
        metavar="REF",
        help="Branch name or PR number. Default: current branch.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        metavar="SECS",
        help="Max seconds to wait. Default: 300.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Print result as JSON.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current check status without waiting.",
    )

    args = parser.parse_args(argv)

    if args.status:
        details = get_pr_status(args.branch)
        if args.output_json:
            print(json.dumps(details, indent=2))
        else:
            print(_summarise(details))
        return 0 if not details.get("error") else 1

    print(
        f"[gh_checks] Waiting for PR checks (timeout={args.timeout}s)...",
        file=sys.stderr,
    )

    passed, details = wait_for_checks(branch=args.branch, timeout=args.timeout)

    if args.output_json:
        print(json.dumps({"passed": passed, **details}, indent=2))
        return 0 if passed else 1

    status_str = "PASSED" if passed else ("TIMEOUT" if details.get("timeout") else "FAILED")
    print(f"\n[gh_checks] {status_str}", file=sys.stderr)
    print(_summarise(details), file=sys.stderr)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
