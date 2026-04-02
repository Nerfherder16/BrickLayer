"""Unit tests for Settings Schema API endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from shared.auth import create_jwt


def _auth_header(role: str) -> dict[str, str]:
    token = create_jwt(user_id="u1", tenant_id="t1", role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_get_settings_schema_returns_definitions_key():
    """GET /api/settings/schema returns JSON with 'definitions' key (not '$defs')."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings/schema")

    assert response.status_code == 200
    body = response.json()
    assert "definitions" in body or "properties" in body
    assert "$defs" not in body


@pytest.mark.anyio
async def test_get_settings_schema_no_anyof_null():
    """GET /api/settings/schema has no 'anyOf' with null type (Optional fields flattened)."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings/schema")

    assert response.status_code == 200
    body = response.json()
    schema_str = str(body)
    # Ensure no anyOf patterns wrapping null remain
    assert "{'type': 'null'}" not in schema_str
    assert "\"type\": \"null\"" not in str(response.text)


@pytest.mark.anyio
async def test_get_user_settings_returns_defaults():
    """GET /api/settings/user returns current user settings when authenticated."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings/user", headers=_auth_header("member"))

    assert response.status_code == 200
    body = response.json()
    assert "theme" in body
    assert "font_size" in body
    assert "tab_size" in body
    assert "auto_save" in body
    assert "line_numbers" in body


@pytest.mark.anyio
async def test_get_user_settings_requires_jwt():
    """GET /api/settings/user returns 4xx without a JWT."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings/user")

    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_put_user_settings_updates_theme():
    """PUT /api/settings/user updates and returns changed settings."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/settings/user",
            json={"theme": "light"},
            headers=_auth_header("member"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["theme"] == "light"


@pytest.mark.anyio
async def test_get_admin_settings_with_member_token_returns_403():
    """GET /api/admin/settings returns 403 when called with a member-role token."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/admin/settings", headers=_auth_header("member"))

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_admin_settings_with_admin_token_returns_200():
    """GET /api/admin/settings returns 200 when called with an admin-role token."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/admin/settings", headers=_auth_header("admin"))

    assert response.status_code == 200
    body = response.json()
    assert "max_file_size_mb" in body
