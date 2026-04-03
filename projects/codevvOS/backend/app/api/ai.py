"""AI endpoints with per-user rate limiting."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from shared.auth import bearer_scheme, verify_jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

RATE_LIMIT_AI = "30/minute"


def _get_user_key(request: Request) -> str:
    """Extract user_id from JWT for per-user rate limiting, fall back to IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = verify_jwt(auth[7:])
            return f"user:{payload.get('user_id', '')}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_key)
router = APIRouter(prefix="/api/ai")


@router.get("/status")
@limiter.limit(RATE_LIMIT_AI)
async def ai_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Return AI service availability. Rate limited to 30 requests/minute per user."""
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"status": "available"}
