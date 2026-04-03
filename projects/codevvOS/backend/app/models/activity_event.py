from __future__ import annotations

import uuid

from backend.app.models.base import Base
from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON(), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
