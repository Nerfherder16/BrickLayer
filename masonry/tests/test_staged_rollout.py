"""Tests for staged rollout functionality in masonry/scripts/improve_agent.py"""

import json
import dataclasses
import pytest
from pathlib import Path


class TestStagedRolloutDataclass:
    """Tests for the StagedRollout dataclass."""

    def test_import(self):
        """StagedRollout must be importable from improve_agent."""
        from masonry.scripts.improve_agent import StagedRollout
        assert StagedRollout is not None

    def test_stages_default(self):
        """Default stages list must be [0.05, 0.20, 0.50, 1.00]."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.7)
        assert sr.stages == [0.05, 0.20, 0.50, 1.00]

    def test_rollback_threshold_default(self):
        """Default rollback_threshold must be -0.05."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.7)
        assert sr.rollback_threshold == pytest.approx(-0.05)

    def test_should_rollback_true_on_sharp_drop(self):
        """should_rollback returns True when score drops more than 5% vs baseline."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.8)
        # 0.74 - 0.80 = -0.06, which is < -0.05 threshold
        assert sr.should_rollback(0.74) is True

    def test_should_rollback_false_within_threshold(self):
        """should_rollback returns False when score is within the threshold."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.8)
        # 0.76 - 0.80 = -0.04, which is > -0.05 threshold
        assert sr.should_rollback(0.76) is False

    def test_should_rollback_false_on_improvement(self):
        """should_rollback returns False when score improves."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.7)
        assert sr.should_rollback(0.85) is False

    def test_should_rollback_false_at_exact_threshold(self):
        """should_rollback returns False when drop equals exactly the threshold."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.80)
        # 0.75 - 0.80 = -0.05, which is NOT < -0.05
        assert sr.should_rollback(0.75) is False

    def test_next_stage_progression(self):
        """next_stage returns correct next percentage in sequence."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.7)
        assert sr.next_stage(0.05) == pytest.approx(0.20)
        assert sr.next_stage(0.20) == pytest.approx(0.50)
        assert sr.next_stage(0.50) == pytest.approx(1.00)

    def test_next_stage_returns_none_at_100(self):
        """next_stage returns None when already at 100%."""
        from masonry.scripts.improve_agent import StagedRollout
        sr = StagedRollout(agent_name="test-agent", baseline_score=0.7)
        assert sr.next_stage(1.00) is None

    def test_dataclass_fields_present(self):
        """StagedRollout must have expected fields."""
        from masonry.scripts.improve_agent import StagedRollout
        field_names = {f.name for f in dataclasses.fields(StagedRollout)}
        assert "agent_name" in field_names
        assert "baseline_score" in field_names
        assert "stages" in field_names
        assert "rollback_threshold" in field_names


class TestSaveSnapshot:
    """Tests for save_snapshot function."""

    def test_save_snapshot_creates_file(self, tmp_path):
        """save_snapshot creates a JSON file in the correct directory."""
        from masonry.scripts.improve_agent import save_snapshot
        path = save_snapshot(
            agent_name="test-agent",
            instructions="some instructions",
            score=0.75,
            stage=0.05,
            base_dir=tmp_path,
        )
        assert Path(path).exists()

    def test_save_snapshot_correct_json_structure(self, tmp_path):
        """save_snapshot writes JSON with required fields."""
        from masonry.scripts.improve_agent import save_snapshot
        path = save_snapshot(
            agent_name="test-agent",
            instructions="my instructions text",
            score=0.85,
            stage=0.20,
            base_dir=tmp_path,
        )
        data = json.loads(Path(path).read_text())
        assert data["agent_name"] == "test-agent"
        assert data["instructions"] == "my instructions text"
        assert data["score"] == pytest.approx(0.85)
        assert data["stage_pct"] == pytest.approx(0.20)
        assert "timestamp" in data

    def test_save_snapshot_correct_directory(self, tmp_path):
        """save_snapshot places file under masonry/agent_snapshots/{agent}/history/."""
        from masonry.scripts.improve_agent import save_snapshot
        path = save_snapshot(
            agent_name="my-agent",
            instructions="instructions",
            score=0.6,
            stage=0.50,
            base_dir=tmp_path,
        )
        expected_parent = tmp_path / "masonry" / "agent_snapshots" / "my-agent" / "history"
        assert Path(path).parent == expected_parent

    def test_save_snapshot_filename_contains_stage(self, tmp_path):
        """save_snapshot filename contains stage percentage."""
        from masonry.scripts.improve_agent import save_snapshot
        path = save_snapshot(
            agent_name="test-agent",
            instructions="inst",
            score=0.7,
            stage=0.50,
            base_dir=tmp_path,
        )
        assert "stage" in Path(path).name

    def test_save_snapshot_returns_string_path(self, tmp_path):
        """save_snapshot returns a string (not a Path object)."""
        from masonry.scripts.improve_agent import save_snapshot
        result = save_snapshot(
            agent_name="test-agent",
            instructions="inst",
            score=0.7,
            stage=0.05,
            base_dir=tmp_path,
        )
        assert isinstance(result, str)


class TestRunStagedRollout:
    """Tests for run_staged_rollout function."""

    def test_promoted_on_steady_improvement(self, tmp_path):
        """run_staged_rollout returns PROMOTED when new score steadily exceeds baseline."""
        from masonry.scripts.improve_agent import run_staged_rollout
        # new_score = 0.90, baseline = 0.70 — every stage score stays well above threshold
        status, final_score = run_staged_rollout(
            agent_name="test-agent",
            new_instructions="improved instructions",
            baseline_score=0.70,
            new_score=0.90,
            base_dir=tmp_path,
        )
        assert status == "PROMOTED"
        assert isinstance(final_score, float)

    def test_rollback_on_sharp_drop(self, tmp_path):
        """run_staged_rollout returns ROLLBACK when staged score triggers rollback threshold."""
        from masonry.scripts.improve_agent import run_staged_rollout
        # new_score = 0.60, baseline = 0.80
        # stage 0.05: 0.80 + (0.60 - 0.80)*0.05 = 0.80 - 0.01 = 0.79 — safe
        # stage 0.20: 0.80 + (0.60 - 0.80)*0.20 = 0.80 - 0.04 = 0.76 — safe
        # stage 0.50: 0.80 + (0.60 - 0.80)*0.50 = 0.80 - 0.10 = 0.70 — drop = -0.10 < -0.05 → rollback
        result = run_staged_rollout(
            agent_name="test-agent",
            new_instructions="worse instructions",
            baseline_score=0.80,
            new_score=0.60,
            base_dir=tmp_path,
        )
        assert result[0] == "ROLLBACK"
        assert len(result) == 3  # ("ROLLBACK", stage, reason)

    def test_rollback_result_contains_stage_and_reason(self, tmp_path):
        """ROLLBACK result tuple contains the failing stage and a reason string."""
        from masonry.scripts.improve_agent import run_staged_rollout
        result = run_staged_rollout(
            agent_name="test-agent",
            new_instructions="worse instructions",
            baseline_score=0.80,
            new_score=0.60,
            base_dir=tmp_path,
        )
        assert result[0] == "ROLLBACK"
        stage = result[1]
        reason = result[2]
        assert isinstance(stage, float)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_promoted_result_has_two_elements(self, tmp_path):
        """PROMOTED result is a 2-tuple: (status, final_score)."""
        from masonry.scripts.improve_agent import run_staged_rollout
        result = run_staged_rollout(
            agent_name="test-agent",
            new_instructions="good instructions",
            baseline_score=0.70,
            new_score=0.85,
            base_dir=tmp_path,
        )
        assert len(result) == 2
        assert result[0] == "PROMOTED"

    def test_snapshots_saved_for_each_stage(self, tmp_path):
        """run_staged_rollout saves a snapshot file for each completed stage."""
        from masonry.scripts.improve_agent import run_staged_rollout
        run_staged_rollout(
            agent_name="snap-agent",
            new_instructions="good instructions",
            baseline_score=0.70,
            new_score=0.90,
            base_dir=tmp_path,
        )
        history_dir = tmp_path / "masonry" / "agent_snapshots" / "snap-agent" / "history"
        snapshots = list(history_dir.glob("*.json"))
        # 4 stages: 0.05, 0.20, 0.50, 1.00
        assert len(snapshots) == 4

    def test_staged_score_formula(self, tmp_path):
        """Staged score uses baseline + (new - baseline) * stage_pct formula."""
        from masonry.scripts.improve_agent import run_staged_rollout
        # Use a score that just barely clears rollback at all stages
        # baseline=0.70, new=0.90 → all staged scores are above baseline - 0.05
        result = run_staged_rollout(
            agent_name="formula-agent",
            new_instructions="instructions",
            baseline_score=0.70,
            new_score=0.90,
            base_dir=tmp_path,
        )
        # final score at stage 1.00 = 0.70 + (0.90 - 0.70)*1.00 = 0.90
        assert result[0] == "PROMOTED"
        assert result[1] == pytest.approx(0.90)
