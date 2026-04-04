"""Tests for bl.tmux.wave — batch spawn and collect."""

from unittest.mock import MagicMock, patch


class TestSpawnWave:
    @patch("bl.tmux.wave.spawn_agent")
    @patch("bl.tmux.wave.in_tmux", return_value=False)
    def test_returns_all_spawns(self, mock_tmux, mock_spawn):
        mock_spawn.return_value = MagicMock()
        from bl.tmux.wave import spawn_wave

        agents = [
            {"agent_name": "a1", "prompt": "p1"},
            {"agent_name": "a2", "prompt": "p2"},
        ]
        result = spawn_wave(agents)
        assert len(result) == 2
        assert mock_spawn.call_count == 2

    @patch("bl.tmux.wave.subprocess.run")
    @patch("bl.tmux.wave.spawn_agent")
    @patch("bl.tmux.wave.in_tmux", return_value=True)
    def test_calls_tiled_layout_once(self, mock_tmux, mock_spawn, mock_run):
        mock_spawn.return_value = MagicMock()
        from bl.tmux.wave import spawn_wave

        agents = [{"agent_name": f"a{i}", "prompt": f"p{i}"} for i in range(3)]
        spawn_wave(agents)
        layout_calls = [c for c in mock_run.call_args_list if "tiled" in str(c)]
        assert len(layout_calls) == 1

    @patch("bl.tmux.wave.spawn_agent")
    @patch("bl.tmux.wave.in_tmux", return_value=False)
    def test_max_concurrency_limits_spawns(self, mock_tmux, mock_spawn):
        mock_spawn.return_value = MagicMock()
        from bl.tmux.wave import spawn_wave

        agents = [{"agent_name": f"a{i}", "prompt": f"p{i}"} for i in range(10)]
        result = spawn_wave(agents, max_concurrency=3)
        assert len(result) == 3


class TestCollectWave:
    @patch("bl.tmux.wave.wait_for_agent")
    def test_waits_for_all(self, mock_wait):
        mock_wait.return_value = MagicMock()
        from bl.tmux.wave import collect_wave

        spawns = [MagicMock(), MagicMock()]
        results = collect_wave(spawns, timeout=60)
        assert len(results) == 2
        assert mock_wait.call_count == 2
