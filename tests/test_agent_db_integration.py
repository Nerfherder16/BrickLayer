"""Integration test for agent_db write-after-finding flow."""

import json
from bl.agent_db import record_run, get_score, get_trend, get_underperformers


class TestAgentDbRoundTrip:
    def test_record_creates_file(self, tmp_path):
        """record_run creates agent_db.json if it doesn't exist."""
        score = record_run(tmp_path, "quantitative-analyst", "HEALTHY")
        assert (tmp_path / "agent_db.json").exists()
        assert score == 1.0

    def test_score_updates_after_multiple_runs(self, tmp_path):
        """Score reflects verdict distribution after multiple runs."""
        record_run(tmp_path, "fix-implementer", "FIXED")
        record_run(tmp_path, "fix-implementer", "FIXED")
        record_run(tmp_path, "fix-implementer", "INCONCLUSIVE")
        score = get_score(tmp_path, "fix-implementer")
        # 2 success + 0 partial + 1 failure = 2/3 ≈ 0.6667
        assert 0.66 < score < 0.67

    def test_trend_insufficient_data(self, tmp_path):
        """Trend returns insufficient_data with fewer than window runs."""
        record_run(tmp_path, "diagnose-analyst", "DIAGNOSIS_COMPLETE")
        trend = get_trend(tmp_path, "diagnose-analyst", window=5)
        assert trend["trending"] == "insufficient_data"

    def test_trend_detects_decline(self, tmp_path):
        """Trend detects declining performance across windows."""
        agent = "competitive-analyst"
        # 5 good runs then 5 bad runs
        for _ in range(5):
            record_run(tmp_path, agent, "HEALTHY")
        for _ in range(5):
            record_run(tmp_path, agent, "INCONCLUSIVE")
        trend = get_trend(tmp_path, agent, window=5)
        assert trend["trending"] == "down"

    def test_underperformers_detected(self, tmp_path):
        """Agents below threshold with enough runs are flagged."""
        for _ in range(5):
            record_run(tmp_path, "bad-agent", "INCONCLUSIVE")
        result = get_underperformers(tmp_path, threshold=0.40, min_runs=3)
        assert len(result) == 1
        assert result[0]["name"] == "bad-agent"

    def test_json_schema_shape(self, tmp_path):
        """agent_db.json has expected schema after recording."""
        record_run(
            tmp_path, "test-agent", "HEALTHY", duration_ms=1500, quality_score=0.9
        )
        db = json.loads((tmp_path / "agent_db.json").read_text())
        rec = db["test-agent"]
        assert "runs" in rec
        assert "verdicts" in rec
        assert "score" in rec
        assert "last_run" in rec
        assert "run_history" in rec
        assert len(rec["run_history"]) == 1
        assert rec["run_history"][0]["verdict"] == "HEALTHY"
        assert rec["run_history"][0]["duration_ms"] == 1500
