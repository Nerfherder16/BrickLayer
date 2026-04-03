"""notifications table

Revision ID: 003
Revises: 002
Create Date: 2026-04-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.TEXT(), nullable=False),
        sa.Column("title", sa.TEXT(), nullable=False),
        sa.Column("body", sa.TEXT(), nullable=True),
        sa.Column(
            "read", sa.BOOLEAN(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON notifications TO codevv_app")
    op.execute(
        """
        CREATE POLICY notifications_tenant_isolation ON notifications
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )

    op.execute(
        "CREATE INDEX ix_notifications_tenant_user_created"
        " ON notifications (tenant_id, user_id, created_at DESC)"
    )
    op.create_index(
        "ix_notifications_tenant_user_read",
        "notifications",
        ["tenant_id", "user_id", "read"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_tenant_user_read", table_name="notifications")
    op.execute("DROP INDEX IF EXISTS ix_notifications_tenant_user_created")
    op.execute("DROP POLICY IF EXISTS notifications_tenant_isolation ON notifications")
    op.drop_table("notifications")
