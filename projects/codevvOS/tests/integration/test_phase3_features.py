"""
Phase 3 Graduation Integration Test — AI Chat, File Tree, and Layout

Tests the Phase 3 API surface using the FastAPI ASGI test client (no live server
required). Each test spins up the app in-process, making the suite runnable in
CI without a running Docker Compose stack.

Tests:
  a. POST /api/ai/chat without JWT → 401
  b. POST /api/ai/chat with empty body → 422
  c. POST /api/ai/chat with valid JWT, no OLLAMA_BASE_URL → 503
  d. GET /api/files/tree?path=/workspace with JWT → 200 (stubbed workspace)
  e. GET /api/files/tree?path=../../etc/passwd with JWT → 400 (path traversal)
  f. PUT /api/layout with TerminalPanel component key → 200
  g. GET /api/layout returns saved layout intact (round-trip)
"""
from __future__ import annotations

import json
import os

import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# JWT helper (mirrors tests/unit/test_ai_chat.py)
# ---------------------------------------------------------------------------


def _make_jwt(user_id: str = "test-user", tenant_id: str = "test-tenant") -> str:
    from shared.auth import create_jwt  # noqa: PLC0415

    return create_jwt(user_id=user_id, tenant_id=tenant_id, role="member")


# ---------------------------------------------------------------------------
# Rate-limiter reset fixture — prevents cross-test 429 bleed
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_ai_rate_limiter():
    from backend.app.api.ai import limiter  # noqa: PLC0415
    from backend.app.api.layout import _layout_store  # noqa: PLC0415

    limiter._storage.reset()
    _layout_store.clear()
    yield
    limiter._storage.reset()
    _layout_store.clear()


# ---------------------------------------------------------------------------
# AI Chat endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_without_jwt_returns_401():
    """POST /api/ai/chat without Authorization header returns 401."""
    from backend.app.main import app  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/ai/chat", json={"message": "hello"})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_ai_chat_with_empty_body_returns_422():
    """POST /api/ai/chat with no body (missing required `message`) returns 422."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/ai/chat",
            content=b"",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_ai_chat_without_ollama_configured_returns_503(monkeypatch):
    """POST /api/ai/chat with valid JWT but no OLLAMA_BASE_URL returns 503."""
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
    body = response.json()
    assert "not configured" in body.get("detail", "").lower()


# ---------------------------------------------------------------------------
# File tree endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_file_tree_with_valid_jwt_returns_200(tmp_path, monkeypatch):
    """GET /api/files/tree?path=<workspace> with JWT returns 200 and tree structure."""
    from backend.app.main import app  # noqa: PLC0415

    # Create a temporary workspace with a known structure
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "src").mkdir()
    (workspace / "app.py").write_text("# hello")

    monkeypatch.setenv("WORKSPACE_ROOT", str(workspace))
    # Patch the module-level constant so verify_path_in_workspace uses the temp dir
    monkeypatch.setattr("backend.app.api.files.WORKSPACE_ROOT", str(workspace))

    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/api/files/tree?path={workspace}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "dir"
    assert "children" in data
    child_names = {c["name"] for c in data["children"]}
    assert "src" in child_names
    assert "app.py" in child_names


@pytest.mark.anyio
async def test_file_tree_path_traversal_returns_400(tmp_path, monkeypatch):
    """GET /api/files/tree with ../../etc/passwd path returns 400 (traversal blocked)."""
    from backend.app.main import app  # noqa: PLC0415

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.setenv("WORKSPACE_ROOT", str(workspace))
    monkeypatch.setattr("backend.app.api.files.WORKSPACE_ROOT", str(workspace))

    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/files/tree?path=../../etc/passwd",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    body = response.json()
    assert "traversal" in body.get("detail", "").lower() or "workspace" in body.get("detail", "").lower()


# ---------------------------------------------------------------------------
# Layout persistence tests — TerminalPanel component key round-trip
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_layout_put_with_terminal_panel_returns_200():
    """PUT /api/layout with TerminalPanel component key returns 200."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    layout_payload = {
        "layout_version": 1,
        "layout": {
            "orientation": "HORIZONTAL",
            "panels": [{"id": "terminal", "component": "TerminalPanel"}],
        },
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/layout",
            json=layout_payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json().get("status") == "ok"


@pytest.mark.anyio
async def test_layout_round_trip_returns_saved_layout():
    """PUT then GET /api/layout returns the saved layout intact."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    saved_layout = {
        "orientation": "HORIZONTAL",
        "panels": [
            {"id": "terminal", "component": "TerminalPanel"},
            {"id": "ai-chat", "component": "AIChatPanel"},
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        put_resp = await client.put(
            "/api/layout",
            json={"layout_version": 1, "layout": saved_layout},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert put_resp.status_code == 200

        get_resp = await client.get(
            "/api/layout",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["layout_version"] == 1
    assert body["layout"] == saved_layout
