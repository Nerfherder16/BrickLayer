"""Tests for bl.tmux.signals — hook lifecycle signal files."""

import json


class TestStartSignal:
    def test_schema_with_pane(self, tmp_path, monkeypatch):
        monkeypatch.setattr("bl.tmux.signals.SIGNAL_DIR", tmp_path)
        from bl.tmux.signals import write_start_signal

        write_start_signal("a1b2", "research-analyst", "/home/test", "sonnet", "%5")
        signal = json.loads((tmp_path / "bl-agent-start-a1b2.json").read_text())

        assert signal["agent_id"] == "a1b2"
        assert signal["agent_name"] == "research-analyst"
        assert signal["model"] == "claude-sonnet-4-6"
        assert signal["cwd"] == "/home/test"
        assert signal["pane_id"] == "%5"
        assert signal["tmux"] is True
        assert "timestamp" in signal

    def test_schema_without_pane(self, tmp_path, monkeypatch):
        monkeypatch.setattr("bl.tmux.signals.SIGNAL_DIR", tmp_path)
        from bl.tmux.signals import write_start_signal

        write_start_signal("x1y2", "scout", "/tmp", None, None)
        signal = json.loads((tmp_path / "bl-agent-start-x1y2.json").read_text())
        assert signal["tmux"] is False
        assert signal["pane_id"] is None


class TestStopSignal:
    def test_schema(self, tmp_path, monkeypatch):
        monkeypatch.setattr("bl.tmux.signals.SIGNAL_DIR", tmp_path)
        from bl.tmux.core import AgentResult
        from bl.tmux.signals import write_stop_signal

        result = AgentResult(
            agent_id="a1b2",
            agent_name="research-analyst",
            exit_code=0,
            stdout="",
            session_id="sess-1",
            duration_ms=5000,
        )
        write_stop_signal("a1b2", "research-analyst", result)
        signal = json.loads((tmp_path / "bl-agent-stop-a1b2.json").read_text())

        assert signal["agent_id"] == "a1b2"
        assert signal["exit_code"] == 0
        assert signal["duration_ms"] == 5000
        assert signal["session_id"] == "sess-1"
