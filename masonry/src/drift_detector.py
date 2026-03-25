"""masonry/src/drift_detector.py

Drift detection for Masonry agents.

Compares each agent's recent verdict history against a stored baseline score
and produces a DriftReport with an alert level and recommendation.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

_VERDICT_SCORE: dict[str, float] = {
    "HEALTHY": 1.0,
    "FIXED": 1.0,
    "COMPLIANT": 1.0,
    "CALIBRATED": 1.0,
    "WARNING": 0.5,
    "PARTIAL": 0.5,
    "DEGRADED_TRENDING": 0.5,
    "FAILURE": 0.0,
    "NON_COMPLIANT": 0.0,
}

_DEFAULT_VERDICT_SCORE = 0.5


class DriftReport(BaseModel):
    agent_name: str
    baseline_score: float
    current_score: float
    drift_pct: float          # positive = regression, negative = improvement
    alert_level: str          # "ok" | "warning" | "critical"
    recommendation: str


def _score_verdicts(verdicts: list[str], confidences: list[float] | None = None) -> float:
    """Score an agent by mean confidence, not by verdict category."""
    if not verdicts:
        return 1.0
    if confidences and len(confidences) == len(verdicts):
        return sum(confidences) / len(confidences)
    # Fallback: category scoring for agents without confidence data
    scores = [_VERDICT_SCORE.get(v, _DEFAULT_VERDICT_SCORE) for v in verdicts]
    return sum(scores) / len(scores)


def _alert_level(drift_pct: float) -> str:
    if drift_pct >= 25.0:
        return "critical"
    if drift_pct >= 10.0:
        return "warning"
    return "ok"


def _recommendation(alert_level: str, agent_name: str) -> str:
    if alert_level == "critical":
        return (
            f"Agent '{agent_name}' has critical drift (>=25%). "
            "Re-run optimize loop immediately: "
            f"python masonry/scripts/improve_agent.py {agent_name}"
        )
    if alert_level == "warning":
        return (
            f"Agent '{agent_name}' shows warning-level drift (10-25%). "
            "Consider scheduling an optimization cycle."
        )
    return f"Agent '{agent_name}' is within acceptable performance bounds."


def detect_drift(
    agent_name: str,
    baseline_score: float,
    recent_verdicts: list[str],
    confidences: list[float] | None = None,
) -> DriftReport:
    """Compute a DriftReport for a single agent."""
    current_score = _score_verdicts(recent_verdicts, confidences)
    drift_pct = (baseline_score - current_score) / baseline_score * 100.0 if baseline_score > 0.0 else 0.0
    level = _alert_level(drift_pct)
    return DriftReport(
        agent_name=agent_name,
        baseline_score=baseline_score,
        current_score=current_score,
        drift_pct=drift_pct,
        alert_level=level,
        recommendation=_recommendation(level, agent_name),
    )


def run_drift_check(
    agent_db_path: Path,
    registry: list,
) -> list[DriftReport]:
    """Run drift detection for all registry agents that have verdict history."""
    if not agent_db_path.exists():
        return []
    try:
        agent_db: dict = json.loads(agent_db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    registry_names = {entry.name for entry in registry}
    reports: list[DriftReport] = []
    for agent_name in registry_names:
        entry = agent_db.get(agent_name)
        if not entry:
            continue
        verdicts: list[str] = entry.get("verdicts", [])
        if not verdicts:
            continue
        baseline_score: float = float(entry.get("score", 0.0))
        confidences: list[float] = entry.get("confidences", [])
        reports.append(detect_drift(agent_name, baseline_score, verdicts, confidences or None))
    return reports
