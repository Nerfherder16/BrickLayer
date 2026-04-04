from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer()


def _get_secret() -> str:
    p = Path("/run/secrets/jwt_secret")
    if p.exists():
        return p.read_text().strip()
    return os.environ.get("JWT_SECRET", "dev-jwt-secret-change-in-prod")


def create_jwt(user_id: str, tenant_id: str, role: str, expires_delta: int = 3600) -> str:
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": int(time.time()) + expires_delta,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def verify_jwt(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        raise ValueError(f"Invalid token header: {e}")

    if header.get("alg", "").lower() == "none":
        raise ValueError("Algorithm 'none' is not allowed")

    try:
        payload = jwt.decode(
            token,
            _get_secret(),
            algorithms=[ALGORITHM],  # Explicit allowlist — never empty
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")


def require_role(required_role: str):
    async def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> dict:
        try:
            payload = verify_jwt(credentials.credentials)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

        if payload.get("role") != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required, got '{payload.get('role')}'",
            )
        return payload

    return dependency
