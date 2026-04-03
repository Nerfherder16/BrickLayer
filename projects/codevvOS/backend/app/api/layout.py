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


async def _get_layout(user_id: str, tenant_id: str) -> Any:
    """Stub — returns stored layout record or None. Replaced in integration layer."""
    return None


async def _upsert_layout(
    user_id: str, tenant_id: str, layout_version: int, layout_json: dict[str, Any]
) -> None:
    """Stub — upserts layout record. Replaced in integration layer."""


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
