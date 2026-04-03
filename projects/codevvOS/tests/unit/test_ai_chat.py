"""Unit tests for POST /api/ai/chat SSE endpoint."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient


def _make_jwt(user_id: str = "test-user", tenant_id: str = "test-tenant") -> str:
    from shared.auth import create_jwt  # noqa: PLC0415

    return create_jwt(user_id=user_id, tenant_id=tenant_id, role="member")


@pytest.fixture(autouse=True)
def reset_ai_rate_limiter():
    """Reset AI rate limiter storage before and after each test."""
    from backend.app.api.ai import limiter  # noqa: PLC0415

    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.fixture()
def ollama_env(monkeypatch):
    """Set OLLAMA_BASE_URL for tests that need it."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434/api")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")


def _mock_ollama_stream(chunks: list[dict]):
    """Build a mock async context manager for httpx.AsyncClient.stream."""

    class _FakeResponse:
        async def aiter_lines(self):
            for chunk in chunks:
                yield json.dumps(chunk)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class _FakeClient:
        def stream(self, method, url, **kwargs):
            return _FakeResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    return _FakeClient()


# ---------------------------------------------------------------------------
# Test 1: no JWT → 401
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_without_jwt_returns_401():
    """POST /api/ai/chat without Authorization header returns 401."""
    from backend.app.main import app  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/ai/chat", json={"message": "hello"})

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test 2: missing message field → 422
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_missing_message_returns_422():
    """POST /api/ai/chat with empty body returns 422 (Pydantic validation)."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/ai/chat",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Test 3: OLLAMA_BASE_URL not set → 503
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_no_ollama_url_returns_503(monkeypatch):
    """POST /api/ai/chat with OLLAMA_BASE_URL unset returns 503."""
    from backend.app.main import app  # noqa: PLC0415

    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/ai/chat",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "AI service not configured"


# ---------------------------------------------------------------------------
# Test 4: valid request + mock Ollama → SSE stream with token + [DONE]
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_valid_request_streams_sse(ollama_env):
    """POST /api/ai/chat streams SSE: data: {"token": "..."} then data: [DONE]."""
    from backend.app.main import app  # noqa: PLC0415

    chunks = [
        {"message": {"content": "Hello"}, "done": False},
        {"message": {"content": " world"}, "done": True},
    ]
    mock_client = _mock_ollama_stream(chunks)
    token = _make_jwt()

    with patch("backend.app.api.ai.httpx.AsyncClient", return_value=mock_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/ai/chat",
                json={"message": "hi"},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert 'data: {"token": "Hello"}' in body
    assert 'data: {"token": " world"}' in body
    assert "data: [DONE]" in body


# ---------------------------------------------------------------------------
# Test 5: Ollama unreachable → SSE error + [DONE]
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_ollama_unreachable_streams_error(ollama_env):
    """POST /api/ai/chat with ConnectError streams error then [DONE]."""
    from backend.app.main import app  # noqa: PLC0415

    class _FailingClient:
        def stream(self, method, url, **kwargs):
            raise httpx.ConnectError("refused")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    token = _make_jwt()
    with patch("backend.app.api.ai.httpx.AsyncClient", return_value=_FailingClient()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/ai/chat",
                json={"message": "hi"},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    body = response.text
    assert 'data: {"error": "AI service unavailable"}' in body
    assert "data: [DONE]" in body


# ---------------------------------------------------------------------------
# Test 6: history is forwarded to Ollama
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_history_forwarded_to_ollama(ollama_env):
    """POST /api/ai/chat passes history + new message to Ollama in order."""
    from backend.app.main import app  # noqa: PLC0415

    captured_payload: dict = {}

    class _CapturingResponse:
        async def aiter_lines(self):
            yield json.dumps({"message": {"content": "ok"}, "done": True})

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class _CapturingClient:
        def stream(self, method, url, json=None, **kwargs):
            nonlocal captured_payload
            captured_payload = json or {}
            return _CapturingResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    token = _make_jwt()
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply"},
    ]

    with patch("backend.app.api.ai.httpx.AsyncClient", return_value=_CapturingClient()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/ai/chat",
                json={"message": "second", "history": history},
                headers={"Authorization": f"Bearer {token}"},
            )

    messages = captured_payload.get("messages", [])
    assert len(messages) == 3
    assert messages[0] == {"role": "user", "content": "first"}
    assert messages[1] == {"role": "assistant", "content": "reply"}
    assert messages[2] == {"role": "user", "content": "second"}


# ---------------------------------------------------------------------------
# Test 7: rate limit — 31st request returns 429
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_chat_rate_limit_31st_request_returns_429(ollama_env):
    """POST /api/ai/chat: 31st request from same user returns 429."""
    from backend.app.main import app  # noqa: PLC0415

    chunks = [{"message": {"content": "x"}, "done": True}]
    token = _make_jwt()

    # Each request needs a fresh mock client instance
    with patch(
        "backend.app.api.ai.httpx.AsyncClient",
        side_effect=lambda: _mock_ollama_stream(chunks),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            statuses = []
            for _ in range(31):
                r = await client.post(
                    "/api/ai/chat",
                    json={"message": "hi"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                statuses.append(r.status_code)

    assert statuses[:30] == [200] * 30
    assert statuses[30] == 429
