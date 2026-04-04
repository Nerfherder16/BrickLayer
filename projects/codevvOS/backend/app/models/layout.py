from __future__ import annotations

import uuid

from backend.app.models.base import Base
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import JSONB, UUID


class UserLayout(Base):
    __tablename__ = "user_layouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    layout_json = Column(JSONB(), nullable=True)
    layout_version = Column(Integer(), nullable=False, default=1)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
