"""Tests for bl/runners/scout.py — Scout agent runner."""

from unittest.mock import MagicMock, patch

from bl.runners.scout import run_scout_for_project


class TestRunScoutTmuxIntegration:
    @patch("bl.runners.scout.wait_for_agent")
    @patch("bl.runners.scout.spawn_agent")
    @patch("bl.runners.scout.cfg")
    def test_scout_calls_spawn_agent(self, mock_cfg, mock_spawn, mock_wait):
        scout_md = MagicMock()
        scout_md.exists.return_value = True
        scout_md.read_text.return_value = "Scout instructions"
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=scout_md)

        project_root = MagicMock()
        cfg_path = MagicMock()
        cfg_path.exists.return_value = False
        project_root.__truediv__ = MagicMock(return_value=cfg_path)
        mock_cfg.project_root = project_root
        mock_cfg.recall_src = MagicMock()

        mock_spawn.return_value = MagicMock()
        mock_wait.return_value = MagicMock(
            exit_code=0,
            stdout="# BrickLayer Campaign Questions\n## Q1\nQuestion text",
        )
        mock_cfg.questions_md = MagicMock()

        run_scout_for_project()

        mock_spawn.assert_called_once()
        call_kwargs = mock_spawn.call_args
        assert call_kwargs.kwargs.get("dangerously_skip_permissions") is True
        assert call_kwargs.kwargs.get("output_format") is None
        mock_wait.assert_called_once()

    @patch("bl.runners.scout.spawn_agent")
    @patch("bl.runners.scout.cfg")
    def test_scout_missing_md(self, mock_cfg, mock_spawn):
        scout_md = MagicMock()
        scout_md.exists.return_value = False
        mock_cfg.agents_dir = MagicMock()
        mock_cfg.agents_dir.__truediv__ = MagicMock(return_value=scout_md)

        run_scout_for_project()
        mock_spawn.assert_not_called()
