from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from backend.app.db.session import get_db, set_tenant_context
from backend.app.models.notification import Notification
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from shared.auth import bearer_scheme, verify_jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api")


class NotificationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str | None
    read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationItem]
    has_more: bool


class NotificationCreate(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str | None = None


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        return verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


async def _sse_heartbeat() -> AsyncGenerator[str, None]:
    """Yield SSE keep-alive comments every 15 seconds."""
    while True:
        yield ": heartbeat\n\n"
        await asyncio.sleep(15)


@router.get("/events")
async def sse_events() -> StreamingResponse:
    """Server-Sent Events stream for live preview auto-reload and push notifications."""
    return StreamingResponse(
        _sse_heartbeat(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/notifications", response_model=NotificationList)
async def list_notifications(
    limit: int = Query(default=50, le=100),
    before_id: uuid.UUID | None = Query(default=None),
    user: dict = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationList:
    tenant_id = user["tenant_id"]
    user_id = user["user_id"]
    await set_tenant_context(db, tenant_id)

    stmt = (
        select(Notification)
        .where(Notification.tenant_id == tenant_id, Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit + 1)
    )
    if before_id is not None:
        sub = select(Notification.created_at).where(Notification.id == before_id).scalar_subquery()
        stmt = stmt.where(Notification.created_at < sub)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = [NotificationItem.model_validate(r) for r in rows[:limit]]
    return NotificationList(items=items, has_more=has_more)


@router.patch("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: dict = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    tenant_id = user["tenant_id"]
    user_id = user["user_id"]
    await set_tenant_context(db, tenant_id)

    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
        Notification.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    notif = result.scalar_one_or_none()
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    await db.commit()
    return Response(status_code=204)


@router.post("/notifications", status_code=201)
async def create_notification(
    body: NotificationCreate,
    x_bl_internal_secret: str | None = Header(default=None, alias="X-BL-Internal-Secret"),
    db: AsyncSession = Depends(get_db),
) -> NotificationItem:
    secret = os.environ.get("BL_INTERNAL_SECRET", "")
    if not secret or x_bl_internal_secret != secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    notif = Notification(
        tenant_id=body.tenant_id,
        user_id=body.user_id,
        type=body.type,
        title=body.title,
        body=body.body,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return NotificationItem.model_validate(notif)
