"""Drift detection for Masonry agent quality monitoring.

Compares recent agent verdicts against baseline scores to detect
performance degradation that warrants re-optimization.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict

from masonry.src.schemas.payloads import AgentRegistryEntry


# ── Verdict scoring ──────────────────────────────────────────────────────────

# Verdicts that indicate success
_OK_VERDICTS = frozenset({
    "HEALTHY", "FIXED", "COMPLIANT", "CALIBRATED", "CONFIRMED", "OK",
    "IMPROVEMENT", "PROMISING", "DIAGNOSIS_COMPLETE", "FIX_APPLIED",
    "COMPLETE",
})

# Verdicts that indicate partial success
_PARTIAL_VERDICTS = frozenset({
    "WARNING", "PARTIAL", "PROBABLE", "POSSIBLE", "UNCALIBRATED", "INCONCLUSIVE",
})

# Everything else = failure (0.0)


def _score_verdict(verdict: str) -> float:
    """Score a single verdict string: 1.0, 0.5, or 0.0."""
    v = verdict.strip().upper()
    if v in _OK_VERDICTS:
        return 1.0
    if v in _PARTIAL_VERDICTS:
        return 0.5
    return 0.0


# ── DriftReport ──────────────────────────────────────────────────────────────


class DriftReport(BaseModel):
    """Drift analysis result for a single agent."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    baseline_score: float
    current_score: float
    drift_pct: Optional[float]
    alert_level: Literal["ok", "warning", "critical", "calibrating"]
    recommendation: str


# ── detect_drift ─────────────────────────────────────────────────────────────


def detect_drift(
    agent_name: str,
    baseline_score: float,
    recent_verdicts: list[str],
) -> DriftReport:
    """Compute drift for a single agent and return a DriftReport.

    Args:
        agent_name: The agent being evaluated.
        baseline_score: The agent's historical quality score (from agent_db).
        recent_verdicts: Recent verdict strings to compute current performance.
    """
    if not recent_verdicts:
        current_score = baseline_score  # no data → assume stable
    else:
        current_score = sum(_score_verdict(v) for v in recent_verdicts) / len(recent_verdicts)

    if baseline_score == 0.0:
        # No calibrated baseline yet — cannot compute meaningful drift.
        # Return "calibrating" level so new agents are not silently masked as ok.
        drift_pct = None
        alert_level: Literal["ok", "warning", "critical", "calibrating"] = "calibrating"
        recommendation = (
            f"{agent_name} has no calibrated baseline (baseline_score=0.0). "
            f"Current score: {current_score:.2f}. "
            "Accumulate more findings to establish a baseline before drift detection is meaningful."
        )
    else:
        drift_pct = (baseline_score - current_score) / baseline_score * 100

        if drift_pct < 10:
            alert_level = "ok"
            recommendation = (
                f"{agent_name} is performing within acceptable range "
                f"(drift {drift_pct:.1f}%). No action required."
            )
        elif drift_pct <= 25:
            alert_level = "warning"
            recommendation = (
                f"{agent_name} shows moderate performance drift ({drift_pct:.1f}%). "
                "Consider running DSPy re-optimization. Monitor closely."
            )
        else:
            alert_level = "critical"
            recommendation = (
                f"{agent_name} has critical performance drift ({drift_pct:.1f}%). "
                "Immediate re-optimization recommended. Review recent findings for root cause."
            )

    return DriftReport(
        agent_name=agent_name,
        baseline_score=baseline_score,
        current_score=current_score,
        drift_pct=drift_pct,
        alert_level=alert_level,
        recommendation=recommendation,
    )


# ── run_drift_check ──────────────────────────────────────────────────────────


def run_drift_check(
    agent_db_path: Path,
    registry: list[AgentRegistryEntry],
) -> list[DriftReport]:
    """Run drift check for all agents in the registry that have verdict history.

    Args:
        agent_db_path: Path to agent_db.json.
        registry: List of registered agents.

    Returns:
        List of DriftReport objects. Agents without verdict history are skipped.
    """
    try:
        raw = agent_db_path.read_text(encoding="utf-8")
        agent_db: dict[str, Any] = json.loads(raw)
    except (OSError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[drift_detector] Could not read agent_db: {exc}", file=sys.stderr)
        return []

    reports: list[DriftReport] = []
    registry_names = {a.name for a in registry}

    for agent_name, entry in agent_db.items():
        if agent_name not in registry_names:
            continue

        verdicts = entry.get("verdicts", [])
        if not verdicts:
            continue  # skip agents without verdict history

        baseline_score = entry.get("score", 0.0)
        report = detect_drift(agent_name, baseline_score, verdicts)
        reports.append(report)

    return reports
