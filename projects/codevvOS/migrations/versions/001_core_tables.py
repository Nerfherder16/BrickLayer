"""core tables

Revision ID: 001
Revises:
Create Date: 2026-04-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create codevv_app role with NOLOGIN NOBYPASSRLS NOINHERIT
    op.execute("""
        DO $$ BEGIN
            CREATE ROLE codevv_app WITH NOLOGIN NOBYPASSRLS NOINHERIT;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email"),
    )

    # projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workspace_template", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # workspace_templates table
    op.create_table(
        "workspace_templates",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # activity_events table
    op.create_table(
        "activity_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # agent_runs table
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Enable RLS on all tenant-scoped tables
    for table in ["users", "projects", "workspace_templates", "activity_events", "agent_runs"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO codevv_app")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            """
        )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO codevv_app")

    # Composite indexes
    for table in ["users", "projects", "workspace_templates", "activity_events", "agent_runs"]:
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id", "id"])
        op.create_index(
            f"ix_{table}_tenant_created",
            table,
            ["tenant_id", sa.text("created_at DESC")],
        )


def downgrade() -> None:
    # Drop indexes
    for table in ["users", "projects", "workspace_templates", "activity_events", "agent_runs"]:
        op.drop_index(f"ix_{table}_tenant_created", table_name=table)
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)

    # Drop RLS policies
    for table in ["users", "projects", "workspace_templates", "activity_events", "agent_runs"]:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")

    # Drop tables in reverse order
    op.drop_table("agent_runs")
    op.drop_table("activity_events")
    op.drop_table("workspace_templates")
    op.drop_table("projects")
    op.drop_table("users")
    op.drop_table("tenants")

    # Drop role
    op.execute("DROP ROLE IF EXISTS codevv_app")
