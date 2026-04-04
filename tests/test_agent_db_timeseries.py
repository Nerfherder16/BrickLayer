"""
tests/test_agent_db_timeseries.py — Time-series history and trend detection.

Covers:
  - record_run() stores run entries in run_history[]
  - Backward compat: existing entries without run_history key
  - run_history[] capped at 100 entries (oldest dropped)
  - get_trend() returns "insufficient_data" when < window runs
  - get_trend() detects upward trend
  - get_trend() detects downward trend
  - get_trend() returns stable when no significant delta
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bl.agent_db import get_trend, record_run  # noqa: E402


class TestRecordRunTimeSeries:
    def test_run_entry_stored_with_all_fields(self, tmp_path):
        """record_run() appends an entry to run_history[] with expected keys."""
        record_run(tmp_path, "agent-x", "HEALTHY", duration_ms=150, quality_score=0.8)

        db_path = tmp_path / "agent_db.json"
        assert db_path.exists()
        db = json.loads(db_path.read_text())

        history = db["agent-x"]["run_history"]
        assert len(history) == 1

        entry = history[0]
        assert entry["verdict"] == "HEALTHY"
        assert entry["duration_ms"] == 150
        assert entry["quality_score"] == 0.8
        assert "timestamp" in entry
        # timestamp should be a non-empty ISO-8601 string
        assert len(entry["timestamp"]) > 10

    def test_quality_score_none_serializes_as_null(self, tmp_path):
        """quality_score=None should appear as JSON null (not a string)."""
        record_run(tmp_path, "agent-x", "HEALTHY", duration_ms=0, quality_score=None)

        db = json.loads((tmp_path / "agent_db.json").read_text())
        entry = db["agent-x"]["run_history"][0]
        assert entry["quality_score"] is None  # Python None == JSON null

    def test_existing_entry_without_run_history_no_keyerror(self, tmp_path):
        """Calling record_run() on an existing entry with no run_history key is safe."""
        # Manually write a legacy entry (no run_history key)
        legacy_db = {
            "agent-legacy": {
                "runs": 5,
                "verdicts": {"HEALTHY": 5},
                "score": 1.0,
                "last_run": "2025-01-01T00:00:00+00:00",
                "created": "2025-01-01T00:00:00+00:00",
                "repair_count": 0,
                "last_repair": None,
            }
        }
        (tmp_path / "agent_db.json").write_text(json.dumps(legacy_db))

        # Should not raise KeyError
        score = record_run(tmp_path, "agent-legacy", "HEALTHY")
        assert isinstance(score, float)

        db = json.loads((tmp_path / "agent_db.json").read_text())
        # run_history was created and has one entry
        assert "run_history" in db["agent-legacy"]
        assert len(db["agent-legacy"]["run_history"]) == 1

    def test_run_history_capped_at_100(self, tmp_path):
        """Calling record_run() 101 times → run_history has exactly 100 entries (oldest dropped)."""
        for i in range(101):
            record_run(tmp_path, "agent-cap", "HEALTHY", duration_ms=i)

        db = json.loads((tmp_path / "agent_db.json").read_text())
        history = db["agent-cap"]["run_history"]
        assert len(history) == 100
        # The oldest entry (duration_ms=0) should have been dropped;
        # the newest entry should be the last one recorded (duration_ms=100)
        assert history[-1]["duration_ms"] == 100
        assert history[0]["duration_ms"] == 1  # entry 0 was dropped

    def test_integer_runs_counter_still_increments(self, tmp_path):
        """The existing integer runs counter must still work alongside run_history[]."""
        record_run(tmp_path, "agent-x", "HEALTHY")
        record_run(tmp_path, "agent-x", "FAILURE")

        db = json.loads((tmp_path / "agent_db.json").read_text())
        assert db["agent-x"]["runs"] == 2
        assert len(db["agent-x"]["run_history"]) == 2


class TestGetTrend:
    def _populate(self, tmp_path, agent_name: str, verdicts: list[str]):
        """Helper: record a sequence of verdicts."""
        for v in verdicts:
            record_run(tmp_path, agent_name, v)

    def test_insufficient_data_below_window(self, tmp_path):
        """< window runs → trending == 'insufficient_data'."""
        self._populate(tmp_path, "agent-few", ["HEALTHY", "HEALTHY", "FAILURE"])
        result = get_trend(tmp_path, "agent-few", window=5)
        assert result["trending"] == "insufficient_data"
        assert result["recent_runs"] == 3
        # score_recent is computed over the available runs
        assert isinstance(result["score_recent"], float)
        assert result["score_prior"] is None

    def test_exactly_window_runs_is_insufficient(self, tmp_path):
        """Exactly window runs → still insufficient (need window runs for recent + prior window for comparison)."""
        self._populate(tmp_path, "agent-exact", ["HEALTHY"] * 5)
        result = get_trend(tmp_path, "agent-exact", window=5)
        assert result["trending"] == "insufficient_data"

    def test_trending_up(self, tmp_path):
        """Last 5 all HEALTHY, prior 5 all FAILURE → trending == 'up'."""
        verdicts = ["FAILURE"] * 5 + ["HEALTHY"] * 5
        self._populate(tmp_path, "agent-up", verdicts)
        result = get_trend(tmp_path, "agent-up", window=5)
        assert result["trending"] == "up"
        assert result["score_recent"] == 1.0
        assert result["score_prior"] == 0.0

    def test_trending_down(self, tmp_path):
        """Last 5 all FAILURE, prior 5 all HEALTHY → trending == 'down'."""
        verdicts = ["HEALTHY"] * 5 + ["FAILURE"] * 5
        self._populate(tmp_path, "agent-down", verdicts)
        result = get_trend(tmp_path, "agent-down", window=5)
        assert result["trending"] == "down"
        assert result["score_recent"] == 0.0
        assert result["score_prior"] == 1.0

    def test_trending_stable(self, tmp_path):
        """Same mix in both windows → trending == 'stable'."""
        # 3 HEALTHY + 2 FAILURE in both windows → score 0.6 each
        verdicts = ["HEALTHY", "HEALTHY", "HEALTHY", "FAILURE", "FAILURE"] * 2
        self._populate(tmp_path, "agent-stable", verdicts)
        result = get_trend(tmp_path, "agent-stable", window=5)
        assert result["trending"] == "stable"
        assert result["score_recent"] == pytest.approx(0.6)
        assert result["score_prior"] == pytest.approx(0.6)

    def test_no_runs_at_all(self, tmp_path):
        """Agent not in DB → insufficient_data with score_recent=0.0."""
        result = get_trend(tmp_path, "agent-ghost", window=5)
        assert result["trending"] == "insufficient_data"
        assert result["recent_runs"] == 0
        assert result["score_prior"] is None

    def test_return_shape_has_all_keys(self, tmp_path):
        """get_trend() always returns the four required keys."""
        result = get_trend(tmp_path, "agent-keys", window=5)
        assert set(result.keys()) == {
            "score_recent",
            "score_prior",
            "trending",
            "recent_runs",
        }
