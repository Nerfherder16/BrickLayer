from __future__ import annotations

import uuid

from backend.app.models.base import Base
from sqlalchemy import TIMESTAMP, Column, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    workspace_template = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
