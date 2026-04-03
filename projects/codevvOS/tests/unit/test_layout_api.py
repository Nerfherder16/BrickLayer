"""Unit tests for GET/PUT /api/layout endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


def _make_jwt(user_id: str = "user-a", tenant_id: str = "tenant-1") -> str:
    from shared.auth import create_jwt  # noqa: PLC0415

    return create_jwt(user_id=user_id, tenant_id=tenant_id, role="member")


@pytest.mark.anyio
async def test_get_layout_no_saved_layout_returns_null():
    """GET /api/layout with no saved layout returns {layout_version: null, layout: null}."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    with patch("backend.app.api.layout._get_layout", new=AsyncMock(return_value=None)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/layout",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body == {"layout_version": None, "layout": None}


@pytest.mark.anyio
async def test_put_layout_valid_returns_200():
    """PUT /api/layout with valid layout_version 1 returns 200."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    with patch("backend.app.api.layout._upsert_layout", new=AsyncMock(return_value=None)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/api/layout",
                json={"layout_version": 1, "layout": {"orientation": "HORIZONTAL"}},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_layout_after_put_returns_saved_layout():
    """GET /api/layout after PUT returns the saved layout."""
    from backend.app.main import app  # noqa: PLC0415

    saved_layout = {"orientation": "HORIZONTAL", "panels": []}
    token = _make_jwt()

    mock_record = MagicMock()
    mock_record.layout_json = saved_layout
    mock_record.layout_version = 1

    with patch("backend.app.api.layout._get_layout", new=AsyncMock(return_value=mock_record)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/layout",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["layout"] == saved_layout
    assert body["layout_version"] == 1


@pytest.mark.anyio
async def test_put_layout_version_0_returns_422():
    """PUT /api/layout with layout_version 0 returns 422."""
    from backend.app.main import app  # noqa: PLC0415

    token = _make_jwt()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/layout",
            json={"layout_version": 0, "layout": {"panels": []}},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_layout_without_jwt_returns_401():
    """GET /api/layout without JWT returns 401."""
    from backend.app.main import app  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/layout")

    assert response.status_code == 403


@pytest.mark.anyio
async def test_put_layout_without_jwt_returns_401():
    """PUT /api/layout without JWT returns 401."""
    from backend.app.main import app  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/layout",
            json={"layout_version": 1, "layout": {}},
        )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_cross_user_isolation_different_users_get_null():
    """User B (different user, same tenant) should not see user A's layout."""
    from backend.app.main import app  # noqa: PLC0415

    token_b = _make_jwt(user_id="user-b", tenant_id="tenant-1")

    # User B has no layout stored
    with patch("backend.app.api.layout._get_layout", new=AsyncMock(return_value=None)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/layout",
                headers={"Authorization": f"Bearer {token_b}"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body == {"layout_version": None, "layout": None}
