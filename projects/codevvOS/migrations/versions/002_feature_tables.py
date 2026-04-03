"""feature tables — user_layouts

Revision ID: 002
Revises: 001
Create Date: 2026-04-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_layouts",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("layout_json", JSONB(), nullable=True),
        sa.Column("layout_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_layouts_user_tenant"),
    )

    op.execute("ALTER TABLE user_layouts ENABLE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON user_layouts TO codevv_app")
    op.execute(
        """
        CREATE POLICY user_layouts_tenant_isolation ON user_layouts
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )

    op.create_index("ix_user_layouts_user_tenant", "user_layouts", ["user_id", "tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_user_layouts_user_tenant", table_name="user_layouts")
    op.execute("DROP POLICY IF EXISTS user_layouts_tenant_isolation ON user_layouts")
    op.drop_table("user_layouts")
