"""Tests for masonry/src/dspy_pipeline/drift_detector.py."""

from __future__ import annotations

import json
from pathlib import Path


from masonry.src.dspy_pipeline.drift_detector import (
    DriftReport,
    detect_drift,
    run_drift_check,
)
from masonry.src.schemas import AgentRegistryEntry


# ──────────────────────────────────────────────────────────────────────────
# detect_drift
# ──────────────────────────────────────────────────────────────────────────


class TestDetectDrift:
    def test_all_healthy_verdicts_no_drift(self):
        verdicts = ["HEALTHY", "HEALTHY", "HEALTHY", "HEALTHY", "HEALTHY"]
        report = detect_drift("test-agent", baseline_score=0.85, recent_verdicts=verdicts)

        assert report.agent_name == "test-agent"
        assert report.current_score == 1.0
        assert report.drift_pct < 10
        assert report.alert_level == "ok"

    def test_all_failure_verdicts_critical_drift(self):
        verdicts = ["FAILURE", "FAILURE", "FAILURE", "FAILURE"]
        report = detect_drift("test-agent", baseline_score=0.85, recent_verdicts=verdicts)

        assert report.current_score == 0.0
        assert report.drift_pct > 25
        assert report.alert_level == "critical"

    def test_mixed_verdicts_warning_drift(self):
        # Mix: some pass, some fail → current ~0.5
        verdicts = ["HEALTHY", "FAILURE", "WARNING", "HEALTHY"]
        report = detect_drift("test-agent", baseline_score=0.85, recent_verdicts=verdicts)

        # current_score: (1.0 + 0.0 + 0.5 + 1.0) / 4 = 0.625
        assert 0.5 < report.current_score < 0.8

    def test_empty_verdicts_ok(self):
        """Empty verdict list should not crash."""
        report = detect_drift("test-agent", baseline_score=0.85, recent_verdicts=[])
        assert isinstance(report, DriftReport)

    def test_report_has_recommendation(self):
        verdicts = ["FAILURE"] * 5
        report = detect_drift("test-agent", baseline_score=0.8, recent_verdicts=verdicts)
        assert len(report.recommendation) > 0

    def test_alert_level_thresholds(self):
        # < 10% drift → ok
        # Baseline 0.8, need current >= 0.72 for < 10% drift
        # HEALTHY = 1.0, which gives 0% drift from 0.8 baseline? No:
        # drift_pct = (0.8 - 1.0) / 0.8 * 100 = -25% → ok (negative drift = improvement)
        verdicts_better = ["HEALTHY"] * 5
        report = detect_drift("a", baseline_score=0.8, recent_verdicts=verdicts_better)
        assert report.alert_level == "ok"

        # > 25% drift → critical
        verdicts_worse = ["FAILURE"] * 5
        report = detect_drift("a", baseline_score=0.8, recent_verdicts=verdicts_worse)
        assert report.alert_level == "critical"

    def test_partial_verdicts_are_scored_0_5(self):
        verdicts = ["PARTIAL", "PARTIAL"]
        report = detect_drift("a", baseline_score=1.0, recent_verdicts=verdicts)
        assert abs(report.current_score - 0.5) < 0.01

    def test_ok_verdicts_scored_1_0(self):
        for v in ["HEALTHY", "FIXED", "COMPLIANT", "CALIBRATED"]:
            verdicts = [v]
            report = detect_drift("a", baseline_score=0.9, recent_verdicts=verdicts)
            assert report.current_score == 1.0, f"Expected 1.0 for {v}"

    def test_failure_verdicts_scored_0_0(self):
        for v in ["FAILURE", "NON_COMPLIANT"]:
            verdicts = [v]
            report = detect_drift("a", baseline_score=0.9, recent_verdicts=verdicts)
            assert report.current_score == 0.0, f"Expected 0.0 for {v}"

    def test_drift_report_is_pydantic_model(self):
        report = detect_drift("a", 0.8, ["HEALTHY"])
        assert isinstance(report, DriftReport)
        # Should be serializable
        data = report.model_dump()
        assert "agent_name" in data
        assert "alert_level" in data


# ──────────────────────────────────────────────────────────────────────────
# run_drift_check
# ──────────────────────────────────────────────────────────────────────────


class TestRunDriftCheck:
    def _make_agent_db(self, tmp_path: Path, agents: dict) -> Path:
        db_path = tmp_path / "agent_db.json"
        db_path.write_text(json.dumps(agents), encoding="utf-8")
        return db_path

    def _make_registry(self) -> list[AgentRegistryEntry]:
        return [
            AgentRegistryEntry(name="quantitative-analyst", file="qa.md", tier="trusted"),
            AgentRegistryEntry(name="fix-agent", file="fix.md", tier="candidate"),
        ]

    def test_returns_list_of_drift_reports(self, tmp_path):
        agent_db = {
            "quantitative-analyst": {
                "score": 0.85,
                "verdicts": ["HEALTHY", "HEALTHY", "WARNING"],
            },
        }
        db_path = self._make_agent_db(tmp_path, agent_db)
        registry = self._make_registry()

        reports = run_drift_check(db_path, registry)

        assert isinstance(reports, list)
        for r in reports:
            assert isinstance(r, DriftReport)

    def test_missing_agent_db_returns_empty(self, tmp_path):
        reports = run_drift_check(Path("/does/not/exist/agent_db.json"), self._make_registry())
        assert reports == []

    def test_agents_without_verdicts_skipped(self, tmp_path):
        agent_db = {
            "quantitative-analyst": {"score": 0.85},  # no verdicts
        }
        db_path = self._make_agent_db(tmp_path, agent_db)
        reports = run_drift_check(db_path, self._make_registry())
        assert len(reports) == 0

    def test_agent_with_verdicts_gets_report(self, tmp_path):
        agent_db = {
            "quantitative-analyst": {
                "score": 0.85,
                "verdicts": ["HEALTHY", "FAILURE", "WARNING"],
            },
        }
        db_path = self._make_agent_db(tmp_path, agent_db)
        reports = run_drift_check(db_path, self._make_registry())
        assert len(reports) == 1
        assert reports[0].agent_name == "quantitative-analyst"
