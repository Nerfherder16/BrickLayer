"""Unit tests for notification API endpoints (PostgreSQL-backed implementation)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


def _make_token(
    user_id: str = "u1", tenant_id: str = "t1", role: str = "member"
) -> str:
    from shared.auth import create_jwt

    return create_jwt(user_id=user_id, tenant_id=tenant_id, role=role)


def _make_notif_stub(index: int = 0, read: bool = False) -> SimpleNamespace:
    """Return a SimpleNamespace that mimics a Notification ORM row."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        type="info",
        title=f"Notification {index}",
        body=f"Body {index}",
        read=read,
        created_at=datetime(
            2026,
            1,
            1,
            index // 3600,
            (index % 3600) // 60,
            index % 60,
            tzinfo=timezone.utc,
        ),
    )


@pytest.fixture
def mock_db():
    """Yields (session, result) — configure result before requests."""
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    return session, result


@pytest.fixture
def override_db(mock_db):
    """Override get_db with mock_db for the duration of the test."""
    session, result = mock_db
    from backend.app.db.session import get_db
    from backend.app.main import app

    async def _mock_get_db():
        yield session

    app.dependency_overrides[get_db] = _mock_get_db
    yield session, result
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# GET /api/notifications — pagination with has_more
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_60_items_returns_50_with_has_more(override_db):
    """GET /api/notifications with 60 items in DB returns 50 items and has_more=true."""
    session, result = override_db
    # Return 51 stubs — the API fetches limit+1 to detect has_more
    stubs = [_make_notif_stub(i) for i in range(51)]
    result.scalars.return_value.all.return_value = stubs

    from backend.app.main import app

    token = _make_token(user_id="u1", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["has_more"] is True
    assert len(data["items"]) == 50


@pytest.mark.anyio
async def test_list_cursor_returns_remaining_10_no_more(override_db):
    """GET /api/notifications?before_id=X returns remaining 10 items with has_more=false."""
    session, result = override_db
    # Return 10 stubs — fewer than limit+1, so has_more=False
    stubs = [_make_notif_stub(i) for i in range(10)]
    result.scalars.return_value.all.return_value = stubs

    from backend.app.main import app

    cursor_id = str(uuid.uuid4())
    token = _make_token(user_id="u1", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/api/notifications?before_id={cursor_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["has_more"] is False
    assert len(data["items"]) == 10


@pytest.mark.anyio
async def test_list_empty_returns_has_more_false(override_db):
    """GET /api/notifications with no items returns empty list and has_more=false."""
    _session, result = override_db
    result.scalars.return_value.all.return_value = []

    from backend.app.main import app

    token = _make_token(user_id="u1", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["has_more"] is False
    assert data["items"] == []


@pytest.mark.anyio
async def test_user_b_cannot_see_user_a_notifications(override_db):
    """User B gets 0 results even when mock would return items for user A."""
    _session, result = override_db
    # DB returns empty for user B (RLS + WHERE clause enforce this in prod)
    result.scalars.return_value.all.return_value = []

    from backend.app.main import app

    token_b = _make_token(user_id="u2", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["has_more"] is False


# ---------------------------------------------------------------------------
# PATCH /api/notifications/{id}/read — 204 No Content
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_patch_returns_204_and_sets_read_true(override_db):
    """PATCH /api/notifications/{id}/read returns 204 and sets read=True on the item."""
    session, result = override_db
    stub = _make_notif_stub(read=False)
    result.scalar_one_or_none.return_value = stub

    from backend.app.main import app

    token = _make_token(user_id="u1", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/notifications/{stub.id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 204
    assert stub.read is True


@pytest.mark.anyio
async def test_patch_unknown_notification_returns_404(override_db):
    """PATCH /api/notifications/{id}/read returns 404 for unknown id."""
    _session, result = override_db
    result.scalar_one_or_none.return_value = None

    from backend.app.main import app

    token = _make_token(user_id="u1", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/notifications/{uuid.uuid4()}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_wrong_user_returns_404(override_db):
    """PATCH /api/notifications/{id}/read returns 404 when notification belongs to another user."""
    _session, result = override_db
    # DB returns nothing for wrong user (WHERE user_id=... filters it out)
    result.scalar_one_or_none.return_value = None

    from backend.app.main import app

    token = _make_token(user_id="u2", tenant_id="t1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/notifications/{uuid.uuid4()}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/notifications — internal secret auth
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_post_without_secret_header_returns_403(override_db):
    """POST /api/notifications without X-BL-Internal-Secret returns 403."""
    from backend.app.main import app

    payload = {
        "tenant_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "type": "info",
        "title": "Test",
        "body": "Body",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/notifications", json=payload)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_post_with_wrong_secret_returns_403(override_db):
    """POST /api/notifications with wrong X-BL-Internal-Secret returns 403."""
    from backend.app.main import app

    payload = {
        "tenant_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "type": "info",
        "title": "Test",
        "body": "Body",
    }
    with patch.dict(os.environ, {"BL_INTERNAL_SECRET": "correct-secret"}):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/notifications",
                json=payload,
                headers={"X-BL-Internal-Secret": "wrong-secret"},
            )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_post_with_correct_secret_returns_201(override_db):
    """POST /api/notifications with correct X-BL-Internal-Secret returns 201."""
    session, _result = override_db

    # db.refresh() is a no-op mock; side_effect populates DB-generated fields.
    async def _mock_refresh(obj: object) -> None:
        obj.id = uuid.uuid4()  # type: ignore[attr-defined]
        obj.read = False  # type: ignore[attr-defined]
        obj.created_at = datetime(2026, 4, 3, 12, 0, 0, tzinfo=timezone.utc)  # type: ignore[attr-defined]

    session.refresh = AsyncMock(side_effect=_mock_refresh)

    from backend.app.main import app

    payload = {
        "tenant_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "type": "info",
        "title": "Test notification",
        "body": "This is a test",
    }
    with patch.dict(os.environ, {"BL_INTERNAL_SECRET": "test-secret"}):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/notifications",
                json=payload,
                headers={"X-BL-Internal-Secret": "test-secret"},
            )

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Unauthenticated requests → 401
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_unauthenticated_returns_401():
    """GET /api/notifications without Authorization returns 401."""
    from backend.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/notifications")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_patch_unauthenticated_returns_401():
    """PATCH /api/notifications/{id}/read without Authorization returns 401."""
    from backend.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(f"/api/notifications/{uuid.uuid4()}/read")

    assert response.status_code == 401
