from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, JSON, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from backend.app.models.base import Base


class WorkspaceTemplate(Base):
    __tablename__ = "workspace_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    config = Column(JSON(), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
