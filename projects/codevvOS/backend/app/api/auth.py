"""Auth endpoints: login with rate limiting, logout with token blacklist, user list."""

from __future__ import annotations

import uuid

import bcrypt
from backend.app.core.security import RATE_LIMIT_LOGIN
from backend.app.db.session import get_db, set_tenant_context
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from shared.auth import create_jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth")
api_router = APIRouter(prefix="/api/auth")
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    user_id: str
    password: str


class RegisterAdminRequest(BaseModel):
    display_name: str
    email: str
    password: str


async def _get_user_by_id(user_id: str, db: AsyncSession) -> dict | None:
    """Look up a user by UUID. Gets tenant from the users table directly (superuser bypasses RLS)."""
    result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
    row = result.fetchone()
    if not row:
        return None
    await set_tenant_context(db, str(row[0]))
    result = await db.execute(
        text("SELECT id, tenant_id, email, password_hash, role FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "tenant_id": row[1],
        "email": row[2],
        "password_hash": row[3],
        "role": row[4],
    }


async def _blacklist_token(token: str) -> None:
    """Add token to Redis blacklist. Stub — implemented in integration layer."""


async def _get_all_users(db: AsyncSession) -> list[dict]:
    """Return all users in the tenant."""
    result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
    row = result.fetchone()
    if not row:
        return []
    await set_tenant_context(db, str(row[0]))
    result = await db.execute(text("SELECT id, email, role FROM users"))
    return [
        {"id": r[0], "email": r[1], "display_name": r[1], "role": r[2]} for r in result.fetchall()
    ]


def _compute_initials(display_name: str) -> str:
    """Compute avatar initials from display name (e.g. 'Tim Green' → 'TG')."""
    parts = display_name.strip().split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class UserSummary(BaseModel):
    id: str
    display_name: str
    avatar_initials: str


@api_router.post("/register-admin", status_code=201)
async def register_admin(body: RegisterAdminRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Create the initial admin account with a default tenant.

    Returns 409 if a tenant already exists (setup already completed).
    """
    async with db.begin():
        result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        if result.fetchone():
            raise HTTPException(status_code=409, detail="Admin account already exists")

        tenant_id = uuid.uuid4()
        await db.execute(
            text("INSERT INTO tenants (id, name, slug) VALUES (:id, :name, :slug)"),
            {"id": str(tenant_id), "name": "Default", "slug": "default"},
        )

        await set_tenant_context(db, str(tenant_id))

        password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        user_id = uuid.uuid4()
        await db.execute(
            text(
                "INSERT INTO users (id, tenant_id, email, password_hash, role) "
                "VALUES (:id, :tenant_id, :email, :password_hash, 'admin')"
            ),
            {
                "id": str(user_id),
                "tenant_id": str(tenant_id),
                "email": body.email,
                "password_hash": password_hash,
            },
        )

    token = create_jwt(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        role="admin",
    )
    return {
        "token": token,
        "user": {"id": str(user_id), "email": body.email, "role": "admin"},
    }


@api_router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserSummary]:
    """Return all users for the login screen picker. Unauthenticated."""
    users = await _get_all_users(db)
    return [
        UserSummary(
            id=str(u["id"]),
            display_name=u["display_name"],
            avatar_initials=_compute_initials(u["display_name"]),
        )
        for u in users
    ]


@router.post("/login")
@limiter.limit(RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Authenticate a user and return a JWT.

    Rate limited to 10 attempts per minute per IP.
    Returns 401 for invalid credentials, 429 when rate limit exceeded.
    """
    user = await _get_user_by_id(body.user_id, db)
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
        "user": {"id": str(user["id"]), "email": user["email"], "role": user["role"]},
    }


@router.post("/logout")
async def logout(request: Request) -> dict:
    """Invalidate a JWT by adding it to the Redis blacklist."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        await _blacklist_token(token)
    return {"status": "logged out"}
