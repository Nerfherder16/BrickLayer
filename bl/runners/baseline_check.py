"""
bl/runners/baseline_check.py — Baseline regression check runner (mode: baseline_check).

Loads a previously saved baseline for a question and compares it against either
a latest-result file or an explicitly provided result. Returns FAILURE if a
regression is detected, HEALTHY if everything is within bounds, or INCONCLUSIVE
if no baseline has been saved yet.

Handles questions with mode: baseline_check

Spec field syntax (parsed from the question's Spec or Test field):
    question_id: "D1.1"                             — which question's baseline to check
    current_result_file: ".bl-baseline/D1.1_latest.json"  — optional explicit result path
    project_dir: "."                                — optional (defaults to cwd / cfg.project_root)
    fail_on_verdict_change: true                    — FAILURE if verdict worsened (default: true)
    fail_on_metric_regression:                      — optional per-metric thresholds
      p95_ms: 50                                    — FAILURE if p95_ms rose by >50%
      pass_rate: 10                                 — FAILURE if pass_rate dropped by >10%
"""

import json
import os
from pathlib import Path

from bl.baseline import diff_against_baseline, load_baseline
from bl.config import cfg


# ---------------------------------------------------------------------------
# Spec parser
# ---------------------------------------------------------------------------


def _parse_baseline_check_spec(question: dict) -> dict:
    """Parse the question dict into a baseline check spec.

    Reads from question["spec"] (preferred) or question["test"] / question["Test"].

    Returns a dict with keys:
        question_id, current_result_file, project_dir,
        fail_on_verdict_change, fail_on_metric_regression
    """
    spec: dict = {
        "question_id": None,
        "current_result_file": None,
        "project_dir": None,
        "fail_on_verdict_change": True,
        "fail_on_metric_regression": {},
    }

    # Accept spec as a dict (pre-parsed YAML) or as a raw text field
    raw_spec = question.get("spec") or question.get("Spec")

    if isinstance(raw_spec, dict):
        spec["question_id"] = raw_spec.get("question_id")
        spec["current_result_file"] = raw_spec.get("current_result_file")
        spec["project_dir"] = raw_spec.get("project_dir")
        fovc = raw_spec.get("fail_on_verdict_change", True)
        spec["fail_on_verdict_change"] = str(fovc).lower() not in ("false", "0", "no")
        fomr = raw_spec.get("fail_on_metric_regression", {})
        if isinstance(fomr, dict):
            spec["fail_on_metric_regression"] = {k: float(v) for k, v in fomr.items()}
        return spec

    # Fall back to line-by-line text parsing
    text = ""
    if isinstance(raw_spec, str):
        text = raw_spec
    else:
        text = question.get("test", "") or question.get("Test", "")

    in_metric_block = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("```"):
            in_metric_block = False
            continue

        low = stripped.lower()

        if in_metric_block:
            # Indented metric threshold: "  p95_ms: 50"
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                try:
                    spec["fail_on_metric_regression"][key.strip()] = float(val.strip())
                except ValueError:
                    pass
            continue

        if low.startswith("question_id:"):
            spec["question_id"] = (
                stripped.split(":", 1)[1].strip().strip('"').strip("'")
            )
        elif low.startswith("current_result_file:"):
            spec["current_result_file"] = stripped.split(":", 1)[1].strip()
        elif low.startswith("project_dir:"):
            spec["project_dir"] = stripped.split(":", 1)[1].strip()
        elif low.startswith("fail_on_verdict_change:"):
            val = stripped.split(":", 1)[1].strip().lower()
            spec["fail_on_verdict_change"] = val not in ("false", "0", "no")
        elif low.startswith("fail_on_metric_regression:"):
            in_metric_block = True

    return spec


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_baseline_check(question: dict) -> dict:
    """Run a baseline regression check and return a verdict envelope.

    Args:
        question:  Parsed question dict. Must have mode: baseline_check and
                   either a spec dict or text with question_id:.

    Returns:
        Standard verdict envelope: {verdict, summary, data, details}.

        HEALTHY      — result matches baseline within all configured thresholds.
        FAILURE      — regression detected (verdict worsened or metric crossed threshold).
        INCONCLUSIVE — no baseline has been saved for this question yet, or the
                       current result file could not be loaded.
    """
    parsed = _parse_baseline_check_spec(question)
    question_id = parsed["question_id"]

    if not question_id:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "baseline_check: no question_id specified in spec",
            "data": {"error": "missing_question_id"},
            "details": (
                "The baseline_check runner requires a question_id in the Spec field.\n"
                "Example:\n  question_id: D1.1"
            ),
        }

    # Resolve project dir
    project_dir = (
        parsed["project_dir"] or getattr(cfg, "project_root", None) or os.getcwd()
    )
    project_dir = str(Path(project_dir).resolve())

    # Load the saved baseline
    snapshot = load_baseline(project_dir, question_id)
    if snapshot is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"baseline_check: no baseline saved for {question_id}",
            "data": {
                "question_id": question_id,
                "project_dir": project_dir,
                "error": "no_baseline",
            },
            "details": (
                f"No baseline found for question '{question_id}' in {project_dir}/.bl-baseline/.\n"
                "Save a baseline first by calling bl.baseline.save_baseline() after a known-good run."
            ),
        }

    # Load the current result to compare against
    current_result = _load_current_result(parsed, project_dir, question_id)
    if current_result is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"baseline_check: could not load current result for {question_id}",
            "data": {
                "question_id": question_id,
                "project_dir": project_dir,
                "current_result_file": parsed["current_result_file"],
                "error": "current_result_not_found",
            },
            "details": (
                f"No current result available for question '{question_id}'.\n"
                "Either specify current_result_file: in the spec, or ensure the runner\n"
                f"writes its latest result to {project_dir}/.bl-baseline/{question_id}_latest.json."
            ),
        }

    # Diff
    diff = diff_against_baseline(current_result, snapshot)

    # Evaluate thresholds
    failures: list[str] = []
    warnings: list[str] = []

    if parsed["fail_on_verdict_change"] and diff["verdict_changed"]:
        failures.append(f"Verdict regressed: {diff['verdict_delta']}")

    for metric, threshold_pct in parsed["fail_on_metric_regression"].items():
        delta = diff["metric_deltas"].get(metric)
        if delta is None:
            continue
        pct = delta["delta_pct"]
        # For metrics where higher is worse (latency), positive delta triggers failure.
        # For metrics where lower is worse (pass_rate), we check absolute drop.
        if abs(pct) > threshold_pct:
            direction = "rose" if pct > 0 else "dropped"
            failures.append(
                f"{metric} {direction} by {abs(pct):.1f}% "
                f"(baseline={delta['baseline']}, current={delta['current']}, "
                f"threshold={threshold_pct}%)"
            )

    if diff["new_issues"] and not failures:
        warnings.extend([f"New issue: {i}" for i in diff["new_issues"]])

    # Determine verdict
    if failures:
        verdict = "FAILURE"
    elif warnings:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    baseline_meta = {
        "saved_at": snapshot.get("timestamp", "unknown"),
        "git_sha": snapshot.get("git_sha"),
        "baseline_verdict": snapshot.get("result", {}).get("verdict", "UNKNOWN"),
    }
    current_verdict = current_result.get("verdict", "UNKNOWN")

    summary_parts = [f"baseline_check {question_id}: {current_verdict}"]
    if failures:
        summary_parts.append(" | ".join(failures))
    elif warnings:
        summary_parts.append(" | ".join(warnings))
    elif diff["resolved_issues"]:
        summary_parts.append(
            f"{len(diff['resolved_issues'])} issue(s) resolved vs baseline"
        )
    else:
        summary_parts.append("no regressions detected")
    summary = " — ".join(summary_parts)

    # Build details
    detail_lines = [
        f"Question: {question_id}",
        f"Project: {project_dir}",
        f"Baseline saved: {baseline_meta['saved_at']} (sha: {baseline_meta['git_sha'] or 'n/a'})",
        f"Baseline verdict: {baseline_meta['baseline_verdict']}",
        f"Current verdict:  {current_verdict}",
        "",
    ]

    if diff["verdict_changed"]:
        detail_lines.append(f"VERDICT REGRESSION: {diff['verdict_delta']}")
    else:
        detail_lines.append("Verdict: unchanged")

    if diff["metric_deltas"]:
        detail_lines.append("\nMetric deltas:")
        for metric, d in diff["metric_deltas"].items():
            sign = "+" if d["delta_pct"] > 0 else ""
            detail_lines.append(
                f"  {metric}: {d['baseline']} → {d['current']} ({sign}{d['delta_pct']:.1f}%)"
            )

    if diff["new_issues"]:
        detail_lines.append(f"\nNew issues ({len(diff['new_issues'])}):")
        for issue in diff["new_issues"]:
            detail_lines.append(f"  - {issue}")

    if diff["resolved_issues"]:
        detail_lines.append(f"\nResolved issues ({len(diff['resolved_issues'])}):")
        for issue in diff["resolved_issues"]:
            detail_lines.append(f"  - {issue}")

    if failures:
        detail_lines.append("\nFailure reasons:")
        for f_reason in failures:
            detail_lines.append(f"  - {f_reason}")

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "question_id": question_id,
            "baseline": baseline_meta,
            "current_verdict": current_verdict,
            "diff": diff,
            "failures": failures,
            "warnings": warnings,
        },
        "details": "\n".join(detail_lines),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_current_result(
    parsed: dict, project_dir: str, question_id: str
) -> dict | None:
    """Load the current result envelope to compare against the baseline.

    Checks (in order):
    1. parsed["current_result_file"] — explicit path from spec.
    2. {project_dir}/.bl-baseline/{question_id}_latest.json — convention path.

    Returns the result dict or None if not found / unreadable.
    """
    candidates: list[Path] = []

    if parsed["current_result_file"]:
        p = Path(parsed["current_result_file"])
        if not p.is_absolute():
            p = Path(project_dir) / p
        candidates.append(p)

    # Convention: runners write their latest result here
    candidates.append(Path(project_dir) / ".bl-baseline" / f"{question_id}_latest.json")

    for path in candidates:
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                # If the file is a full snapshot wrapper, unwrap it
                if "result" in raw and "question_id" in raw:
                    return raw["result"]
                return raw
            except (json.JSONDecodeError, OSError):
                continue

    return None
