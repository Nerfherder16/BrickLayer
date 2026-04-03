from __future__ import annotations

import uuid

from backend.app.models.base import Base
from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    result = Column(JSON(), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
