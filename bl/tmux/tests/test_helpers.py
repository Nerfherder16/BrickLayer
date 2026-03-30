"""Tests for bl.tmux.helpers — detection, model map, env, arg building."""

import json
from unittest.mock import patch


class TestInTmux:
    def test_returns_true_when_tmux_env_set(self, monkeypatch):
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")
        from bl.tmux.helpers import in_tmux

        assert in_tmux() is True

    @patch("bl.tmux.helpers._tmux_socket_active", return_value=False)
    def test_returns_false_when_no_env_and_no_socket(self, mock_socket, monkeypatch):
        monkeypatch.delenv("TMUX", raising=False)
        from bl.tmux.helpers import in_tmux

        assert in_tmux() is False

    @patch("bl.tmux.helpers._tmux_socket_active", return_value=False)
    def test_returns_false_when_tmux_env_empty(self, mock_socket, monkeypatch):
        monkeypatch.setenv("TMUX", "")
        from bl.tmux.helpers import in_tmux

        assert in_tmux() is False

    @patch("bl.tmux.helpers._tmux_socket_active", return_value=True)
    def test_returns_true_via_socket_fallback(self, mock_socket, monkeypatch):
        monkeypatch.delenv("TMUX", raising=False)
        from bl.tmux.helpers import in_tmux

        assert in_tmux() is True


class TestResolveModel:
    def test_maps_opus(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model("opus") == "claude-opus-4-6"

    def test_maps_sonnet(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model("sonnet") == "claude-sonnet-4-6"

    def test_maps_haiku(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model("haiku") == "claude-haiku-4-5-20251001"

    def test_passthrough_full_id(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model("claude-opus-4-6") == "claude-opus-4-6"

    def test_none_returns_none(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model(None) is None

    def test_empty_returns_none(self):
        from bl.tmux.helpers import resolve_model

        assert resolve_model("") is None


class TestBuildEnv:
    def test_excludes_claudecode(self, monkeypatch):
        monkeypatch.setenv("CLAUDECODE", "1")
        monkeypatch.setenv("HOME", "/home/test")
        from bl.tmux.helpers import build_env

        env = build_env()
        assert "CLAUDECODE" not in env
        assert env["HOME"] == "/home/test"

    def test_applies_overrides(self, monkeypatch):
        monkeypatch.delenv("CLAUDECODE", raising=False)
        from bl.tmux.helpers import build_env

        env = build_env({"MY_VAR": "hello"})
        assert env["MY_VAR"] == "hello"

    def test_empty_string_removes_key(self, monkeypatch):
        monkeypatch.setenv("REMOVE_ME", "value")
        from bl.tmux.helpers import build_env

        env = build_env({"REMOVE_ME": ""})
        assert "REMOVE_ME" not in env


class TestBuildClaudeArgs:
    def test_minimal_args(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args()
        assert args == ["-p", "-", "--output-format", "json"]

    def test_with_model(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(model="sonnet")
        assert "--model" in args
        assert "claude-sonnet-4-6" in args

    def test_with_allowed_tools(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(allowed_tools=["Read", "Write"])
        assert "--allowedTools" in args
        assert "Read,Write" in args

    def test_with_disallowed_tools(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(disallowed_tools=["Bash"])
        assert "--disallowedTools" in args
        assert "Bash" in args

    def test_dangerously_skip_permissions(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(dangerously_skip_permissions=True)
        assert "--dangerously-skip-permissions" in args

    def test_no_output_format_when_none(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(output_format=None)
        assert "--output-format" not in args

    def test_session_id_adds_resume(self):
        from bl.tmux.helpers import build_claude_args

        args = build_claude_args(session_id="abc123")
        assert "--resume" in args
        assert "abc123" in args


class TestExtractSessionId:
    def test_extracts_from_valid_json(self):
        from bl.tmux.helpers import extract_session_id

        raw = json.dumps({"session_id": "abc-123", "result": "ok"})
        assert extract_session_id(raw) == "abc-123"

    def test_returns_none_for_missing_key(self):
        from bl.tmux.helpers import extract_session_id

        assert extract_session_id('{"result": "ok"}') is None

    def test_returns_none_for_invalid_json(self):
        from bl.tmux.helpers import extract_session_id

        assert extract_session_id("not json") is None

    def test_returns_none_for_empty(self):
        from bl.tmux.helpers import extract_session_id

        assert extract_session_id("") is None
