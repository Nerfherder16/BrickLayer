"""
bl/question_weights.py — Self-improving question bank weights.

Tracks verdict history per question and computes priority weights to guide
mortar's question selection in future waves.

Integration point:
    bl.questions.get_next_pending() picks the first PENDING question in order.
    To use weights, call get_sorted_questions() with the IDs of all PENDING
    questions, then iterate that sorted list instead of the raw question order.
    Example:

        from bl.question_weights import get_sorted_questions
        pending_ids = [q["id"] for q in questions if q["status"] == "PENDING"]
        ordered_ids = get_sorted_questions(project_dir, pending_ids)
        # find the first question whose ID is in ordered_ids (preserving object)
        by_id = {q["id"]: q for q in questions}
        for qid in ordered_ids:
            q = by_id.get(qid)
            if q:
                return q
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Verdict constants (mirrors bl/runners/base.py envelope)
# ---------------------------------------------------------------------------
_VERDICT_FAILURE = "FAILURE"
_VERDICT_WARNING = "WARNING"
_VERDICT_HEALTHY = "HEALTHY"
_VERDICT_INCONCLUSIVE = "INCONCLUSIVE"

_WEIGHTS_FILE = ".bl-weights.json"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class QuestionWeight:
    question_id: str
    runs: int = 0
    failures: int = 0
    warnings: int = 0
    healthys: int = 0
    inconclusives: int = 0
    last_verdict: str = ""
    weight: float = 1.0  # 0.0 = prune, 1.0 = normal, 2.0 = high-priority
    last_updated: str = ""  # ISO-8601


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _weights_path(project_dir: str) -> Path:
    return Path(project_dir) / _WEIGHTS_FILE


def load_weights(project_dir: str) -> dict[str, QuestionWeight]:
    """Load weights from {project_dir}/.bl-weights.json. Returns {} if missing."""
    path = _weights_path(project_dir)
    if not path.exists():
        return {}
    try:
        raw: dict = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    weights: dict[str, QuestionWeight] = {}
    for qid, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        weights[qid] = QuestionWeight(
            question_id=entry.get("question_id", qid),
            runs=int(entry.get("runs", 0)),
            failures=int(entry.get("failures", 0)),
            warnings=int(entry.get("warnings", 0)),
            healthys=int(entry.get("healthys", 0)),
            inconclusives=int(entry.get("inconclusives", 0)),
            last_verdict=entry.get("last_verdict", ""),
            weight=float(entry.get("weight", 1.0)),
            last_updated=entry.get("last_updated", ""),
        )
    return weights


def save_weights(project_dir: str, weights: dict[str, QuestionWeight]) -> None:
    """Save weights to {project_dir}/.bl-weights.json."""
    path = _weights_path(project_dir)
    serialised = {qid: asdict(qw) for qid, qw in weights.items()}
    path.write_text(
        json.dumps(serialised, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Weight computation
# ---------------------------------------------------------------------------


def compute_weight(qw: QuestionWeight) -> float:
    """
    Scoring formula:
    - Base weight = 1.0
    - Each FAILURE run: +0.5 (capped at +2.0 total bonus)
    - Each WARNING run: +0.2 (capped at +0.6 total bonus)
    - If runs >= 3 and ALL HEALTHY: weight = 0.3 (low signal — deprioritize)
    - If runs >= 5 and ALL HEALTHY: weight = 0.1 (prune candidate)
    - If runs >= 3 and ALL INCONCLUSIVE: weight = 0.2 (broken runner — deprioritize)
    - Cap final weight at 3.0
    """
    if qw.runs == 0:
        return 1.0

    # Short-circuit: all-HEALTHY degradation rules
    signal_runs = qw.failures + qw.warnings + qw.inconclusives
    if signal_runs == 0:
        # Every run was HEALTHY
        if qw.runs >= 5:
            return 0.1
        if qw.runs >= 3:
            return 0.3

    # All INCONCLUSIVE (no failures, no warnings, no healthys)
    if qw.healthys == 0 and qw.failures == 0 and qw.warnings == 0 and qw.runs >= 3:
        return 0.2

    # Normal scoring
    failure_bonus = min(qw.failures * 0.5, 2.0)
    warning_bonus = min(qw.warnings * 0.2, 0.6)
    raw = 1.0 + failure_bonus + warning_bonus
    return min(raw, 3.0)


# ---------------------------------------------------------------------------
# Record a result
# ---------------------------------------------------------------------------


def record_result(project_dir: str, question_id: str, verdict: str) -> QuestionWeight:
    """
    Update weight for a question based on its latest verdict.
    Recomputes weight using the scoring formula. Saves and returns the updated QuestionWeight.
    """
    weights = load_weights(project_dir)
    qw = weights.get(question_id, QuestionWeight(question_id=question_id))

    qw.runs += 1
    qw.last_verdict = verdict
    v = verdict.upper()
    if v == _VERDICT_FAILURE:
        qw.failures += 1
    elif v == _VERDICT_WARNING:
        qw.warnings += 1
    elif v == _VERDICT_HEALTHY:
        qw.healthys += 1
    else:
        # INCONCLUSIVE or any other verdict
        qw.inconclusives += 1

    qw.weight = compute_weight(qw)
    qw.last_updated = datetime.now(timezone.utc).isoformat()

    weights[question_id] = qw
    save_weights(project_dir, weights)
    return qw


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------


def get_sorted_questions(project_dir: str, question_ids: list[str]) -> list[str]:
    """
    Return question_ids sorted by weight descending.
    Unknown questions (not in weights) get weight=1.0 (neutral).
    Used by mortar to prioritize which PENDING question to run next.
    """
    weights = load_weights(project_dir)

    def _key(qid: str) -> float:
        qw = weights.get(qid)
        return qw.weight if qw is not None else 1.0

    return sorted(question_ids, key=_key, reverse=True)


def prune_candidates(project_dir: str, threshold: float = 0.15) -> list[str]:
    """
    Return question IDs with weight <= threshold.
    These are candidates for removal from questions.md in the next wave.
    """
    weights = load_weights(project_dir)
    return [qid for qid, qw in weights.items() if qw.weight <= threshold]


# ---------------------------------------------------------------------------
# Human-readable report
# ---------------------------------------------------------------------------

_LABEL_HIGH = "HIGH"
_LABEL_NORM = "NORM"
_LABEL_LOW = "LOW "


def weight_report(project_dir: str) -> str:
    """
    Human-readable weight report. Format:

    Question Weights (12 tracked):
      HIGH  Q3  weight=2.5  (3 runs: 2F 1W)
      HIGH  Q7  weight=2.1  (5 runs: 1F 3W 1H)
      NORM  Q1  weight=1.0  (2 runs: 1H 1W)
      LOW   Q9  weight=0.3  (4 runs: 4H)
    PRUNE candidates: Q5, Q11
    """
    weights = load_weights(project_dir)
    if not weights:
        return "Question Weights (0 tracked): no data."

    prunable = prune_candidates(project_dir)
    sorted_items = sorted(weights.values(), key=lambda qw: qw.weight, reverse=True)

    lines = [f"Question Weights ({len(weights)} tracked):"]
    for qw in sorted_items:
        if qw.weight >= 1.5:
            label = _LABEL_HIGH
        elif qw.weight >= 0.5:
            label = _LABEL_NORM
        else:
            label = _LABEL_LOW

        parts = []
        if qw.failures:
            parts.append(f"{qw.failures}F")
        if qw.warnings:
            parts.append(f"{qw.warnings}W")
        if qw.healthys:
            parts.append(f"{qw.healthys}H")
        if qw.inconclusives:
            parts.append(f"{qw.inconclusives}I")
        run_summary = " ".join(parts) if parts else "no signal"

        lines.append(
            f"  {label}  {qw.question_id:<10}  weight={qw.weight:<5.2f}  "
            f"({qw.runs} run{'s' if qw.runs != 1 else ''}: {run_summary})"
        )

    if prunable:
        lines.append(f"PRUNE candidates: {', '.join(sorted(prunable))}")
    else:
        lines.append("PRUNE candidates: none")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Demo project dir: {tmpdir}\n")

        # Simulate a series of verdicts for several questions
        scenarios = [
            ("Q1", ["FAILURE", "WARNING", "FAILURE"]),  # high signal
            ("Q2", ["HEALTHY", "HEALTHY", "HEALTHY"]),  # all healthy (deprioritize)
            ("Q3", ["WARNING", "HEALTHY", "WARNING"]),  # mixed
            ("Q4", ["INCONCLUSIVE", "INCONCLUSIVE", "INCONCLUSIVE"]),  # broken runner
            (
                "Q5",
                ["HEALTHY", "HEALTHY", "HEALTHY", "HEALTHY", "HEALTHY"],
            ),  # prune candidate
            ("Q6", ["FAILURE"]),  # single run, high signal
            ("Q7", ["HEALTHY"]),  # single run, neutral
        ]

        for qid, verdicts in scenarios:
            for v in verdicts:
                record_result(tmpdir, qid, v)

        print(weight_report(tmpdir))
        print()

        pending = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
        sorted_q = get_sorted_questions(tmpdir, pending)
        print(f"Sorted PENDING order: {sorted_q}")
        print(f"Prune candidates (threshold=0.15): {prune_candidates(tmpdir, 0.15)}")
