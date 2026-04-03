from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from shared.auth import bearer_scheme, verify_jwt

router = APIRouter(prefix="/api")

# In-memory store for Phase 1 unit tests
_notifications: list[dict] = []


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        return verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.get("/notifications")
async def list_notifications(
    limit: int = Query(default=50, le=100),
    before_id: str | None = Query(default=None),
    user: dict = Depends(_get_current_user),
):
    user_id = user.get("user_id", "")
    user_notifications = [n for n in _notifications if n["user_id"] == user_id]
    user_notifications.sort(key=lambda n: n["created_at"], reverse=True)

    if before_id:
        idx = next((i for i, n in enumerate(user_notifications) if n["id"] == before_id), None)
        if idx is not None:
            user_notifications = user_notifications[idx + 1:]

    return user_notifications[:limit]


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: dict = Depends(_get_current_user),
):
    user_id = user.get("user_id", "")
    for n in _notifications:
        if n["id"] == notification_id and n["user_id"] == user_id:
            n["read"] = True
            return n
    raise HTTPException(status_code=404, detail="Notification not found")
