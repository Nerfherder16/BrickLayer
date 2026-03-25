"""Tests for agent_db.json run history appending in score_all_agents.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from masonry.scripts.score_all_agents import write_agent_db_record  # noqa: E402


def _make_record(
    score: float = 0.85,
    verdict: str = "HEALTHY",
) -> dict:
    return {
        "score": score,
        "verdicts": ["COMPLETE"],
        "questions": 5,
        "overall": verdict,
        "confidences": [1.0],
    }


def test_runs_array_populated(tmp_path: Path) -> None:
    """After two writes for the same agent, runs array has 2 entries."""
    db_path = tmp_path / "agent_db.json"

    write_agent_db_record("test-agent", _make_record(), db_path)
    write_agent_db_record("test-agent", _make_record(score=0.90), db_path)

    data = json.loads(db_path.read_text())
    runs = data["test-agent"]["runs"]
    assert len(runs) == 2, f"Expected 2 runs, got {len(runs)}"


def test_runs_array_capped_at_50(tmp_path: Path) -> None:
    """runs array never exceeds 50 entries."""
    db_path = tmp_path / "agent_db.json"

    for i in range(55):
        write_agent_db_record("test-agent", _make_record(score=0.5 + i * 0.001), db_path)

    data = json.loads(db_path.read_text())
    runs = data["test-agent"]["runs"]
    assert len(runs) == 50, f"Expected 50 runs (capped), got {len(runs)}"


def test_run_entry_shape(tmp_path: Path) -> None:
    """Each run entry has timestamp, verdict, score, duration_ms, quality_score."""
    db_path = tmp_path / "agent_db.json"

    write_agent_db_record("test-agent", _make_record(score=0.77, verdict="WARNING"), db_path)

    data = json.loads(db_path.read_text())
    run = data["test-agent"]["runs"][0]

    assert "timestamp" in run, "run entry missing 'timestamp'"
    assert "verdict" in run, "run entry missing 'verdict'"
    assert "score" in run, "run entry missing 'score'"
    assert "duration_ms" in run, "run entry missing 'duration_ms'"
    assert "quality_score" in run, "run entry missing 'quality_score'"


def test_run_verdict_matches_overall(tmp_path: Path) -> None:
    """The verdict field in the run entry matches the overall field of the record."""
    db_path = tmp_path / "agent_db.json"

    write_agent_db_record("test-agent", _make_record(verdict="WARNING"), db_path)

    data = json.loads(db_path.read_text())
    run = data["test-agent"]["runs"][0]
    assert run["verdict"] == "WARNING"


def test_existing_fields_preserved(tmp_path: Path) -> None:
    """Top-level fields (score, verdicts, questions, overall, confidences) are preserved."""
    db_path = tmp_path / "agent_db.json"

    record = _make_record(score=0.75)
    write_agent_db_record("test-agent", record, db_path)

    data = json.loads(db_path.read_text())
    agent_rec = data["test-agent"]

    assert agent_rec["score"] == 0.75
    assert agent_rec["overall"] == "HEALTHY"
    assert "verdicts" in agent_rec
    assert "questions" in agent_rec
    assert "confidences" in agent_rec


def test_run_score_matches_record_score(tmp_path: Path) -> None:
    """The score field in the run entry matches the record score."""
    db_path = tmp_path / "agent_db.json"

    write_agent_db_record("test-agent", _make_record(score=0.63), db_path)

    data = json.loads(db_path.read_text())
    run = data["test-agent"]["runs"][0]
    assert abs(run["score"] - 0.63) < 1e-9


def test_runs_trim_oldest_first(tmp_path: Path) -> None:
    """When capping at 50, the oldest entries are dropped (most recent kept)."""
    db_path = tmp_path / "agent_db.json"

    # Write 51 entries with distinct scores 0.0, 0.001, ..., 0.050
    for i in range(51):
        write_agent_db_record("test-agent", _make_record(score=round(i * 0.001, 4)), db_path)

    data = json.loads(db_path.read_text())
    runs = data["test-agent"]["runs"]
    assert len(runs) == 50
    # The most recent (score=0.050) should be present
    scores = [r["score"] for r in runs]
    assert round(0.050, 4) in scores, "Most recent entry should be kept after trim"
    # The oldest (score=0.000) should have been dropped
    assert 0.000 not in scores, "Oldest entry should have been dropped"
