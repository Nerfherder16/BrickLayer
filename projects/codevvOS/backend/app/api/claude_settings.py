"""Claude AI key management endpoints — JWT-gated, no OAuth PKCE."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from shared.auth import bearer_scheme, verify_jwt

router = APIRouter(prefix="/api")

# In-memory store: user_id -> placeholder (Phase 1 — no DB required)
_claude_keys: dict[str, str] = {}


class ClaudeKeyRequest(BaseModel):
    api_key: str


def _get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        return verify_jwt(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.put("/settings/claude-key")
async def store_claude_key(
    body: ClaudeKeyRequest,
    user: dict = Depends(_get_current_user),
) -> dict:
    """Store (placeholder) for a user's personal Claude API key."""
    _claude_keys[user.get("user_id", "")] = "[ENCRYPTED_PLACEHOLDER]"
    return {"status": "stored"}


@router.delete("/settings/claude-key")
async def delete_claude_key(user: dict = Depends(_get_current_user)) -> dict:
    """Remove a user's personal Claude API key."""
    _claude_keys.pop(user.get("user_id", ""), None)
    return {"status": "deleted"}


@router.get("/ai/config")
async def get_ai_config(user: dict = Depends(_get_current_user)) -> dict:
    """Return AI config for the current user, including whether a personal key is stored."""
    return {"has_personal_key": user.get("user_id", "") in _claude_keys}
