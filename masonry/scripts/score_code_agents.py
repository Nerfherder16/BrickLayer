"""Score developer, test-writer, fix-implementer, code-reviewer from autopilot artifacts.

Walks git branches looking for .autopilot/ directories, parses progress.json
and build.log, scores on tests_pass / lint_clean / no_regression dimensions,
and writes training records to masonry/training_data/scored_code_agents.jsonl.

Usage:
    python masonry/scripts/score_code_agents.py [--base-dir DIR] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Import rubrics — graceful degradation if masonry package not on sys.path
# ---------------------------------------------------------------------------

try:
    from masonry.src.scoring.rubrics import min_training_score, RUBRICS
    _MIN_CODE_SCORE: int = RUBRICS["code"]["min_training_score"]
except ImportError:
    _MIN_CODE_SCORE = 70

    def min_training_score(agent_name: str) -> int:  # type: ignore[misc]
        return _MIN_CODE_SCORE


# ---------------------------------------------------------------------------
# Regex patterns for build.log analysis
# ---------------------------------------------------------------------------

_RE_LINT_ERROR = re.compile(
    r"(lint error|eslint|pylint|ruff|mypy.*error|flake8.*[EW]\d)", re.IGNORECASE
)
_RE_REGRESSION = re.compile(
    r"(regression|previously passing|broke \d+ test|was passing.*now fail)", re.IGNORECASE
)
_RE_TEST_FAIL = re.compile(r"(FAILED|ERROR)\s+\S+::", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _score_tests_pass(tests: dict[str, Any]) -> int:
    """Score tests_pass dimension (0-50 points).

    Full 50 if failing == 0, partial if some pass, 0 if total == 0 or all fail.
    """
    total = tests.get("total", 0)
    failing = tests.get("failing", 0)
    passing = tests.get("passing", 0)

    if total == 0:
        return 0
    if failing == 0:
        return 50
    if passing == 0:
        return 0
    # Partial credit proportional to passing fraction
    return int(50 * passing / total)


def _score_lint_clean(log_text: str) -> int:
    """Score lint_clean dimension (0-20 points).

    20 if no lint errors detected in build.log, 0 otherwise.
    """
    if _RE_LINT_ERROR.search(log_text):
        return 0
    return 20


def _score_no_regression(log_text: str) -> int:
    """Score no_regression dimension (0-30 points).

    30 if no regression patterns detected, 0 otherwise.
    """
    if _RE_REGRESSION.search(log_text):
        return 0
    return 30


# ---------------------------------------------------------------------------
# Autopilot artifact discovery
# ---------------------------------------------------------------------------


def _find_autopilot_dirs(base_dir: Path) -> list[Path]:
    """Find all .autopilot/ directories under base_dir (in working tree only)."""
    found: list[Path] = []
    for ap_dir in base_dir.rglob(".autopilot"):
        if ap_dir.is_dir() and (ap_dir / "progress.json").exists():
            found.append(ap_dir)
    return found


def _find_autopilot_dirs_in_branches(base_dir: Path) -> list[tuple[str, dict[str, Any], str]]:
    """Walk git branches to find .autopilot/progress.json contents.

    Returns list of (branch_name, progress_dict, log_text) tuples.
    Gracefully returns empty list if not in a git repo.
    """
    results: list[tuple[str, dict[str, Any], str]] = []

    try:
        branches_raw = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            capture_output=True,
            text=True,
            cwd=str(base_dir),
            timeout=10,
        )
        if branches_raw.returncode != 0:
            return results
        branches = [b.strip() for b in branches_raw.stdout.splitlines() if b.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return results

    for branch in branches:
        # Try to read .autopilot/progress.json from this branch
        try:
            prog_raw = subprocess.run(
                ["git", "show", f"{branch}:.autopilot/progress.json"],
                capture_output=True,
                text=True,
                cwd=str(base_dir),
                timeout=5,
            )
            if prog_raw.returncode != 0 or not prog_raw.stdout.strip():
                continue
            progress = json.loads(prog_raw.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            continue

        # Try to read build.log
        try:
            log_raw = subprocess.run(
                ["git", "show", f"{branch}:.autopilot/build.log"],
                capture_output=True,
                text=True,
                cwd=str(base_dir),
                timeout=5,
            )
            log_text = log_raw.stdout if log_raw.returncode == 0 else ""
        except (subprocess.SubprocessError, OSError):
            log_text = ""

        results.append((branch, progress, log_text))

    return results


def _collect_from_working_tree(base_dir: Path) -> list[tuple[str, dict[str, Any], str]]:
    """Collect .autopilot artifacts from working tree (not via git show)."""
    results: list[tuple[str, dict[str, Any], str]] = []
    for ap_dir in _find_autopilot_dirs(base_dir):
        prog_path = ap_dir / "progress.json"
        log_path = ap_dir / "build.log"
        try:
            progress = json.loads(prog_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        log_text = ""
        if log_path.exists():
            try:
                log_text = log_path.read_text(encoding="utf-8")
            except OSError:
                pass
        # Use the parent directory name as a pseudo-branch label
        label = ap_dir.parent.name
        results.append((label, progress, log_text))
    return results


# ---------------------------------------------------------------------------
# Scoring a single autopilot session
# ---------------------------------------------------------------------------


def score_autopilot_session(
    label: str,
    progress: dict[str, Any],
    log_text: str,
) -> list[dict[str, Any]]:
    """Score a single autopilot session from progress.json + build.log.

    Attributes tasks to 'developer' or 'test-writer' based on description keywords.
    Returns a list of training records (one per agent type found).
    """
    tests = progress.get("tests", {})
    tasks = progress.get("tasks", [])
    project = progress.get("project", label)

    tests_pts = _score_tests_pass(tests)
    lint_pts = _score_lint_clean(log_text)
    regression_pts = _score_no_regression(log_text)
    total = tests_pts + lint_pts + regression_pts

    # Determine which agent types are present in this session
    has_developer = False
    has_test_writer = False
    for task in tasks:
        desc = task.get("description", "").lower()
        if any(kw in desc for kw in ("test", "spec", "assertion")):
            has_test_writer = True
        else:
            has_developer = True

    # If no tasks with descriptions, assume developer
    if not tasks:
        has_developer = True

    records: list[dict[str, Any]] = []
    base_record = {
        "source": "autopilot",
        "branch": label,
        "project": project,
        "score": total,
        "score_breakdown": {
            "tests_pass": tests_pts,
            "lint_clean": lint_pts,
            "no_regression": regression_pts,
        },
        "input": {
            "task_count": len(tasks),
            "tests_total": tests.get("total", 0),
            "tests_failing": tests.get("failing", 0),
        },
        "output": {
            "status": progress.get("status", "UNKNOWN"),
            "tests_passing": tests.get("passing", 0),
        },
    }

    if has_developer and total >= min_training_score("developer"):
        rec = dict(base_record)
        rec["agent"] = "developer"
        records.append(rec)

    if has_test_writer and total >= min_training_score("test-writer"):
        rec = dict(base_record)
        rec["agent"] = "test-writer"
        records.append(rec)

    return records


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------


def run(
    base_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Score code agents from autopilot artifacts.

    Returns summary: {scanned, training_ready, agents_covered, output_path}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect from both working tree and git branches
    sessions = _collect_from_working_tree(base_dir)
    sessions.extend(_find_autopilot_dirs_in_branches(base_dir))

    # Deduplicate by (branch+project) — prefer working tree entries
    seen: set[str] = set()
    unique_sessions: list[tuple[str, dict[str, Any], str]] = []
    for label, progress, log_text in sessions:
        key = f"{label}:{progress.get('project', '')}"
        if key not in seen:
            seen.add(key)
            unique_sessions.append((label, progress, log_text))

    all_records: list[dict[str, Any]] = []
    agents_covered: set[str] = set()

    for label, progress, log_text in unique_sessions:
        records = score_autopilot_session(label, progress, log_text)
        for rec in records:
            all_records.append(rec)
            agents_covered.add(rec["agent"])

    with output_path.open("w", encoding="utf-8") as fh:
        for rec in all_records:
            fh.write(json.dumps(rec) + "\n")

    return {
        "scanned": len(unique_sessions),
        "training_ready": len(all_records),
        "agents_covered": sorted(agents_covered),
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(description="Score code agents from autopilot artifacts.")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("masonry/training_data/scored_code_agents.jsonl"),
    )
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, output_path=args.output)
    print(f"Scanned: {summary['scanned']} autopilot sessions")
    print(f"Training records written: {summary['training_ready']}")
    print(f"Agents covered: {', '.join(summary['agents_covered']) or 'none'}")
    print(f"Written to: {summary['output_path']}")


if __name__ == "__main__":
    _main()
