"""Tests for bl.tmux.core — spawn_agent, wait_for_agent, dataclasses."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSpawnAgentSubprocess:
    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.subprocess.Popen")
    @patch("bl.tmux.core.in_tmux", return_value=False)
    @patch("bl.tmux.core.write_start_signal")
    def test_creates_popen(
        self,
        mock_signal,
        mock_tmux,
        mock_popen,
        mock_which,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn = spawn_agent("test-agent", "test prompt", cwd="/tmp")
        assert spawn.process is not None
        assert spawn.pane_id is None
        mock_popen.assert_called_once()

    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.subprocess.Popen")
    @patch("bl.tmux.core.in_tmux", return_value=False)
    @patch("bl.tmux.core.write_start_signal")
    def test_writes_prompt_to_file(
        self,
        mock_signal,
        mock_tmux,
        mock_popen,
        mock_which,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn = spawn_agent("test-agent", "hello world", cwd="/tmp")
        assert spawn.prompt_file.read_text() == "hello world"

    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.subprocess.Popen")
    @patch("bl.tmux.core.in_tmux", return_value=False)
    @patch("bl.tmux.core.write_start_signal")
    def test_passes_model_to_claude(
        self,
        mock_signal,
        mock_tmux,
        mock_popen,
        mock_which,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn_agent("test", "prompt", model="opus", cwd="/tmp")
        call_args = mock_popen.call_args[0][0]
        assert "--model" in call_args
        assert "claude-opus-4-6" in call_args

    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.subprocess.Popen")
    @patch("bl.tmux.core.in_tmux", return_value=False)
    @patch("bl.tmux.core.write_start_signal")
    def test_no_output_format_when_capture_false(
        self,
        mock_signal,
        mock_tmux,
        mock_popen,
        mock_which,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn_agent("test", "prompt", capture_output=False, cwd="/tmp")
        call_args = mock_popen.call_args[0][0]
        assert "--output-format" not in call_args


class TestSpawnAgentTmux:
    @patch("bl.tmux.core.spawn_tmux_pane", return_value="%5")
    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.in_tmux", return_value=True)
    @patch("bl.tmux.core.write_start_signal")
    def test_uses_tmux_pane(
        self,
        mock_signal,
        mock_tmux,
        mock_which,
        mock_pane,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn = spawn_agent("test-agent", "prompt", cwd="/tmp")
        assert spawn.pane_id == "%5"
        assert spawn.process is None
        mock_pane.assert_called_once()


    @patch("bl.tmux.core.spawn_tmux_pane", return_value="%5")
    @patch("bl.tmux.core.shutil.which", return_value="/usr/bin/claude")
    @patch("bl.tmux.core.in_tmux", return_value=True)
    @patch("bl.tmux.core.write_start_signal")
    def test_tmux_pane_uses_stream_json(
        self,
        mock_signal,
        mock_tmux,
        mock_which,
        mock_pane,
        tmp_path,
        monkeypatch,
    ):
        """Tmux panes should use stream-json for real-time formatted output."""
        monkeypatch.setattr("bl.tmux.core.TEMP_DIR", tmp_path)
        from bl.tmux.core import spawn_agent

        spawn_agent("test-agent", "prompt", output_format="json", cwd="/tmp")
        pane_call = mock_pane.call_args
        claude_args = pane_call.kwargs["claude_args"]
        idx = claude_args.index("--output-format")
        assert claude_args[idx + 1] == "stream-json"


class TestWaitSubprocess:
    def test_collects_stdout_and_exit_code(self):
        from bl.tmux.core import SpawnResult, _wait_subprocess

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ('{"result": "ok"}', "")
        mock_proc.returncode = 0

        spawn = SpawnResult(
            agent_id="abc",
            agent_name="test",
            pane_id=None,
            result_file=Path("/tmp/bl-result-abc.json"),
            exit_file=Path("/tmp/bl-exit-abc.txt"),
            prompt_file=Path("/tmp/bl-prompt-abc.txt"),
            process=mock_proc,
        )
        with patch("bl.tmux.core.write_stop_signal"):
            result = _wait_subprocess(spawn, timeout=600)

        assert result.exit_code == 0
        assert result.stdout == '{"result": "ok"}'
        assert result.agent_name == "test"

    def test_handles_timeout(self):
        from bl.tmux.core import SpawnResult, _wait_subprocess

        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = [
            subprocess.TimeoutExpired("claude", 600),
            ("", ""),
        ]

        spawn = SpawnResult(
            agent_id="abc",
            agent_name="test",
            pane_id=None,
            result_file=Path("/tmp/r"),
            exit_file=Path("/tmp/e"),
            prompt_file=Path("/tmp/p"),
            process=mock_proc,
        )
        with patch("bl.tmux.core.write_stop_signal"):
            result = _wait_subprocess(spawn, timeout=1)

        assert result.exit_code == -1
        mock_proc.kill.assert_called_once()

    def test_extracts_session_id(self):
        from bl.tmux.core import SpawnResult, _wait_subprocess

        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ('{"session_id": "s-123"}', "")
        mock_proc.returncode = 0

        spawn = SpawnResult(
            agent_id="abc",
            agent_name="test",
            pane_id=None,
            result_file=Path("/tmp/r"),
            exit_file=Path("/tmp/e"),
            prompt_file=Path("/tmp/p"),
            process=mock_proc,
        )
        with patch("bl.tmux.core.write_stop_signal"):
            result = _wait_subprocess(spawn, timeout=600)

        assert result.session_id == "s-123"


class TestWaitTmux:
    @patch("bl.tmux.core.tmux_wait_with_timeout", return_value=True)
    @patch("bl.tmux.core.write_stop_signal")
    def test_reads_result_files(self, mock_signal, mock_wait, tmp_path):
        result_file = tmp_path / "result.json"
        exit_file = tmp_path / "exit.txt"
        result_file.write_text('{"session_id": "s-1"}')
        exit_file.write_text("0\n")

        from bl.tmux.core import SpawnResult, _wait_tmux

        spawn = SpawnResult(
            agent_id="abc",
            agent_name="test",
            pane_id="%5",
            result_file=result_file,
            exit_file=exit_file,
            prompt_file=tmp_path / "prompt.txt",
        )
        result = _wait_tmux(spawn, timeout=600)

        assert result.exit_code == 0
        assert result.session_id == "s-1"

    @patch("bl.tmux.core.tmux_wait_with_timeout", return_value=False)
    @patch("bl.tmux.core.write_stop_signal")
    def test_returns_negative_on_timeout(self, mock_signal, mock_wait):
        from bl.tmux.core import SpawnResult, _wait_tmux

        spawn = SpawnResult(
            agent_id="abc",
            agent_name="test",
            pane_id="%5",
            result_file=Path("/tmp/nonexistent"),
            exit_file=Path("/tmp/nonexistent"),
            prompt_file=Path("/tmp/nonexistent"),
        )
        result = _wait_tmux(spawn, timeout=1)

        assert result.exit_code == -1
        assert result.stdout == ""
