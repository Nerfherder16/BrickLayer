"""Tests for the 002_feature_tables migration — user_layouts table."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
MIGRATION_FILE = PROJECT_ROOT / "migrations" / "versions" / "002_feature_tables.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_002_feature_tables", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _migration_text() -> str:
    return MIGRATION_FILE.read_text()


def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration not found at {MIGRATION_FILE}"


def test_migration_has_upgrade_function():
    m = _load_migration()
    assert hasattr(m, "upgrade") and callable(m.upgrade)


def test_migration_has_downgrade_function():
    m = _load_migration()
    assert hasattr(m, "downgrade") and callable(m.downgrade)


def test_migration_downgrade_drops_user_layouts():
    m = _load_migration()
    src = inspect.getsource(m.downgrade)
    assert "user_layouts" in src, "downgrade() must drop user_layouts table"
    assert "drop_table" in src or "execute" in src


def test_migration_creates_user_layouts_table():
    assert "user_layouts" in _migration_text()


def test_migration_has_layout_json_jsonb():
    text = _migration_text()
    assert "JSONB" in text or "jsonb" in text.lower(), "layout_json must use JSONB type"


def test_migration_has_layout_version_with_default_1():
    text = _migration_text()
    assert "layout_version" in text
    assert "server_default" in text or "default=1" in text or "server_default=sa.text" in text


def test_migration_enables_rls_on_user_layouts():
    text = _migration_text()
    assert "ENABLE ROW LEVEL SECURITY" in text or "enable_row_level_security" in text.lower()


def test_migration_rls_policy_uses_current_setting():
    text = _migration_text()
    assert "current_setting" in text, "RLS policy must use current_setting()"
    assert "app.current_tenant_id" in text


def test_migration_has_unique_constraint_on_user_tenant():
    text = _migration_text()
    assert "UniqueConstraint" in text or "UNIQUE" in text
    # Both user_id and tenant_id must appear in the constraint context
    assert "user_id" in text and "tenant_id" in text


def test_migration_revision_is_002():
    m = _load_migration()
    assert m.revision == "002"


def test_migration_down_revision_is_001():
    m = _load_migration()
    assert m.down_revision == "001"


# ---------------------------------------------------------------------------
# SQLAlchemy model tests
# ---------------------------------------------------------------------------


def test_user_layout_model_importable():
    from backend.app.models.layout import UserLayout  # noqa: PLC0415

    assert UserLayout is not None


def test_user_layout_model_tablename():
    from backend.app.models.layout import UserLayout  # noqa: PLC0415

    assert UserLayout.__tablename__ == "user_layouts"


def test_user_layout_model_has_layout_json():
    from backend.app.models.layout import UserLayout  # noqa: PLC0415
    from sqlalchemy import inspect as sa_inspect  # noqa: PLC0415

    cols = [c.key for c in sa_inspect(UserLayout).mapper.column_attrs]
    assert "layout_json" in cols


def test_user_layout_model_has_layout_version():
    from backend.app.models.layout import UserLayout  # noqa: PLC0415
    from sqlalchemy import inspect as sa_inspect  # noqa: PLC0415

    cols = [c.key for c in sa_inspect(UserLayout).mapper.column_attrs]
    assert "layout_version" in cols


def test_user_layout_model_in_models_init():
    from backend.app.models import UserLayout  # noqa: PLC0415

    assert UserLayout is not None
