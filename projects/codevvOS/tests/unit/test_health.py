"""Tests for GET /health endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health_both_ok_returns_200():
    """GET /health returns 200 with healthy status when both postgres and redis are up."""
    from backend.app.main import app

    with (
        patch("backend.app.api.health._check_postgres", new=AsyncMock(return_value=True)),
        patch("backend.app.api.health._check_redis", new=AsyncMock(return_value=True)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["postgres"] is True
    assert body["redis"] is True


@pytest.mark.anyio
async def test_health_postgres_down_returns_503():
    """GET /health returns 503 with postgres: false when postgres is unreachable."""
    from backend.app.main import app

    with (
        patch("backend.app.api.health._check_postgres", new=AsyncMock(return_value=False)),
        patch("backend.app.api.health._check_redis", new=AsyncMock(return_value=True)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["postgres"] is False
    assert body["redis"] is True


@pytest.mark.anyio
async def test_health_redis_down_returns_503():
    """GET /health returns 503 with redis: false when redis is unreachable."""
    from backend.app.main import app

    with (
        patch("backend.app.api.health._check_postgres", new=AsyncMock(return_value=True)),
        patch("backend.app.api.health._check_redis", new=AsyncMock(return_value=False)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["postgres"] is True
    assert body["redis"] is False


@pytest.mark.anyio
async def test_health_no_auth_required():
    """GET /health is unauthenticated — no Authorization header needed."""
    from backend.app.main import app

    with (
        patch("backend.app.api.health._check_postgres", new=AsyncMock(return_value=True)),
        patch("backend.app.api.health._check_redis", new=AsyncMock(return_value=True)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code != 401
    assert response.status_code != 403
