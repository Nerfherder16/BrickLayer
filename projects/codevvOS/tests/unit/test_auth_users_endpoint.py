"""Unit tests for GET /api/auth/users endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    from backend.app.api.auth import limiter  # noqa: PLC0415

    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.mark.anyio
async def test_list_users_returns_users_with_computed_initials():
    """GET /api/auth/users returns id, display_name, avatar_initials — no passwords."""
    from backend.app.main import app

    mock_users = [
        {"id": "user-1", "display_name": "Tim Green"},
        {"id": "user-2", "display_name": "Alice"},
    ]

    with patch(
        "backend.app.api.auth._get_all_users",
        new=AsyncMock(return_value=mock_users),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/auth/users")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    tim = next(u for u in body if u["display_name"] == "Tim Green")
    assert tim["id"] == "user-1"
    assert tim["avatar_initials"] == "TG"
    assert "password" not in tim
    assert "password_hash" not in tim

    alice = next(u for u in body if u["display_name"] == "Alice")
    assert alice["avatar_initials"] == "A"
    assert "password" not in alice


@pytest.mark.anyio
async def test_list_users_returns_empty_list_when_no_users():
    """GET /api/auth/users with empty DB returns []."""
    from backend.app.main import app

    with patch(
        "backend.app.api.auth._get_all_users",
        new=AsyncMock(return_value=[]),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/auth/users")

    assert response.status_code == 200
    assert response.json() == []
