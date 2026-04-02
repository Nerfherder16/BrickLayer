"""Auth endpoints: login with rate limiting, logout with token blacklist."""
from __future__ import annotations

import bcrypt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.security import RATE_LIMIT_LOGIN
from shared.auth import create_jwt

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    email: str
    password: str


async def _get_user_by_email(email: str) -> dict | None:
    """Look up a user by email. Returns user dict or None if not found.

    Stub — real implementation queries the DB via get_db dependency.
    Designed as a standalone coroutine so unit tests can patch it directly.
    """
    return None


async def _blacklist_token(token: str) -> None:
    """Add token to Redis blacklist. Stub — implemented in integration layer."""


@router.post("/login")
@limiter.limit(RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest) -> dict:
    """Authenticate a user and return a JWT.

    Rate limited to 10 attempts per minute per IP.
    Returns 401 for invalid credentials, 429 when rate limit exceeded.
    """
    user = await _get_user_by_email(body.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(body.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt(
        user_id=str(user["id"]),
        tenant_id=str(user["tenant_id"]),
        role=user["role"],
    )
    return {
        "token": token,
        "user": {"id": str(user["id"]), "email": body.email, "role": user["role"]},
    }


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Invalidate a JWT by adding it to the Redis blacklist."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        await _blacklist_token(token)
    return {"status": "logged out"}
