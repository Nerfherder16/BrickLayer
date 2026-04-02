"""Unit tests for the 001_core_tables migration and SQLAlchemy models."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
MIGRATION_FILE = PROJECT_ROOT / "migrations" / "versions" / "001_core_tables.py"


def _load_migration():
    """Load the migration module from its file path (name starts with digit)."""
    spec = importlib.util.spec_from_file_location("migration_001_core_tables", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Migration file structure tests
# ---------------------------------------------------------------------------


def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration not found at {MIGRATION_FILE}"


def test_migration_has_upgrade_function():
    m = _load_migration()
    assert hasattr(m, "upgrade"), "Migration must have an upgrade() function"
    assert callable(m.upgrade)


def test_migration_has_downgrade_function():
    m = _load_migration()
    assert hasattr(m, "downgrade"), "Migration must have a downgrade() function"
    assert callable(m.downgrade)


def test_migration_downgrade_is_not_pass_only():
    m = _load_migration()
    src = inspect.getsource(m.downgrade)
    assert "drop_table" in src or "execute" in src or "drop_index" in src, (
        "downgrade() must contain real rollback logic, not just pass"
    )


# ---------------------------------------------------------------------------
# Migration file content checks (text scan)
# ---------------------------------------------------------------------------


def _migration_text() -> str:
    return MIGRATION_FILE.read_text()


def test_migration_creates_codevv_app_role():
    assert "codevv_app" in _migration_text(), (
        "Migration must create the codevv_app role"
    )


def test_migration_has_nologin_or_nobypassrls():
    text = _migration_text()
    assert "NOBYPASSRLS" in text or "NOLOGIN" in text, (
        "Migration must include NOBYPASSRLS or NOLOGIN in role definition"
    )


def test_migration_enables_rls():
    text = _migration_text().lower()
    assert "enable_row_level_security" in text or "rls" in text, (
        "Migration must enable row-level security"
    )


def test_migration_uses_current_setting_for_rls():
    assert "current_setting" in _migration_text(), (
        "RLS policy must use current_setting() for tenant isolation"
    )


def test_migration_references_tenant_id():
    assert "tenant_id" in _migration_text(), (
        "Migration must reference tenant_id for multi-tenancy"
    )


# ---------------------------------------------------------------------------
# SQLAlchemy model existence tests
# ---------------------------------------------------------------------------


def test_tenant_model_importable():
    from backend.app.models import Tenant  # noqa: PLC0415

    assert Tenant is not None


def test_user_model_importable():
    from backend.app.models import User  # noqa: PLC0415

    assert User is not None


def test_project_model_importable():
    from backend.app.models import Project  # noqa: PLC0415

    assert Project is not None


def test_workspace_template_model_importable():
    from backend.app.models import WorkspaceTemplate  # noqa: PLC0415

    assert WorkspaceTemplate is not None


def test_activity_event_model_importable():
    from backend.app.models import ActivityEvent  # noqa: PLC0415

    assert ActivityEvent is not None


def test_agent_run_model_importable():
    from backend.app.models import AgentRun  # noqa: PLC0415

    assert AgentRun is not None


# ---------------------------------------------------------------------------
# User model field checks
# ---------------------------------------------------------------------------


def test_user_model_has_role_field():
    from backend.app.models import User  # noqa: PLC0415
    from sqlalchemy import inspect as sa_inspect  # noqa: PLC0415

    mapper = sa_inspect(User)
    column_names = [c.key for c in mapper.mapper.column_attrs]
    assert "role" in column_names, "User model must have a 'role' field"
