"""
tests/test_snapshot_agent.py — Tests for masonry/scripts/snapshot_agent.py.

Written before implementation. All tests must fail until the developer
completes the task.

The module under test: masonry/scripts/snapshot_agent.py
CLI:
    python masonry/scripts/snapshot_agent.py karen --score 0.84 --eval-size 20
    python masonry/scripts/snapshot_agent.py karen --rollback

Core functions tested:
    snapshot_agent(agent_name, base_dir, score, eval_size) -> Path
    rollback_agent(agent_name, base_dir) -> str
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# This import will fail (ImportError) until the developer creates the module.
from masonry.scripts.snapshot_agent import rollback_agent, snapshot_agent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_md(agent_dir: Path, agent_name: str, content: str) -> Path:
    """Create a minimal agent .md file inside a fake agents directory."""
    agents_dir = agent_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    md_file = agents_dir / f"{agent_name}.md"
    md_file.write_text(content, encoding="utf-8")
    return md_file


def _snapshots_dir(base_dir: Path, agent_name: str) -> Path:
    """Return the expected snapshot storage directory for an agent."""
    return base_dir / "masonry" / "agent_snapshots" / agent_name


def _baseline_path(base_dir: Path, agent_name: str) -> Path:
    """Return the expected baseline.json path for an agent."""
    return _snapshots_dir(base_dir, agent_name) / "baseline.json"


# ---------------------------------------------------------------------------
# Test 1: snapshot_creates_versioned_file
# ---------------------------------------------------------------------------


class TestSnapshotCreatesVersionedFile:
    """snapshot_agent creates a versioned .md file in the snapshot directory."""

    def test_snapshot_creates_versioned_file(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt v1")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        # The returned path must exist on disk
        assert snapshot_path.exists(), (
            f"snapshot_agent returned {snapshot_path!r} but file does not exist"
        )

        # File must be inside the expected snapshot directory
        expected_dir = _snapshots_dir(tmp_path, agent_name)
        assert snapshot_path.parent == expected_dir, (
            f"Snapshot file must be in {expected_dir!r}, got {snapshot_path.parent!r}"
        )

        # Filename must start with "v1_" (first snapshot)
        assert snapshot_path.name.startswith("v1_"), (
            f"First snapshot must be named v1_..., got {snapshot_path.name!r}"
        )

        # Filename must end with ".md"
        assert snapshot_path.suffix == ".md", (
            f"Snapshot file must be a .md file, got suffix {snapshot_path.suffix!r}"
        )

        # Filename must contain the score encoded as "s0.84"
        assert "s0.84" in snapshot_path.name, (
            f"Snapshot filename must contain 's0.84', got {snapshot_path.name!r}"
        )

    def test_snapshot_increments_version_on_second_call(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt v1")

        # First snapshot
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=10,
        )

        # Update agent content, then take a second snapshot
        md_file = tmp_path / ".claude" / "agents" / f"{agent_name}.md"
        md_file.write_text("# karen prompt v2", encoding="utf-8")

        second_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=10,
        )

        # Second snapshot must be v2
        assert second_path.name.startswith("v2_"), (
            f"Second snapshot must be named v2_..., got {second_path.name!r}"
        )


# ---------------------------------------------------------------------------
# Test 2: snapshot_updates_baseline
# ---------------------------------------------------------------------------


class TestSnapshotUpdatesBaseline:
    """snapshot_agent writes a valid baseline.json with all required fields."""

    REQUIRED_FIELDS = {
        "agent",
        "current_version",
        "score",
        "eval_size",
        "snapshot_file",
        "recorded_at",
    }

    def test_baseline_written_with_all_fields(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        baseline_path = _baseline_path(tmp_path, agent_name)
        assert baseline_path.exists(), (
            f"baseline.json must be written at {baseline_path!r}"
        )

        payload = json.loads(baseline_path.read_text(encoding="utf-8"))

        for field in self.REQUIRED_FIELDS:
            assert field in payload, (
                f"Required field '{field}' missing from baseline.json"
            )

    def test_baseline_field_values(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        payload = json.loads(
            _baseline_path(tmp_path, agent_name).read_text(encoding="utf-8")
        )

        assert payload["agent"] == agent_name, (
            f"Expected agent={agent_name!r}, got {payload['agent']!r}"
        )

        assert payload["score"] == 0.84, (
            f"Expected score=0.84, got {payload['score']!r}"
        )

        assert payload["eval_size"] == 20, (
            f"Expected eval_size=20, got {payload['eval_size']!r}"
        )

        # current_version must start with "v1_"
        assert payload["current_version"].startswith("v1_"), (
            f"current_version must start with 'v1_', got {payload['current_version']!r}"
        )

        # snapshot_file must be a non-empty string that ends with ".md"
        assert isinstance(payload["snapshot_file"], str), (
            "snapshot_file must be a string"
        )
        assert payload["snapshot_file"].endswith(".md"), (
            f"snapshot_file must reference a .md file, got {payload['snapshot_file']!r}"
        )

        # recorded_at must be a non-empty ISO-8601 string
        assert isinstance(payload["recorded_at"], str), (
            "recorded_at must be a string"
        )
        assert len(payload["recorded_at"]) >= 10, (
            f"recorded_at looks too short to be ISO-8601: {payload['recorded_at']!r}"
        )

        # current_version in baseline must match the returned snapshot filename (stem)
        assert payload["current_version"] == snapshot_path.stem, (
            f"current_version {payload['current_version']!r} must match snapshot stem "
            f"{snapshot_path.stem!r}"
        )


# ---------------------------------------------------------------------------
# Test 3: rollback_restores_content
# ---------------------------------------------------------------------------


class TestRollbackRestoresContent:
    """rollback_agent copies the previous snapshot content back to the agent .md file."""

    def test_rollback_restores_content(self, tmp_path: Path) -> None:
        agent_name = "karen"
        md_file = _make_agent_md(tmp_path, agent_name, "prompt A")

        # Take first snapshot while content is "prompt A"
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=10,
        )

        # Update agent content and take second snapshot
        md_file.write_text("prompt B", encoding="utf-8")
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=10,
        )

        # Confirm agent currently has "prompt B"
        assert md_file.read_text(encoding="utf-8") == "prompt B", (
            "Pre-condition failed: agent .md should contain 'prompt B' before rollback"
        )

        # Execute rollback
        rolled_back_version = rollback_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
        )

        # The agent .md must now contain "prompt A"
        restored_content = md_file.read_text(encoding="utf-8")
        assert restored_content == "prompt A", (
            f"After rollback, agent .md must contain 'prompt A', got {restored_content!r}"
        )

    def test_rollback_returns_version_string(self, tmp_path: Path) -> None:
        agent_name = "karen"
        md_file = _make_agent_md(tmp_path, agent_name, "prompt A")

        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=10,
        )

        md_file.write_text("prompt B", encoding="utf-8")
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=10,
        )

        rolled_back_version = rollback_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
        )

        # Must return the version label it rolled back to (e.g. "v1_20260323_s0.75")
        assert isinstance(rolled_back_version, str), (
            "rollback_agent must return a string version identifier"
        )
        assert rolled_back_version.startswith("v1_"), (
            f"Should have rolled back to v1, got {rolled_back_version!r}"
        )

    def test_rollback_updates_baseline_to_previous_version(self, tmp_path: Path) -> None:
        agent_name = "karen"
        md_file = _make_agent_md(tmp_path, agent_name, "prompt A")

        first_snap = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=10,
        )

        md_file.write_text("prompt B", encoding="utf-8")
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=10,
        )

        rollback_agent(agent_name=agent_name, base_dir=tmp_path)

        # baseline.json must now point to the first snapshot (v1)
        payload = json.loads(
            _baseline_path(tmp_path, agent_name).read_text(encoding="utf-8")
        )
        assert payload["current_version"] == first_snap.stem, (
            f"After rollback, baseline current_version must be {first_snap.stem!r}, "
            f"got {payload['current_version']!r}"
        )


# ---------------------------------------------------------------------------
# Test 4: rollback_no_previous_version
# ---------------------------------------------------------------------------


class TestRollbackNoPreviousVersion:
    """rollback_agent raises ValueError when there is only one snapshot."""

    def test_rollback_raises_when_only_one_snapshot(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "prompt A")

        # Take only one snapshot — there is nothing to roll back to
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        with pytest.raises(ValueError):
            rollback_agent(agent_name=agent_name, base_dir=tmp_path)

    def test_rollback_error_message_is_descriptive(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "prompt A")

        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        with pytest.raises(ValueError, match="[Nn]o previous") as exc_info:
            rollback_agent(agent_name=agent_name, base_dir=tmp_path)

        # The message must mention the agent name so callers know what failed
        assert agent_name in str(exc_info.value), (
            f"ValueError message must mention agent name '{agent_name}'"
        )


# ---------------------------------------------------------------------------
# Test 5: snapshot_writes_sidecar_json
# ---------------------------------------------------------------------------


class TestSnapshotWritesSidecarJson:
    """snapshot_agent writes a sidecar .json file alongside each .md snapshot."""

    REQUIRED_SIDECAR_FIELDS = {
        "agent",
        "version",
        "score",
        "eval_size",
        "snapshot_file",
        "recorded_at",
    }

    def test_sidecar_written_alongside_md(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        # Sidecar must exist next to the .md file with same stem
        sidecar_path = snapshot_path.with_suffix(".json")
        assert sidecar_path.exists(), (
            f"Sidecar JSON must be written at {sidecar_path!r}"
        )

    def test_sidecar_contains_all_required_fields(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        sidecar_path = snapshot_path.with_suffix(".json")
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))

        for field in self.REQUIRED_SIDECAR_FIELDS:
            assert field in sidecar, (
                f"Required sidecar field '{field}' missing"
            )

    def test_sidecar_field_values_match_snapshot(self, tmp_path: Path) -> None:
        agent_name = "karen"
        _make_agent_md(tmp_path, agent_name, "# karen prompt")

        snapshot_path = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.84,
            eval_size=20,
        )

        sidecar_path = snapshot_path.with_suffix(".json")
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))

        assert sidecar["agent"] == agent_name
        assert sidecar["score"] == 0.84
        assert sidecar["eval_size"] == 20
        assert sidecar["version"] == snapshot_path.stem
        assert sidecar["snapshot_file"].endswith(".md")
        assert len(sidecar["recorded_at"]) >= 10


# ---------------------------------------------------------------------------
# Test 6: rollback_restores_score_from_sidecar
# ---------------------------------------------------------------------------


class TestRollbackRestoresScoreFromSidecar:
    """rollback_agent restores score, eval_size, and recorded_at from the sidecar."""

    def test_rollback_restores_score_from_sidecar(self, tmp_path: Path) -> None:
        agent_name = "karen"
        md_file = _make_agent_md(tmp_path, agent_name, "prompt A")

        # First snapshot with score 0.75
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=15,
        )

        # Second snapshot with score 0.88
        md_file.write_text("prompt B", encoding="utf-8")
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=20,
        )

        # Rollback to v1
        rollback_agent(agent_name=agent_name, base_dir=tmp_path)

        # baseline.json must now have the v1 score and eval_size
        payload = json.loads(
            _baseline_path(tmp_path, agent_name).read_text(encoding="utf-8")
        )

        assert payload["score"] == 0.75, (
            f"After rollback, baseline score must be 0.75 (v1's score), got {payload['score']!r}"
        )
        assert payload["eval_size"] == 15, (
            f"After rollback, baseline eval_size must be 15 (v1's eval_size), got {payload['eval_size']!r}"
        )

    def test_rollback_without_sidecar_clears_score(self, tmp_path: Path) -> None:
        """When the sidecar is missing, rollback sets score to None."""
        agent_name = "karen"
        md_file = _make_agent_md(tmp_path, agent_name, "prompt A")

        # First snapshot (will have a sidecar)
        first_snap = snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.75,
            eval_size=15,
        )

        # Remove the v1 sidecar to simulate missing sidecar scenario
        first_sidecar = first_snap.with_suffix(".json")
        first_sidecar.unlink()

        # Second snapshot
        md_file.write_text("prompt B", encoding="utf-8")
        snapshot_agent(
            agent_name=agent_name,
            base_dir=tmp_path,
            score=0.88,
            eval_size=20,
        )

        # Rollback — no sidecar for v1
        rollback_agent(agent_name=agent_name, base_dir=tmp_path)

        payload = json.loads(
            _baseline_path(tmp_path, agent_name).read_text(encoding="utf-8")
        )

        # score must be None (cleared) when sidecar is missing
        assert payload["score"] is None, (
            f"Without a sidecar, rollback must set score=None, got {payload['score']!r}"
        )
