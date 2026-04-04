"""Unit tests for Claude AI auth migration — no OAuth PKCE, JWT-gated key management."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from shared.auth import create_jwt


def _auth_header(user_id: str = "u1", role: str = "member") -> dict[str, str]:
    token = create_jwt(user_id=user_id, tenant_id="t1", role=role)
    return {"Authorization": f"Bearer {token}"}


def test_no_oauth_pkce_file():
    """No claude_auth.py with OAuth PKCE logic exists."""
    import importlib.util
    import os

    # Check that claude_auth module doesn't exist with authorize/token_exchange
    spec = importlib.util.find_spec("backend.app.api.claude_auth")
    if spec is None:
        return  # No such module — test passes

    # If it somehow exists, ensure it has no PKCE-related functions
    module = importlib.import_module("backend.app.api.claude_auth")
    assert not hasattr(module, "authorize"), "claude_auth.py should not have OAuth authorize"
    assert not hasattr(module, "token_exchange"), "claude_auth.py should not have token_exchange"


@pytest.mark.anyio
async def test_get_ai_config_requires_jwt():
    """GET /api/ai/config returns 403/401 without auth token."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/ai/config")

    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_get_ai_config_returns_has_personal_key_false():
    """GET /api/ai/config returns {"has_personal_key": false} with valid JWT (no key stored)."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/ai/config", headers=_auth_header(user_id="newuser"))

    assert response.status_code == 200
    body = response.json()
    assert body["has_personal_key"] is False


@pytest.mark.anyio
async def test_put_claude_key_returns_200():
    """PUT /api/settings/claude-key with valid api_key returns 200."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/settings/claude-key",
            json={"api_key": "sk-ant-test"},
            headers=_auth_header(user_id="u_put"),
        )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_ai_config_returns_has_personal_key_true_after_put():
    """After PUT /api/settings/claude-key, GET /api/ai/config returns {"has_personal_key": true}."""
    from backend.app.main import app

    headers = _auth_header(user_id="u_flow")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        put_resp = await client.put(
            "/api/settings/claude-key",
            json={"api_key": "sk-ant-test"},
            headers=headers,
        )
        assert put_resp.status_code == 200

        config_resp = await client.get("/api/ai/config", headers=headers)

    assert config_resp.status_code == 200
    assert config_resp.json()["has_personal_key"] is True


@pytest.mark.anyio
async def test_delete_claude_key_returns_200():
    """DELETE /api/settings/claude-key returns 200."""
    from backend.app.main import app

    headers = _auth_header(user_id="u_del")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.put(
            "/api/settings/claude-key",
            json={"api_key": "sk-ant-test"},
            headers=headers,
        )
        response = await client.delete("/api/settings/claude-key", headers=headers)

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_ai_config_returns_has_personal_key_false_after_delete():
    """After DELETE /api/settings/claude-key, GET /api/ai/config returns {"has_personal_key": false}."""
    from backend.app.main import app

    headers = _auth_header(user_id="u_delflow")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.put(
            "/api/settings/claude-key",
            json={"api_key": "sk-ant-test"},
            headers=headers,
        )
        del_resp = await client.delete("/api/settings/claude-key", headers=headers)
        assert del_resp.status_code == 200

        config_resp = await client.get("/api/ai/config", headers=headers)

    assert config_resp.status_code == 200
    assert config_resp.json()["has_personal_key"] is False
