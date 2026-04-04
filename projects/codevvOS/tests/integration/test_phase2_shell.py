"""
Phase 2 Graduation Integration Test — Full Backend Shell Flow

Validates the complete Phase 2 API surface:
  a. GET /api/auth/users → returns JSON array of users
  b. POST /auth/login   → returns JWT on valid credentials
  c. GET /api/layout    → returns null layout for new/fresh session
  d. PUT /api/layout    → saves layout, returns {"status": "ok"}
  e. GET /api/layout    → returns the saved layout

Requires the Docker Compose stack to be running.
Skips gracefully if the server is not reachable.

To run:
  INTEGRATION_TESTS=1 uv run pytest tests/integration/test_phase2_shell.py -m integration -q
"""
from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.integration

BACKEND_URL = os.environ.get("TEST_BACKEND_URL", "http://localhost:8000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "test@codevvos.test")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "test-password-123")
_SKIP_REASON = "Backend not reachable — start the compose stack to run integration tests"


def _server_reachable() -> bool:
    """Return True if the backend health endpoint responds within 5 s."""
    try:
        with httpx.Client(timeout=5) as client:
            return client.get(f"{BACKEND_URL}/health").status_code == 200
    except Exception:
        return False


SERVER_UP = _server_reachable()
_skip = pytest.mark.skipif(not SERVER_UP, reason=_SKIP_REASON)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def http_client():
    with httpx.Client(timeout=30) as client:
        yield client


@pytest.fixture(scope="module")
def auth_token(http_client: httpx.Client) -> str | None:
    """Return a JWT for the test user, or None if the user doesn't exist."""
    if not SERVER_UP:
        return None
    resp = http_client.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    if resp.status_code == 200:
        return resp.json()["token"]
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@_skip
def test_list_users_returns_array(http_client: httpx.Client) -> None:
    """GET /api/auth/users returns a JSON array (may be empty on fresh stack)."""
    resp = http_client.get(f"{BACKEND_URL}/api/auth/users")
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    for user in users:
        assert "id" in user
        assert "display_name" in user
        assert "avatar_initials" in user


@_skip
def test_login_returns_jwt(http_client: httpx.Client) -> None:
    """POST /auth/login returns 200 + JWT on valid credentials, or 401 if user absent."""
    resp = http_client.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code in (200, 401), f"Unexpected status: {resp.status_code}"
    if resp.status_code == 200:
        body = resp.json()
        assert "token" in body
        assert isinstance(body["token"], str)
        assert len(body["token"]) > 10


@_skip
def test_get_layout_returns_valid_schema(
    http_client: httpx.Client, auth_token: str | None
) -> None:
    """GET /api/layout returns {layout_version, layout} — null for new users."""
    if auth_token is None:
        pytest.skip(
            "Test user not available; set TEST_USER_EMAIL / TEST_USER_PASSWORD to enable"
        )
    resp = http_client.get(
        f"{BACKEND_URL}/api/layout",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "layout_version" in body
    assert "layout" in body
    # Invariant: null layout_version implies null layout
    if body["layout_version"] is None:
        assert body["layout"] is None


@_skip
def test_layout_put_and_get_roundtrip(
    http_client: httpx.Client, auth_token: str | None
) -> None:
    """PUT /api/layout saves layout; subsequent GET returns the saved value."""
    if auth_token is None:
        pytest.skip(
            "Test user not available; set TEST_USER_EMAIL / TEST_USER_PASSWORD to enable"
        )
    headers = {"Authorization": f"Bearer {auth_token}"}
    test_layout: dict = {"orientation": "HORIZONTAL", "panels": [{"id": "welcome"}]}

    # d. PUT — save a known layout
    put_resp = http_client.put(
        f"{BACKEND_URL}/api/layout",
        json={"layout_version": 1, "layout": test_layout},
        headers=headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["status"] == "ok"

    # e. GET — must reflect what we just saved
    get_resp = http_client.get(f"{BACKEND_URL}/api/layout", headers=headers)
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["layout_version"] == 1
    assert body["layout"] == test_layout
