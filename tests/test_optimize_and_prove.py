"""
tests/test_optimize_and_prove.py — Tests for masonry/scripts/optimize_and_prove.py.

Written before implementation. All tests must fail (ImportError) until the developer
creates the module.

The module under test: masonry/scripts/optimize_and_prove.py

Responsibilities:
- Run eval_agent.py to get score_before
- Snapshot current prompt via snapshot_agent.py
- Run optimize_claude.py to generate a candidate prompt
- Run eval_agent.py again to get score_after
- Deploy (snapshot new) if score_after >= score_before + min_delta AND score_after >= min_score
- Rollback (snapshot --rollback) otherwise
- Return {"deployed": bool, "score_before": float, "score_after": float, "delta": float}
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


# This import will fail (ImportError) until the developer creates the module.
from masonry.scripts.optimize_and_prove import run_optimize_and_prove


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_process() -> MagicMock:
    """Mock subprocess.CompletedProcess with returncode=0."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""
    return result


def _write_eval_json(path: Path, agent: str, score: float) -> None:
    """Write a minimal eval_latest.json to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "agent": agent,
        "score": score,
        "eval_size": 20,
        "passed": int(score * 20),
        "failed": 20 - int(score * 20),
        "evaluated_at": "2026-03-23T00:00:00Z",
        "model": "claude-sonnet-4-6",
        "examples": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: deploys when score improves above both thresholds
# ---------------------------------------------------------------------------


class TestDeploysOnImprovement:
    """
    When score_after >= score_before + min_delta AND score_after >= min_score,
    the pipeline deploys: snapshots the new prompt and returns deployed=True.
    """

    def test_deploys_on_improvement(self, tmp_path: Path) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.84
        score_after = 0.89

        # First read returns score_before; second read returns score_after.
        call_count = 0

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            proc = _ok_process()
            # The first eval call triggers writing score_before; the second writes score_after.
            # We simulate the file being updated by the subprocess by writing it here.
            if "eval_agent.py" in " ".join(str(c) for c in cmd):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return proc

        with patch("subprocess.run", side_effect=_fake_subprocess) as mock_sub:
            result = run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                signature="karen",
                eval_size=20,
                min_delta=0.01,
                min_score=0.70,
            )

        assert result["deployed"] is True
        assert abs(result["score_before"] - score_before) < 1e-9
        assert abs(result["score_after"] - score_after) < 1e-9
        assert abs(result["delta"] - (score_after - score_before)) < 1e-9

    def test_deploys_prints_deployed_message(
        self, tmp_path: Path, capsys
    ) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.84
        score_after = 0.89
        call_count = 0

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            if "eval_agent.py" in " ".join(str(c) for c in cmd):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                signature="karen",
                eval_size=20,
                min_delta=0.01,
                min_score=0.70,
            )

        captured = capsys.readouterr()
        assert "DEPLOYED" in captured.out
        assert agent_name in captured.out


# ---------------------------------------------------------------------------
# Test 2: rejects and rolls back when score_after is worse
# ---------------------------------------------------------------------------


class TestRejectsWhenWorse:
    """
    When score_after < score_before, the pipeline must:
    - call snapshot_agent.py --rollback
    - return deployed=False
    - print a message containing "REJECTED"
    """

    def test_rejects_when_worse(self, tmp_path: Path, capsys) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.84
        score_after = 0.82
        call_count = 0
        subprocess_cmds: list[list[str]] = []

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            cmd_str_list = [str(c) for c in cmd]
            subprocess_cmds.append(cmd_str_list)
            if "eval_agent.py" in " ".join(cmd_str_list):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            result = run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                signature="karen",
                eval_size=20,
                min_delta=0.01,
                min_score=0.70,
            )

        assert result["deployed"] is False
        assert abs(result["score_before"] - score_before) < 1e-9
        assert abs(result["score_after"] - score_after) < 1e-9

        # snapshot_agent.py --rollback must have been called
        rollback_calls = [
            cmd for cmd in subprocess_cmds
            if "snapshot_agent.py" in " ".join(cmd) and "--rollback" in cmd
        ]
        assert len(rollback_calls) >= 1, (
            "Expected at least one snapshot_agent.py --rollback call, got none. "
            f"All subprocess calls: {subprocess_cmds}"
        )

        captured = capsys.readouterr()
        assert "REJECTED" in captured.out

    def test_return_dict_has_all_keys_when_rejected(self, tmp_path: Path) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.84
        score_after = 0.82
        call_count = 0

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            if "eval_agent.py" in " ".join(str(c) for c in cmd):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            result = run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
            )

        assert "deployed" in result
        assert "score_before" in result
        assert "score_after" in result
        assert "delta" in result


# ---------------------------------------------------------------------------
# Test 3: rejects when score_after is above baseline delta but below min_score floor
# ---------------------------------------------------------------------------


class TestRejectsBelowFloor:
    """
    When score_after >= score_before + min_delta but score_after < min_score,
    the pipeline must reject and rollback — both gates must be satisfied.
    """

    def test_rejects_below_floor(self, tmp_path: Path) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        # 0.68 → 0.69: improved by 0.01 (>= min_delta=0.01) BUT below min_score=0.70
        score_before = 0.68
        score_after = 0.69
        call_count = 0
        subprocess_cmds: list[list[str]] = []

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            cmd_str_list = [str(c) for c in cmd]
            subprocess_cmds.append(cmd_str_list)
            if "eval_agent.py" in " ".join(cmd_str_list):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            result = run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                min_delta=0.01,
                min_score=0.70,
            )

        assert result["deployed"] is False, (
            f"Expected deployed=False because score_after ({score_after}) < min_score (0.70), "
            f"got deployed={result['deployed']}"
        )

        rollback_calls = [
            cmd for cmd in subprocess_cmds
            if "snapshot_agent.py" in " ".join(cmd) and "--rollback" in cmd
        ]
        assert len(rollback_calls) >= 1, (
            "Expected rollback call when score_after is below min_score floor"
        )


# ---------------------------------------------------------------------------
# Test 4: rejects when delta is too small (below min_delta)
# ---------------------------------------------------------------------------


class TestMinDeltaRequired:
    """
    When score_after - score_before < min_delta, the pipeline rejects even if
    score_after is technically higher. The improvement is not meaningful enough.
    """

    def test_min_delta_required(self, tmp_path: Path) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        # 0.84 → 0.845: delta=0.005, which is below min_delta=0.01
        score_before = 0.84
        score_after = 0.845
        call_count = 0
        subprocess_cmds: list[list[str]] = []

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            cmd_str_list = [str(c) for c in cmd]
            subprocess_cmds.append(cmd_str_list)
            if "eval_agent.py" in " ".join(cmd_str_list):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            result = run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                min_delta=0.01,
                min_score=0.70,
            )

        assert result["deployed"] is False, (
            f"Expected deployed=False because delta ({score_after - score_before:.4f}) "
            f"< min_delta (0.01), got deployed={result['deployed']}"
        )

        rollback_calls = [
            cmd for cmd in subprocess_cmds
            if "snapshot_agent.py" in " ".join(cmd) and "--rollback" in cmd
        ]
        assert len(rollback_calls) >= 1, (
            "Expected rollback call when delta is below min_delta threshold"
        )


# ---------------------------------------------------------------------------
# Test 5: subprocess call order is correct
# ---------------------------------------------------------------------------


class TestSubprocessCallOrder:
    """
    The pipeline must invoke the four scripts in the correct order:
    1. eval_agent.py  (score_before)
    2. snapshot_agent.py (no --rollback flag, with --score)
    3. optimize_claude.py
    4. eval_agent.py  (score_after)
    5a. snapshot_agent.py (no --rollback, with --score)  — on deploy
    5b. snapshot_agent.py --rollback                     — on reject
    """

    def test_script_call_order_on_deploy(self, tmp_path: Path) -> None:
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.80
        score_after = 0.90
        call_count = 0
        ordered_scripts: list[str] = []

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            cmd_joined = " ".join(str(c) for c in cmd)
            for script in ("eval_agent.py", "snapshot_agent.py", "optimize_claude.py"):
                if script in cmd_joined:
                    ordered_scripts.append(script)
                    break
            if "eval_agent.py" in cmd_joined:
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                min_delta=0.01,
                min_score=0.70,
            )

        # Must have at least 5 calls in the pipeline
        assert len(ordered_scripts) >= 5, (
            f"Expected at least 5 subprocess calls, got {len(ordered_scripts)}: {ordered_scripts}"
        )

        # First call must be eval_agent.py
        assert ordered_scripts[0] == "eval_agent.py", (
            f"First subprocess call must be eval_agent.py, got {ordered_scripts[0]}"
        )

        # Second call must be snapshot_agent.py (pre-optimization snapshot)
        assert ordered_scripts[1] == "snapshot_agent.py", (
            f"Second subprocess call must be snapshot_agent.py, got {ordered_scripts[1]}"
        )

        # Third call must be optimize_claude.py
        assert ordered_scripts[2] == "optimize_claude.py", (
            f"Third subprocess call must be optimize_claude.py, got {ordered_scripts[2]}"
        )

        # Fourth call must be eval_agent.py (post-optimization)
        assert ordered_scripts[3] == "eval_agent.py", (
            f"Fourth subprocess call must be eval_agent.py, got {ordered_scripts[3]}"
        )

        # Fifth call must be snapshot_agent.py (deploy snapshot)
        assert ordered_scripts[4] == "snapshot_agent.py", (
            f"Fifth subprocess call must be snapshot_agent.py, got {ordered_scripts[4]}"
        )

    def test_pre_snapshot_carries_score_flag(self, tmp_path: Path) -> None:
        """The initial snapshot call (step 2) must pass --score with the score_before value."""
        agent_name = "karen"
        snapshot_dir = tmp_path / "agent_snapshots"
        eval_json = snapshot_dir / agent_name / "eval_latest.json"

        score_before = 0.84
        score_after = 0.90
        call_count = 0
        snapshot_calls: list[list[str]] = []

        def _fake_subprocess(cmd, **kwargs):
            nonlocal call_count
            cmd_str_list = [str(c) for c in cmd]
            if "eval_agent.py" in " ".join(cmd_str_list):
                call_count += 1
                score = score_before if call_count == 1 else score_after
                _write_eval_json(eval_json, agent_name, score)
            if "snapshot_agent.py" in " ".join(cmd_str_list):
                snapshot_calls.append(cmd_str_list)
            return _ok_process()

        with patch("subprocess.run", side_effect=_fake_subprocess):
            run_optimize_and_prove(
                agent_name=agent_name,
                base_dir=tmp_path,
                min_delta=0.01,
                min_score=0.70,
            )

        assert len(snapshot_calls) >= 1, "Expected at least one snapshot_agent.py call"
        first_snapshot = snapshot_calls[0]
        assert "--score" in first_snapshot, (
            f"First snapshot call must include --score flag, got: {first_snapshot}"
        )
