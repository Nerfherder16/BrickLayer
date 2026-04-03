"""Layout persistence endpoints: GET/PUT /api/layout."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from shared.auth import verify_jwt

router = APIRouter(prefix="/api")
bearer_scheme = HTTPBearer()


class LayoutRequest(BaseModel):
    layout_version: int
    layout: dict[str, Any]

    @field_validator("layout_version")
    @classmethod
    def version_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Unsupported layout version")
        return v


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, str]:
    try:
        return verify_jwt(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


# In-memory store keyed by (user_id, tenant_id).
# A full implementation replaces this with a DB-backed store.
_layout_store: dict[tuple[str, str], dict[str, Any]] = {}


class _LayoutRecord:
    def __init__(self, layout_version: int, layout_json: dict[str, Any]) -> None:
        self.layout_version = layout_version
        self.layout_json = layout_json


async def _get_layout(user_id: str, tenant_id: str) -> _LayoutRecord | None:
    """Return the stored layout record for the user, or None if not set."""
    entry = _layout_store.get((user_id, tenant_id))
    if entry is None:
        return None
    return _LayoutRecord(entry["layout_version"], entry["layout_json"])


async def _upsert_layout(
    user_id: str, tenant_id: str, layout_version: int, layout_json: dict[str, Any]
) -> None:
    """Upsert the user's layout into the store."""
    _layout_store[(user_id, tenant_id)] = {
        "layout_version": layout_version,
        "layout_json": layout_json,
    }


@router.get("/layout")
async def get_layout(current_user: dict = Depends(_get_current_user)) -> dict:
    """Return the current user's saved layout, or null if none exists."""
    record = await _get_layout(
        user_id=current_user["user_id"],
        tenant_id=current_user["tenant_id"],
    )
    if record is None:
        return {"layout_version": None, "layout": None}
    return {"layout_version": record.layout_version, "layout": record.layout_json}


@router.put("/layout")
async def put_layout(
    body: LayoutRequest,
    current_user: dict = Depends(_get_current_user),
) -> dict:
    """Upsert the current user's layout."""
    await _upsert_layout(
        user_id=current_user["user_id"],
        tenant_id=current_user["tenant_id"],
        layout_version=body.layout_version,
        layout_json=body.layout,
    )
    return {"status": "ok"}
