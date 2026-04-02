"""Unit tests for POST /auth/login and POST /auth/logout endpoints."""
from __future__ import annotations

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter storage before each test to prevent bleed-over."""
    from backend.app.api.auth import limiter  # noqa: PLC0415

    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.mark.anyio
async def test_login_wrong_password_returns_401():
    """POST /auth/login with wrong password returns 401."""
    from backend.app.main import app

    with patch(
        "backend.app.api.auth._get_user_by_email",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={"email": "user@example.com", "password": "wrongpassword"},
            )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_valid_credentials_returns_200_with_jwt():
    """POST /auth/login with valid credentials returns 200 and a JWT."""
    from backend.app.main import app

    password = "correct-password"  # noqa: S105
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    mock_user = {
        "id": "user-uuid",
        "tenant_id": "tenant-uuid",
        "password_hash": password_hash,
        "role": "member",
    }

    with patch(
        "backend.app.api.auth._get_user_by_email",
        new=AsyncMock(return_value=mock_user),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={"email": "user@example.com", "password": password},
            )

    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert "user" in body
    assert body["user"]["role"] == "member"


@pytest.mark.anyio
async def test_login_rate_limit_returns_429_on_11th_attempt():
    """11 rapid failed login attempts returns 429 on the 11th request."""
    from backend.app.main import app

    with patch(
        "backend.app.api.auth._get_user_by_email",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            statuses = []
            for _ in range(11):
                r = await client.post(
                    "/auth/login",
                    json={"email": "ratelimit@example.com", "password": "wrong"},
                )
                statuses.append(r.status_code)

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


@pytest.mark.anyio
async def test_logout_returns_200():
    """POST /auth/logout with a Bearer token returns 200."""
    from backend.app.main import app
    from shared.auth import create_jwt

    token = create_jwt(user_id="u1", tenant_id="t1", role="member")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "logged out"}
