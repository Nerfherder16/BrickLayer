"""
bl/baseline.py — Baseline snapshot manager for BrickLayer 2.0 (3.05).

Stores and compares known-good runner results to detect regressions between
research runs. Baselines are saved per-question in a `.bl-baseline/` directory
inside the project dir.

Storage layout:
    {project_dir}/.bl-baseline/{question_id}.json
    {project_dir}/.bl-baseline/{question_id}_latest.json  (written by runners)
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _baseline_dir(project_dir: str) -> Path:
    """Return the .bl-baseline directory path, creating it if needed."""
    d = Path(project_dir) / ".bl-baseline"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _git_sha(project_dir: str) -> str | None:
    """Return the short HEAD git SHA for the given directory, or None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _numeric_fields(d: dict) -> dict[str, float]:
    """Recursively collect all numeric leaf values from a dict (one level of data only)."""
    out: dict[str, float] = {}
    for k, v in d.items():
        if isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def _issue_list(result: dict) -> list[str]:
    """Extract a normalised list of issue strings from a result envelope.

    Looks in data.issues, data.errors, data.checks_failed, and
    data.failure_reasons — whichever are present.
    """
    data = result.get("data", {})
    candidates = (
        data.get("issues", [])
        + data.get("errors", [])
        + data.get("checks_failed", [])
        + data.get("failure_reasons", [])
    )
    return [str(c) for c in candidates if c]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def save_baseline(project_dir: str, question_id: str, result: dict) -> None:
    """Save a runner result as the known-good baseline for this question.

    The snapshot includes the original result dict plus metadata:
    timestamp (UTC ISO-8601) and git_sha (if the project is a git repo).

    Args:
        project_dir:  Absolute or relative path to the project root.
        question_id:  The question identifier (e.g. "D1.1").
        result:       Verdict envelope dict returned by a runner.

    Writes to:
        {project_dir}/.bl-baseline/{question_id}.json
    """
    baseline_file = _baseline_dir(project_dir) / f"{question_id}.json"
    snapshot = {
        "question_id": question_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(project_dir),
        "result": result,
    }
    baseline_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def load_baseline(project_dir: str, question_id: str) -> dict | None:
    """Load the saved baseline for a question.

    Args:
        project_dir:  Path to the project root.
        question_id:  The question identifier.

    Returns:
        The full snapshot dict (with keys: question_id, timestamp, git_sha,
        result), or None if no baseline has been saved for this question.
    """
    baseline_file = _baseline_dir(project_dir) / f"{question_id}.json"
    if not baseline_file.exists():
        return None
    try:
        return json.loads(baseline_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def diff_against_baseline(result: dict, baseline: dict) -> dict:
    """Compare a new result against a saved baseline snapshot.

    Detects verdict regressions and numeric metric regressions.

    Args:
        result:    Current verdict envelope dict (returned by a runner).
        baseline:  Full baseline snapshot dict as returned by load_baseline().
                   Accepts both the snapshot wrapper (with a "result" key) and
                   a raw verdict envelope directly.

    Returns:
        A diff dict with the following keys:

        has_regression (bool):
            True if any regression was detected.

        verdict_changed (bool):
            True if the verdict worsened (HEALTHY → FAILURE or WARNING,
            WARNING → FAILURE).

        verdict_delta (str | None):
            Human-readable transition string, e.g. "HEALTHY→FAILURE".
            None if the verdict did not change or was not a regression.

        metric_deltas (dict):
            For each numeric field in result["data"] that also exists in the
            baseline result["data"], reports:
                {"baseline": float, "current": float, "delta_pct": float}
            Only fields where the value changed are included.

        new_issues (list[str]):
            Issues present in the current result but absent from the baseline.

        resolved_issues (list[str]):
            Issues present in the baseline but absent from the current result.
    """
    # Unwrap snapshot wrapper if needed
    baseline_result = baseline.get("result", baseline)

    current_verdict = result.get("verdict", "INCONCLUSIVE")
    baseline_verdict = baseline_result.get("verdict", "INCONCLUSIVE")

    # Verdict severity order (higher index = worse)
    _SEVERITY = {"HEALTHY": 0, "INCONCLUSIVE": 1, "WARNING": 2, "FAILURE": 3}
    current_sev = _SEVERITY.get(current_verdict, 1)
    baseline_sev = _SEVERITY.get(baseline_verdict, 1)

    verdict_changed = current_sev > baseline_sev
    verdict_delta = f"{baseline_verdict}→{current_verdict}" if verdict_changed else None

    # Numeric metric deltas
    current_nums = _numeric_fields(result.get("data", {}))
    baseline_nums = _numeric_fields(baseline_result.get("data", {}))

    metric_deltas: dict[str, dict] = {}
    for field, cur_val in current_nums.items():
        if field not in baseline_nums:
            continue
        base_val = baseline_nums[field]
        if base_val == cur_val:
            continue
        if base_val != 0:
            delta_pct = round(((cur_val - base_val) / abs(base_val)) * 100, 1)
        else:
            delta_pct = float("inf") if cur_val != 0 else 0.0
        metric_deltas[field] = {
            "baseline": base_val,
            "current": cur_val,
            "delta_pct": delta_pct,
        }

    # Issue lists
    current_issues = set(_issue_list(result))
    baseline_issues = set(_issue_list(baseline_result))
    new_issues = sorted(current_issues - baseline_issues)
    resolved_issues = sorted(baseline_issues - current_issues)

    has_regression = verdict_changed or bool(new_issues)

    return {
        "has_regression": has_regression,
        "verdict_changed": verdict_changed,
        "verdict_delta": verdict_delta,
        "metric_deltas": metric_deltas,
        "new_issues": new_issues,
        "resolved_issues": resolved_issues,
    }


def list_baselines(project_dir: str) -> list[dict]:
    """Return a summary list of all saved baselines for a project.

    Args:
        project_dir:  Path to the project root.

    Returns:
        List of dicts, each with keys:
            question_id (str), timestamp (str), verdict (str), git_sha (str | None).
        Sorted by question_id.
    """
    bl_dir = _baseline_dir(project_dir)
    summaries = []
    for f in sorted(bl_dir.glob("*.json")):
        # Skip _latest files written by runners
        if f.stem.endswith("_latest"):
            continue
        try:
            snap = json.loads(f.read_text(encoding="utf-8"))
            summaries.append(
                {
                    "question_id": snap.get("question_id", f.stem),
                    "timestamp": snap.get("timestamp", ""),
                    "verdict": snap.get("result", {}).get("verdict", "UNKNOWN"),
                    "git_sha": snap.get("git_sha"),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    return summaries


def clear_baseline(project_dir: str, question_id: str) -> bool:
    """Remove the saved baseline for a question.

    Args:
        project_dir:  Path to the project root.
        question_id:  The question identifier.

    Returns:
        True if a baseline existed and was removed, False if it did not exist.
    """
    baseline_file = _baseline_dir(project_dir) / f"{question_id}.json"
    if baseline_file.exists():
        baseline_file.unlink()
        return True
    return False
