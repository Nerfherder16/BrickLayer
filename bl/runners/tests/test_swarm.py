"""Tests for bl/runners/swarm.py — swarm meta-runner with wave dispatch."""

from unittest.mock import MagicMock, patch

from bl.runners.swarm import (
    _aggregate_any_failure,
    _aggregate_majority,
    _aggregate_worst,
    _verdict_rank,
    run_swarm,
)


# ---------------------------------------------------------------------------
# Unit tests: verdict ranking and aggregation
# ---------------------------------------------------------------------------


class TestVerdictRank:
    def test_failure_is_worst(self):
        assert _verdict_rank("FAILURE") == 0

    def test_healthy_is_best(self):
        assert _verdict_rank("HEALTHY") == 3

    def test_unknown_treated_as_inconclusive(self):
        assert _verdict_rank("BOGUS") == 2


class TestAggregateWorst:
    def test_empty_returns_inconclusive(self):
        assert _aggregate_worst([]) == "INCONCLUSIVE"

    def test_picks_worst_verdict(self):
        results = [{"verdict": "HEALTHY"}, {"verdict": "WARNING"}]
        assert _aggregate_worst(results) == "WARNING"

    def test_failure_beats_all(self):
        results = [
            {"verdict": "HEALTHY"},
            {"verdict": "FAILURE"},
            {"verdict": "WARNING"},
        ]
        assert _aggregate_worst(results) == "FAILURE"


class TestAggregateMajority:
    def test_empty_returns_inconclusive(self):
        assert _aggregate_majority([], {}) == "INCONCLUSIVE"

    def test_majority_wins(self):
        results = [
            {"id": "a", "verdict": "HEALTHY"},
            {"id": "b", "verdict": "HEALTHY"},
            {"id": "c", "verdict": "FAILURE"},
        ]
        assert _aggregate_majority(results, {}) == "HEALTHY"

    def test_weights_tip_balance(self):
        results = [
            {"id": "a", "verdict": "HEALTHY"},
            {"id": "b", "verdict": "FAILURE"},
        ]
        assert _aggregate_majority(results, {"b": 3}) == "FAILURE"


class TestAggregateAnyFailure:
    def test_no_failure_returns_worst(self):
        results = [{"verdict": "HEALTHY"}, {"verdict": "WARNING"}]
        assert _aggregate_any_failure(results) == "WARNING"

    def test_any_failure_returns_failure(self):
        results = [{"verdict": "HEALTHY"}, {"verdict": "FAILURE"}]
        assert _aggregate_any_failure(results) == "FAILURE"


# ---------------------------------------------------------------------------
# run_swarm: basic behavior
# ---------------------------------------------------------------------------


class TestRunSwarmBasic:
    def test_no_workers_returns_inconclusive(self):
        result = run_swarm({"spec": {"workers": []}})
        assert result["verdict"] == "INCONCLUSIVE"
        assert "no workers" in result["summary"]

    @patch("bl.runners.swarm._run_worker")
    def test_single_non_agent_worker(self, mock_worker):
        mock_worker.return_value = {
            "id": "bench",
            "mode": "benchmark",
            "verdict": "HEALTHY",
            "summary": "fast",
            "data": {},
            "details": "",
            "duration_ms": 100,
        }
        result = run_swarm(
            {
                "spec": {
                    "workers": [{"id": "bench", "mode": "benchmark", "spec": {}}],
                    "timeout_seconds": 30,
                }
            }
        )
        assert result["verdict"] == "HEALTHY"
        assert result["data"]["workers_total"] == 1


# ---------------------------------------------------------------------------
# Wave dispatch: agent-mode workers route through _dispatch_agent_wave
# ---------------------------------------------------------------------------


class TestSwarmWaveDispatch:
    @patch("bl.runners.swarm._dispatch_agent_wave")
    def test_agent_workers_use_wave(self, mock_dispatch):
        mock_dispatch.return_value = [
            {
                "id": "sec",
                "mode": "agent",
                "verdict": "HEALTHY",
                "summary": "secure",
                "data": {},
                "details": "",
                "duration_ms": 5000,
            }
        ]
        result = run_swarm(
            {
                "spec": {
                    "workers": [
                        {
                            "id": "sec",
                            "mode": "agent",
                            "spec": {"agent_name": "security"},
                        }
                    ],
                    "timeout_seconds": 60,
                }
            }
        )
        mock_dispatch.assert_called_once()
        assert result["verdict"] == "HEALTHY"
        assert result["data"]["by_worker"]["sec"]["verdict"] == "HEALTHY"

    @patch("bl.runners.swarm._dispatch_agent_wave")
    @patch("bl.runners.swarm._run_worker")
    def test_non_agent_workers_skip_wave(self, mock_worker, mock_dispatch):
        mock_worker.return_value = {
            "id": "bench",
            "mode": "benchmark",
            "verdict": "HEALTHY",
            "summary": "ok",
            "data": {},
            "details": "",
            "duration_ms": 50,
        }
        result = run_swarm(
            {
                "spec": {
                    "workers": [
                        {"id": "bench", "mode": "benchmark", "spec": {}}
                    ],
                }
            }
        )
        mock_dispatch.assert_not_called()
        assert result["verdict"] == "HEALTHY"

    @patch("bl.runners.swarm._dispatch_agent_wave")
    @patch("bl.runners.swarm._run_worker")
    def test_mixed_workers_routes_correctly(self, mock_worker, mock_dispatch):
        mock_dispatch.return_value = [
            {
                "id": "sec",
                "mode": "agent",
                "verdict": "HEALTHY",
                "summary": "secure",
                "data": {},
                "details": "",
                "duration_ms": 5000,
            }
        ]
        mock_worker.return_value = {
            "id": "bench",
            "mode": "benchmark",
            "verdict": "WARNING",
            "summary": "slow",
            "data": {},
            "details": "",
            "duration_ms": 200,
        }
        result = run_swarm(
            {
                "spec": {
                    "workers": [
                        {
                            "id": "sec",
                            "mode": "agent",
                            "spec": {"agent_name": "security"},
                        },
                        {"id": "bench", "mode": "benchmark", "spec": {}},
                    ],
                    "aggregation": "worst",
                }
            }
        )
        mock_dispatch.assert_called_once()
        mock_worker.assert_called_once()
        assert result["verdict"] == "WARNING"
        assert result["data"]["workers_total"] == 2

    @patch("bl.runners.swarm._dispatch_agent_wave")
    def test_multiple_agent_workers_all_wave(self, mock_dispatch):
        mock_dispatch.return_value = [
            {
                "id": "sec",
                "mode": "agent",
                "verdict": "HEALTHY",
                "summary": "ok",
                "data": {},
                "details": "",
                "duration_ms": 3000,
            },
            {
                "id": "types",
                "mode": "agent",
                "verdict": "WARNING",
                "summary": "issues",
                "data": {},
                "details": "",
                "duration_ms": 4000,
            },
        ]
        result = run_swarm(
            {
                "spec": {
                    "workers": [
                        {
                            "id": "sec",
                            "mode": "agent",
                            "spec": {"agent_name": "security"},
                        },
                        {
                            "id": "types",
                            "mode": "agent",
                            "spec": {"agent_name": "type-strictener"},
                        },
                    ],
                }
            }
        )
        mock_dispatch.assert_called_once()
        agents_arg = mock_dispatch.call_args[0][0]
        assert len(agents_arg) == 2
        assert result["verdict"] == "WARNING"


# ---------------------------------------------------------------------------
# _dispatch_agent_wave internals
# ---------------------------------------------------------------------------


class TestDispatchAgentWave:
    @patch("bl.runners.swarm.collect_wave")
    @patch("bl.runners.swarm.spawn_wave")
    @patch("bl.runners.swarm.parse_agent_raw")
    @patch("bl.runners.swarm.build_agent_prompt")
    def test_dispatches_via_spawn_wave(
        self, mock_build, mock_parse, mock_spawn, mock_collect
    ):
        from bl.runners.swarm import _dispatch_agent_wave

        mock_build.return_value = ("test prompt", "claude-opus-4-6")
        mock_spawn.return_value = [MagicMock()]
        mock_collect.return_value = [
            MagicMock(exit_code=0, stdout='{"verdict":"HEALTHY"}', duration_ms=2000)
        ]
        mock_parse.return_value = {
            "verdict": "HEALTHY",
            "summary": "ok",
            "data": {},
            "details": "",
        }

        workers = [
            {
                "id": "sec",
                "mode": "agent",
                "spec": {"agent_name": "security", "finding": "F1", "source": ""},
            }
        ]
        results = _dispatch_agent_wave(workers, 60)

        assert len(results) == 1
        assert results[0]["id"] == "sec"
        assert results[0]["verdict"] == "HEALTHY"
        assert results[0]["duration_ms"] == 2000
        mock_build.assert_called_once()
        mock_spawn.assert_called_once()
        mock_collect.assert_called_once()

    @patch("bl.runners.swarm.build_agent_prompt")
    def test_prompt_build_failure_returns_inconclusive(self, mock_build):
        from bl.runners.swarm import _dispatch_agent_wave

        mock_build.side_effect = ValueError("Agent file not found: bad.md")

        workers = [
            {
                "id": "bad",
                "mode": "agent",
                "spec": {"agent_name": "bad", "finding": "", "source": ""},
            }
        ]
        results = _dispatch_agent_wave(workers, 60)

        assert len(results) == 1
        assert results[0]["verdict"] == "INCONCLUSIVE"
        assert "not found" in results[0]["summary"]

    @patch("bl.runners.swarm.spawn_wave")
    @patch("bl.runners.swarm.build_agent_prompt")
    def test_cli_not_found_returns_inconclusive(self, mock_build, mock_spawn):
        from bl.runners.swarm import _dispatch_agent_wave

        mock_build.return_value = ("prompt", None)
        mock_spawn.side_effect = FileNotFoundError

        workers = [
            {
                "id": "sec",
                "mode": "agent",
                "spec": {"agent_name": "security", "finding": "", "source": ""},
            }
        ]
        results = _dispatch_agent_wave(workers, 60)

        assert len(results) == 1
        assert results[0]["verdict"] == "INCONCLUSIVE"
        assert "CLI not found" in results[0]["summary"]

    @patch("bl.runners.swarm.collect_wave")
    @patch("bl.runners.swarm.spawn_wave")
    @patch("bl.runners.swarm.build_agent_prompt")
    def test_timeout_returns_inconclusive(self, mock_build, mock_spawn, mock_collect):
        from bl.runners.swarm import _dispatch_agent_wave

        mock_build.return_value = ("prompt", None)
        mock_spawn.return_value = [MagicMock()]
        mock_collect.return_value = [
            MagicMock(exit_code=-1, stdout="", duration_ms=60000)
        ]

        workers = [
            {
                "id": "sec",
                "mode": "agent",
                "spec": {"agent_name": "security", "finding": "", "source": ""},
            }
        ]
        results = _dispatch_agent_wave(workers, 60)

        assert len(results) == 1
        assert results[0]["verdict"] == "INCONCLUSIVE"
        assert "timed out" in results[0]["summary"]
