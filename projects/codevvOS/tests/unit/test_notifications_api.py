"""Unit tests for notification API endpoints.

Uses in-memory store — no DB required for these tests.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


def _make_token(user_id: str = "u1", tenant_id: str = "t1", role: str = "member") -> str:
    from shared.auth import create_jwt
    return create_jwt(user_id=user_id, tenant_id=tenant_id, role=role)


def _seed_notifications(user_id: str = "u1", count: int = 5) -> list[dict]:
    """Populate the in-memory store and return the inserted items."""
    import uuid
    from datetime import datetime, timezone
    from backend.app.api import notifications as nmod

    nmod._notifications.clear()
    items = []
    for i in range(count):
        n = {
            "id": str(uuid.uuid4()),
            "tenant_id": "t1",
            "user_id": user_id,
            "type": "info",
            "title": f"Notification {i}",
            "body": f"Body {i}",
            "read": False,
            "created_at": datetime(2026, 1, 1, 0, 0, i, tzinfo=timezone.utc).isoformat(),
        }
        nmod._notifications.append(n)
        items.append(n)
    return items


@pytest.fixture(autouse=True)
def clear_notifications():
    """Reset in-memory store before each test."""
    from backend.app.api import notifications as nmod
    nmod._notifications.clear()
    yield
    nmod._notifications.clear()


# ---------------------------------------------------------------------------
# GET /api/notifications
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_notifications_returns_paginated_list():
    """GET /api/notifications returns list of notifications for the authenticated user."""
    from backend.app.main import app

    _seed_notifications(user_id="u1", count=3)
    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.anyio
async def test_list_notifications_respects_max_50():
    """GET /api/notifications returns at most 50 items by default."""
    from backend.app.main import app

    _seed_notifications(user_id="u1", count=60)
    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert len(response.json()) == 50


@pytest.mark.anyio
async def test_list_notifications_only_returns_own_user():
    """Notifications for other users are not returned."""
    from backend.app.main import app

    _seed_notifications(user_id="other-user", count=5)
    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/notifications?before_id=X  (cursor pagination)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_notifications_cursor_pagination():
    """GET /api/notifications?before_id=X returns items after the cursor (older)."""
    from backend.app.main import app

    items = _seed_notifications(user_id="u1", count=5)
    # Items are sorted newest-first; items[4] is the oldest (created_at second=4 → 0:00:04)
    # Sorted newest-first in the endpoint: index 0 = created_at=:04, index 4 = created_at=:00
    # We want items after cursor at position 1 (second-newest), which is 3 items.
    token = _make_token(user_id="u1")

    # First, get the full list to determine what the second item's id is
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        full_response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    full_list = full_response.json()
    assert len(full_list) == 5
    cursor_id = full_list[1]["id"]  # second-newest

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/api/notifications?before_id={cursor_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    page = response.json()
    assert len(page) == 3
    # None of the returned items should be the cursor item or newer
    returned_ids = {n["id"] for n in page}
    assert cursor_id not in returned_ids
    assert full_list[0]["id"] not in returned_ids


# ---------------------------------------------------------------------------
# PATCH /api/notifications/{id}/read
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_mark_notification_read():
    """PATCH /api/notifications/{id}/read sets read=True and returns updated record."""
    from backend.app.main import app

    items = _seed_notifications(user_id="u1", count=1)
    notif_id = items[0]["id"]
    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == notif_id
    assert body["read"] is True


@pytest.mark.anyio
async def test_mark_notification_read_wrong_user_returns_404():
    """PATCH /api/notifications/{id}/read returns 404 when notification belongs to another user."""
    from backend.app.main import app

    items = _seed_notifications(user_id="other-user", count=1)
    notif_id = items[0]["id"]
    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_mark_notification_read_nonexistent_returns_404():
    """PATCH /api/notifications/{id}/read returns 404 for unknown id."""
    from backend.app.main import app

    token = _make_token(user_id="u1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/api/notifications/does-not-exist/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Unauthenticated requests → 401
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_notifications_unauthenticated_returns_401():
    """GET /api/notifications without Authorization header returns 401."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/notifications")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_mark_read_unauthenticated_returns_401():
    """PATCH /api/notifications/{id}/read without Authorization header returns 401."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/notifications/some-id/read")

    assert response.status_code == 401
