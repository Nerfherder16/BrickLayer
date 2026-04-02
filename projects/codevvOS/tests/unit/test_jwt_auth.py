"""Unit tests for shared.auth JWT library."""
from __future__ import annotations

import time

import pytest


def test_create_jwt_exists():
    """create_jwt() is importable from shared.auth."""
    from shared.auth import create_jwt  # noqa: F401


def test_verify_jwt_returns_expected_fields():
    """verify_jwt() returns dict with user_id, tenant_id, role, exp."""
    from shared.auth import create_jwt, verify_jwt

    token = create_jwt(user_id="u1", tenant_id="t1", role="admin")
    payload = verify_jwt(token)

    assert payload["user_id"] == "u1"
    assert payload["tenant_id"] == "t1"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_verify_jwt_wrong_secret_raises():
    """verify_jwt() with a token signed by a different secret raises ValueError."""
    import jwt as pyjwt

    from shared.auth import verify_jwt

    bad_token = pyjwt.encode(
        {"user_id": "u1", "tenant_id": "t1", "role": "admin", "exp": int(time.time()) + 3600},
        "wrong-secret",
        algorithm="HS256",
    )
    with pytest.raises(ValueError):
        verify_jwt(bad_token)


def test_verify_jwt_alg_none_rejected():
    """Token with alg:none header is rejected with ValueError."""
    import jwt as pyjwt

    from shared.auth import verify_jwt

    # PyJWT won't encode with alg=none directly; craft the header manually
    header = pyjwt.utils.base64url_encode(b'{"alg":"none","typ":"JWT"}').decode()
    payload_b64 = pyjwt.utils.base64url_encode(
        b'{"user_id":"u1","tenant_id":"t1","role":"admin","exp":9999999999}'
    ).decode()
    none_token = f"{header}.{payload_b64}."

    with pytest.raises(ValueError):
        verify_jwt(none_token)


def test_require_role_rejects_wrong_role():
    """require_role('admin') raises HTTP 403 when caller has role 'member'."""
    import asyncio

    import pytest
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    from shared.auth import create_jwt, require_role

    token = create_jwt(user_id="u2", tenant_id="t1", role="member")
    dep = require_role("admin")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dep(creds))

    assert exc_info.value.status_code == 403


def test_verify_jwt_expired_token_rejected():
    """Expired token raises ValueError."""
    import jwt as pyjwt

    from shared.auth import verify_jwt

    expired_token = pyjwt.encode(
        {"user_id": "u1", "tenant_id": "t1", "role": "admin", "exp": int(time.time()) - 1},
        "dev-jwt-secret-change-in-prod",
        algorithm="HS256",
    )
    with pytest.raises(ValueError, match="expired"):
        verify_jwt(expired_token)
