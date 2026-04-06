"""Tests for masonry/mcp_server/js_engine.py — subprocess bridge to Node.js CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from masonry.mcp_server.js_engine import _call_js_engine, _CLI_DIR, _MASONRY_DIR, _REPO_ROOT


class TestCallJsEngine:
    def _run(self, returncode: int, stdout: str = "", stderr: str = ""):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = stderr
        return mock

    def test_success_returns_parsed_dict(self):
        payload = {"agent": "rough-in", "confidence": 1.0}
        with patch("subprocess.run", return_value=self._run(0, json.dumps(payload))):
            result = _call_js_engine("route.js", ["--prompt", "build something"])
        assert result == payload

    def test_nonzero_exit_returns_none(self):
        with patch("subprocess.run", return_value=self._run(1, '{"error":"oops"}', "bad")):
            result = _call_js_engine("route.js", [])
        assert result is None

    def test_timeout_returns_none(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("node", 10)):
            result = _call_js_engine("status.js", ["--project-dir", "."])
        assert result is None

    def test_file_not_found_returns_none(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("node not found")):
            result = _call_js_engine("registry-list.js", [])
        assert result is None

    def test_invalid_json_returns_none(self):
        with patch("subprocess.run", return_value=self._run(0, "not json at all")):
            result = _call_js_engine("healloop.js", [])
        assert result is None

    def test_unexpected_exception_returns_none(self):
        with patch("subprocess.run", side_effect=OSError("pipe broken")):
            result = _call_js_engine("route.js", [])
        assert result is None

    def test_passes_args_to_subprocess(self):
        payload = {"agents": []}
        with patch("subprocess.run", return_value=self._run(0, json.dumps(payload))) as mock_run:
            _call_js_engine("registry-list.js", ["--tier", "trusted"], timeout=15)
        call_args = mock_run.call_args[0][0]
        assert "registry-list.js" in call_args[-3]
        assert "--tier" in call_args
        assert "trusted" in call_args

    def test_timeout_parameter_forwarded(self):
        payload = {"ran": False}
        with patch("subprocess.run", return_value=self._run(0, json.dumps(payload))) as mock_run:
            _call_js_engine("healloop.js", [], timeout=300)
        assert mock_run.call_args[1]["timeout"] == 300


class TestPathConstants:
    def test_masonry_dir_exists(self):
        assert _MASONRY_DIR.is_dir()

    def test_repo_root_exists(self):
        assert _REPO_ROOT.is_dir()

    def test_cli_dir_path_correct(self):
        assert _CLI_DIR == _MASONRY_DIR / "src" / "engine" / "cli"
