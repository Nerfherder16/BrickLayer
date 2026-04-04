"""Unit tests for POST /api/ai/inline-edit endpoint."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client() -> TestClient:
    """Import app fresh so rate-limit state is isolated per test."""
    from backend.app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


def _stream_chunks(*chunks: str) -> AsyncIterator[str]:
    """Async generator that yields the provided text chunks."""

    async def _gen() -> AsyncIterator[str]:
        for chunk in chunks:
            yield chunk

    return _gen()


# ---------------------------------------------------------------------------
# 422 — missing required fields
# ---------------------------------------------------------------------------


def test_inline_edit_missing_fields_returns_422() -> None:
    client = _make_client()
    response = client.post("/api/ai/inline-edit", json={})
    assert response.status_code == 422


def test_inline_edit_missing_document_returns_422() -> None:
    client = _make_client()
    response = client.post(
        "/api/ai/inline-edit",
        json={"prompt": "fix it", "language": "python"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 413 — document too large (> 100 KB)
# ---------------------------------------------------------------------------


def test_inline_edit_document_over_100kb_returns_413() -> None:
    client = _make_client()
    big_doc = "x" * (100 * 1024 + 1)
    response = client.post(
        "/api/ai/inline-edit",
        json={"prompt": "refactor", "document": big_doc, "language": "python"},
        headers={"X-Session-Id": "test-413"},
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# 200 — valid request returns SSE stream
# ---------------------------------------------------------------------------


def test_inline_edit_valid_request_returns_event_stream() -> None:
    with patch(
        "backend.app.api.ai_edit.stream_inline_edit",
        return_value=_stream_chunks("hello ", "world"),
    ):
        client = _make_client()
        response = client.post(
            "/api/ai/inline-edit",
            json={"prompt": "improve", "document": "x = 1", "language": "python"},
            headers={"X-Session-Id": "test-200"},
        )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Final SSE event is `event: done`
# ---------------------------------------------------------------------------


def test_inline_edit_final_sse_event_is_done() -> None:
    with patch(
        "backend.app.api.ai_edit.stream_inline_edit",
        return_value=_stream_chunks("edited content"),
    ):
        client = _make_client()
        response = client.post(
            "/api/ai/inline-edit",
            json={"prompt": "fix", "document": "code", "language": "js"},
            headers={"X-Session-Id": "test-done"},
        )
    assert response.status_code == 200
    body = response.text
    assert "event: done" in body


# ---------------------------------------------------------------------------
# 429 — rate limit: 6th request in 60-second window
# ---------------------------------------------------------------------------


def test_inline_edit_sixth_request_returns_429() -> None:
    session_id = "test-ratelimit-unique-abc123"

    # Reset the rate-limit store before this test
    import backend.app.api.ai_edit as ai_edit_module  # noqa: PLC0415

    ai_edit_module._rate_store.pop(session_id, None)

    with patch(
        "backend.app.api.ai_edit.stream_inline_edit",
        return_value=_stream_chunks("ok"),
    ):
        client = _make_client()

        # First 5 requests should succeed
        for i in range(5):
            r = client.post(
                "/api/ai/inline-edit",
                json={"prompt": "x", "document": "y", "language": "py"},
                headers={"X-Session-Id": session_id},
            )
            assert r.status_code == 200, f"Request {i + 1} should succeed, got {r.status_code}"

        # 6th must be rejected
        r = client.post(
            "/api/ai/inline-edit",
            json={"prompt": "x", "document": "y", "language": "py"},
            headers={"X-Session-Id": session_id},
        )
    assert r.status_code == 429


# ---------------------------------------------------------------------------
# LLM service reads OLLAMA_BASE_URL env var
# ---------------------------------------------------------------------------


def test_llm_service_reads_ollama_base_url_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom-host:11434")
    import importlib  # noqa: PLC0415

    import backend.app.services.llm_service as svc  # noqa: PLC0415

    importlib.reload(svc)
    assert svc.OLLAMA_BASE_URL == "http://custom-host:11434"
