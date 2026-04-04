"""Tests for backend.app.core.bricklayer_client."""
from __future__ import annotations

import asyncio
import importlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Run a coroutine synchronously inside a test."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Exports test
# ---------------------------------------------------------------------------

class TestModuleExports:
    def test_module_exports_spawn_agent(self):
        mod = importlib.import_module("backend.app.core.bricklayer_client")
        assert hasattr(mod, "spawn_agent"), "bricklayer_client must export spawn_agent"

    def test_module_exports_get_agent_status(self):
        mod = importlib.import_module("backend.app.core.bricklayer_client")
        assert hasattr(mod, "get_agent_status"), "bricklayer_client must export get_agent_status"

    def test_module_exports_stream_agent(self):
        mod = importlib.import_module("backend.app.core.bricklayer_client")
        assert hasattr(mod, "stream_agent"), "bricklayer_client must export stream_agent"


# ---------------------------------------------------------------------------
# spawn_agent tests
# ---------------------------------------------------------------------------

class TestSpawnAgent:
    def _make_response(self, payload: dict, status_code: int = 200):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_spawn_agent_sends_post_to_correct_url(self):
        """spawn_agent must POST to http://bricklayer:8300/agent/spawn."""
        from backend.app.core.bricklayer_client import spawn_agent

        mock_resp = self._make_response({"agent_id": "abc123"})

        captured_url = []
        captured_payload = []
        captured_headers = []

        async def fake_post(url, *, json=None, headers=None, **kwargs):
            captured_url.append(url)
            captured_payload.append(json)
            captured_headers.append(headers)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = fake_post

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            result = run(spawn_agent("rough-in", "do stuff", cwd="/tmp"))

        assert captured_url[0] == "http://bricklayer:8300/agent/spawn"
        assert result == {"agent_id": "abc123"}

    def test_spawn_agent_sends_bl_internal_secret_header(self):
        """spawn_agent must include X-BL-Internal-Secret header."""
        from backend.app.core.bricklayer_client import spawn_agent

        mock_resp = self._make_response({"agent_id": "abc123"})
        captured_headers = []

        async def fake_post(url, *, json=None, headers=None, **kwargs):
            captured_headers.append(headers)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = fake_post

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            with patch.dict("os.environ", {"BL_INTERNAL_SECRET": "test-secret"}):
                run(spawn_agent("rough-in", "do stuff"))

        assert "X-BL-Internal-Secret" in captured_headers[0]
        assert captured_headers[0]["X-BL-Internal-Secret"] == "test-secret"

    def test_spawn_agent_sends_correct_json_payload(self):
        """spawn_agent must send name, prompt, cwd in POST body."""
        from backend.app.core.bricklayer_client import spawn_agent

        mock_resp = self._make_response({"agent_id": "abc123"})
        captured_payload = []

        async def fake_post(url, *, json=None, headers=None, **kwargs):
            captured_payload.append(json)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = fake_post

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            run(spawn_agent("rough-in", "build something", cwd="/project"))

        assert captured_payload[0] == {
            "name": "rough-in",
            "prompt": "build something",
            "cwd": "/project",
        }

    def test_spawn_agent_returns_error_dict_on_connect_refused(self):
        """spawn_agent must return error dict (not raise) when connection refused."""
        import httpx
        from backend.app.core.bricklayer_client import spawn_agent

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            result = run(spawn_agent("rough-in", "do stuff"))

        assert isinstance(result, dict)
        assert result.get("error") == "bricklayer_unavailable"
        assert "detail" in result

    def test_spawn_agent_does_not_raise_on_connect_error(self):
        """spawn_agent must never raise — always return a dict."""
        import httpx
        from backend.app.core.bricklayer_client import spawn_agent

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("ECONNREFUSED")
        )

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            try:
                result = run(spawn_agent("rough-in", "do stuff"))
            except Exception as exc:
                pytest.fail(f"spawn_agent raised unexpectedly: {exc}")

        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# get_agent_status tests
# ---------------------------------------------------------------------------

class TestGetAgentStatus:
    def test_get_agent_status_sends_get_to_correct_url(self):
        """get_agent_status must GET http://bricklayer:8300/agent/<id>/status."""
        from backend.app.core.bricklayer_client import get_agent_status

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "running"}
        mock_resp.raise_for_status = MagicMock()

        captured_url = []

        async def fake_get(url, *, headers=None, **kwargs):
            captured_url.append(url)
            return mock_resp

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = fake_get

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            result = run(get_agent_status("agent-xyz"))

        assert captured_url[0] == "http://bricklayer:8300/agent/agent-xyz/status"
        assert result == {"status": "running"}

    def test_get_agent_status_returns_error_dict_on_connect_error(self):
        """get_agent_status must return error dict when bricklayer is unreachable."""
        import httpx
        from backend.app.core.bricklayer_client import get_agent_status

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("backend.app.core.bricklayer_client.httpx.AsyncClient", return_value=mock_client):
            result = run(get_agent_status("agent-xyz"))

        assert result.get("error") == "bricklayer_unavailable"
