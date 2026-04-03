from __future__ import annotations

import uuid
from datetime import UTC, datetime

from backend.app.models.base import Base
from sqlalchemy import BOOLEAN, TEXT, TIMESTAMP, Column, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(TEXT, nullable=False)
    title = Column(TEXT, nullable=False)
    body = Column(TEXT, nullable=True)
    read = Column(
        BOOLEAN,
        nullable=False,
        server_default=text("false"),
        default=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
    )
