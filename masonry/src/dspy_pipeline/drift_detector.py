"""masonry/src/dspy_pipeline/drift_detector.py

Drift detection for Masonry agents.

Compares each agent's recent verdict history against a stored baseline score
and produces a DriftReport with an alert level and recommendation.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Verdict → numeric score mapping
# ---------------------------------------------------------------------------

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

_DEFAULT_VERDICT_SCORE = 0.5  # unknown verdicts treated as partial


# ---------------------------------------------------------------------------
# DriftReport model
# ---------------------------------------------------------------------------


class DriftReport(BaseModel):
    agent_name: str
    baseline_score: float
    current_score: float
    drift_pct: float          # positive = regression, negative = improvement
    alert_level: str          # "ok" | "warning" | "critical"
    recommendation: str


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _score_verdicts(verdicts: list[str]) -> float:
    """Convert a list of verdict strings to a mean numeric score."""
    if not verdicts:
        return 1.0  # no data — assume healthy (no evidence of regression)
    scores = [_VERDICT_SCORE.get(v, _DEFAULT_VERDICT_SCORE) for v in verdicts]
    return sum(scores) / len(scores)


def _alert_level(drift_pct: float) -> str:
    """Classify drift magnitude as ok / warning / critical."""
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
) -> DriftReport:
    """Compute a DriftReport for a single agent.

    Args:
        agent_name: Identifier for the agent.
        baseline_score: Score recorded at last optimization (0.0–1.0).
        recent_verdicts: List of verdict strings from recent campaign runs.

    Returns:
        DriftReport with drift_pct, alert_level, and recommendation.
    """
    current_score = _score_verdicts(recent_verdicts)
    if baseline_score > 0.0:
        drift_pct = (baseline_score - current_score) / baseline_score * 100.0
    else:
        drift_pct = 0.0
    level = _alert_level(drift_pct)
    return DriftReport(
        agent_name=agent_name,
        baseline_score=baseline_score,
        current_score=current_score,
        drift_pct=drift_pct,
        alert_level=level,
        recommendation=_recommendation(level, agent_name),
    )


# ---------------------------------------------------------------------------
# Batch check
# ---------------------------------------------------------------------------


def run_drift_check(
    agent_db_path: Path,
    registry: list,
) -> list[DriftReport]:
    """Run drift detection for all registry agents that have verdict history.

    Args:
        agent_db_path: Path to agent_db.json.
        registry: List of AgentRegistryEntry (or any objects with .name attr).

    Returns:
        List of DriftReport for agents that have both a score and verdicts in
        the agent DB. Agents without verdicts are skipped.
    """
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
        reports.append(detect_drift(agent_name, baseline_score, verdicts))

    return reports
