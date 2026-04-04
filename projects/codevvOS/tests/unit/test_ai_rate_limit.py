"""Unit tests for GET /api/ai/status with per-user rate limiting."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from shared.auth import create_jwt


@pytest.fixture(autouse=True)
def reset_ai_rate_limiter():
    """Reset in-memory rate limiter storage before each test to prevent bleed-over."""
    from backend.app.api.ai import limiter  # noqa: PLC0415

    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.mark.anyio
async def test_ai_status_returns_200_for_authenticated_user():
    """GET /api/ai/status returns 200 for a valid JWT."""
    from backend.app.main import app

    token = create_jwt(user_id="user-a", tenant_id="tenant-1", role="member")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/ai/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "available"}


@pytest.mark.anyio
async def test_ai_status_rate_limit_returns_429_after_30_requests():
    """31st request from user A returns 429; first 30 succeed."""
    from backend.app.main import app

    token = create_jwt(user_id="user-a", tenant_id="tenant-1", role="member")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        statuses = []
        for _ in range(31):
            r = await client.get(
                "/api/ai/status",
                headers={"Authorization": f"Bearer {token}"},
            )
            statuses.append(r.status_code)

    assert statuses[:30] == [200] * 30
    assert statuses[30] == 429


@pytest.mark.anyio
async def test_ai_status_rate_limit_is_per_user():
    """User B's first request returns 200 after user A has exhausted their limit."""
    from backend.app.main import app

    token_a = create_jwt(user_id="user-a", tenant_id="tenant-1", role="member")
    token_b = create_jwt(user_id="user-b", tenant_id="tenant-1", role="member")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(31):
            await client.get(
                "/api/ai/status",
                headers={"Authorization": f"Bearer {token_a}"},
            )

        response = await client.get(
            "/api/ai/status",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert response.status_code == 200
