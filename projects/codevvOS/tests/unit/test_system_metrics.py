"""Unit tests for GET /api/system/metrics endpoint."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from shared.auth import create_jwt


def _auth_header(role: str) -> dict[str, str]:
    token = create_jwt(user_id="u1", tenant_id="t1", role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_system_metrics_returns_parsed_cgroup_values():
    """GET /api/system/metrics returns correct parsed values from cgroup files."""
    from backend.app.main import app

    with (
        patch(
            "backend.app.api.system._read_cgroup_file",
            side_effect=lambda f: {
                "memory.current": 104857600,
                "memory.max": 2147483648,
            }.get(f),
        ),
        patch("backend.app.api.system._read_cpu_usage", return_value=5000000),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/system/metrics", headers=_auth_header("admin")
            )

    assert response.status_code == 200
    body = response.json()
    assert body["memory_used_bytes"] == 104857600
    assert body["memory_limit_bytes"] == 2147483648
    assert body["cpu_usage_usec"] == 5000000


@pytest.mark.anyio
async def test_system_metrics_missing_cgroup_files_returns_nulls():
    """GET /api/system/metrics returns nulls when cgroup files are absent."""
    from backend.app.main import app

    with (
        patch("backend.app.api.system._read_cgroup_file", return_value=None),
        patch("backend.app.api.system._read_cpu_usage", return_value=None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/system/metrics", headers=_auth_header("admin")
            )

    assert response.status_code == 200
    body = response.json()
    assert body["memory_used_bytes"] is None
    assert body["memory_limit_bytes"] is None
    assert body["cpu_usage_usec"] is None


@pytest.mark.anyio
async def test_system_metrics_member_token_returns_403():
    """GET /api/system/metrics returns 403 when called with a member-role token."""
    from backend.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/system/metrics", headers=_auth_header("member")
        )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_system_metrics_admin_token_returns_200():
    """GET /api/system/metrics returns 200 when called with an admin-role token."""
    from backend.app.main import app

    with (
        patch("backend.app.api.system._read_cgroup_file", return_value=None),
        patch("backend.app.api.system._read_cpu_usage", return_value=None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/system/metrics", headers=_auth_header("admin")
            )

    assert response.status_code == 200
