"""Settings API: schema introspection, per-user settings, admin system settings."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.settings_schema import SystemSettings, UserSettings, to_draft7
from shared.auth import require_role

router = APIRouter()

# In-memory stores keyed by user_id (Phase 1 — no DB required)
_user_settings: dict[str, dict] = {}
_system_settings: dict = SystemSettings().model_dump()


@router.get("/api/settings/schema")
async def get_settings_schema() -> dict:
    """Return the UserSettings JSON schema in Draft-7 format."""
    raw = UserSettings.model_json_schema()
    return to_draft7(raw)


@router.get("/api/settings/user")
async def get_user_settings(user: dict = Depends(require_role("member"))) -> dict:
    """Return current settings for the authenticated user."""
    user_id: str = user["user_id"]
    return _user_settings.get(user_id, UserSettings().model_dump())


@router.put("/api/settings/user")
async def update_user_settings(
    updates: dict,
    user: dict = Depends(require_role("member")),
) -> dict:
    """Merge partial settings update for the authenticated user and return result."""
    user_id: str = user["user_id"]
    current = _user_settings.get(user_id, UserSettings().model_dump())
    current.update(updates)
    _user_settings[user_id] = current
    return current


@router.get("/api/admin/settings")
async def get_admin_settings(user: dict = Depends(require_role("admin"))) -> dict:
    """Return system-wide settings (admin only)."""
    return _system_settings


@router.put("/api/admin/settings")
async def update_admin_settings(
    updates: dict,
    user: dict = Depends(require_role("admin")),
) -> dict:
    """Merge partial system settings update (admin only) and return result."""
    _system_settings.update(updates)
    return _system_settings
