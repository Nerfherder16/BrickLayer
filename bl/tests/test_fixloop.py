"""Tests for bl.fixloop — tmux dispatch integration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from bl.fixloop import _spawn_fix_agent, run_fix_loop


class TestSpawnFixAgentTmuxIntegration:
    """Verify _spawn_fix_agent dispatches through bl.tmux."""

    @patch("bl.fixloop.wait_for_agent")
    @patch("bl.fixloop.spawn_agent")
    @patch("bl.fixloop.cfg")
    def test_calls_spawn_agent(self, mock_cfg, mock_spawn, mock_wait):
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "Fix agent instructions"
        mock_cfg.autosearch_root = MagicMock()
        mock_cfg.autosearch_root.__truediv__ = MagicMock(return_value=MagicMock())
        # Chain: cfg.autosearch_root / "agents" / "fix-agent.md"
        agents_dir = MagicMock()
        agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.autosearch_root.__truediv__ = MagicMock(return_value=agents_dir)

        mock_spawn.return_value = MagicMock()
        mock_wait.return_value = MagicMock(exit_code=0)

        question = {
            "id": "Q1",
            "title": "Test",
            "mode": "fix",
            "test": "",
            "target": "",
        }
        result_dict = {"summary": "failed", "details": "stuff", "failure_type": "bug"}
        finding_path = MagicMock(spec=Path)
        finding_path.read_text.return_value = "Finding content"

        success = _spawn_fix_agent(question, result_dict, finding_path)

        assert success is True
        mock_spawn.assert_called_once()
        call_kwargs = mock_spawn.call_args.kwargs
        assert call_kwargs["agent_name"] == "fix-agent"
        assert call_kwargs["dangerously_skip_permissions"] is True
        assert call_kwargs["capture_output"] is False
        mock_wait.assert_called_once()

    @patch("bl.fixloop.wait_for_agent")
    @patch("bl.fixloop.spawn_agent")
    @patch("bl.fixloop.cfg")
    def test_nonzero_exit_returns_false(self, mock_cfg, mock_spawn, mock_wait):
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "Fix agent instructions"
        agents_dir = MagicMock()
        agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.autosearch_root = MagicMock()
        mock_cfg.autosearch_root.__truediv__ = MagicMock(return_value=agents_dir)

        mock_spawn.return_value = MagicMock()
        mock_wait.return_value = MagicMock(exit_code=1)

        question = {"id": "Q1", "title": "T", "mode": "fix"}
        finding_path = MagicMock(spec=Path)
        finding_path.read_text.return_value = "content"

        success = _spawn_fix_agent(question, {}, finding_path)
        assert success is False

    @patch("bl.fixloop.spawn_agent", side_effect=FileNotFoundError)
    @patch("bl.fixloop.cfg")
    def test_missing_claude_returns_false(self, mock_cfg, mock_spawn):
        agent_md = MagicMock()
        agent_md.exists.return_value = True
        agent_md.read_text.return_value = "Fix agent"
        agents_dir = MagicMock()
        agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.autosearch_root = MagicMock()
        mock_cfg.autosearch_root.__truediv__ = MagicMock(return_value=agents_dir)

        question = {"id": "Q1", "title": "T", "mode": "fix"}
        finding_path = MagicMock(spec=Path)
        finding_path.read_text.return_value = "content"

        success = _spawn_fix_agent(question, {}, finding_path)
        assert success is False

    @patch("bl.fixloop.cfg")
    def test_missing_agent_md_returns_false(self, mock_cfg):
        agent_md = MagicMock()
        agent_md.exists.return_value = False
        agents_dir = MagicMock()
        agents_dir.__truediv__ = MagicMock(return_value=agent_md)
        mock_cfg.autosearch_root = MagicMock()
        mock_cfg.autosearch_root.__truediv__ = MagicMock(return_value=agents_dir)

        question = {"id": "Q1", "title": "T", "mode": "fix"}
        finding_path = MagicMock(spec=Path)

        success = _spawn_fix_agent(question, {}, finding_path)
        assert success is False


class TestRunFixLoop:
    def test_non_failure_passthrough(self):
        result = run_fix_loop(
            {"id": "Q1"}, {"verdict": "HEALTHY"}, Path("/tmp/dummy"), max_attempts=2
        )
        assert result["verdict"] == "HEALTHY"
