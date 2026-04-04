"""Tests for the 003_notifications migration — notifications table."""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
MIGRATION_FILE = PROJECT_ROOT / "migrations" / "versions" / "003_notifications.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "migration_003_notifications", MIGRATION_FILE
    )
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


def test_migration_revision_is_003():
    m = _load_migration()
    assert m.revision == "003"


def test_migration_down_revision_is_002():
    m = _load_migration()
    assert m.down_revision == "002"


def test_migration_creates_notifications_table():
    assert "notifications" in _migration_text()


def test_migration_has_id_column():
    text = _migration_text()
    assert '"id"' in text or "'id'" in text
    assert "gen_random_uuid" in text


def test_migration_has_tenant_id_column():
    assert "tenant_id" in _migration_text()


def test_migration_has_user_id_column():
    assert "user_id" in _migration_text()


def test_migration_has_type_column():
    assert '"type"' in _migration_text() or "'type'" in _migration_text()


def test_migration_has_title_column():
    assert "title" in _migration_text()


def test_migration_has_read_column_with_false_default():
    text = _migration_text()
    assert "read" in text
    assert "false" in text.lower()


def test_migration_has_created_at_with_timezone():
    text = _migration_text()
    assert "created_at" in text
    assert (
        "timezone=True" in text or "TIMESTAMPTZ" in text.upper() or "timezone" in text
    )


def test_migration_enables_rls():
    text = _migration_text()
    assert "ENABLE ROW LEVEL SECURITY" in text


def test_migration_rls_policy_uses_current_setting():
    text = _migration_text()
    assert "current_setting" in text
    assert "app.current_tenant_id" in text


def test_migration_grants_to_codevv_app():
    text = _migration_text()
    assert "codevv_app" in text
    assert "GRANT" in text


def test_migration_has_index_tenant_user_created():
    text = _migration_text()
    assert "ix_notifications_tenant_user_created" in text


def test_migration_has_index_tenant_user_read():
    text = _migration_text()
    assert "ix_notifications_tenant_user_read" in text


def test_migration_downgrade_drops_notifications_table():
    m = _load_migration()
    src = inspect.getsource(m.downgrade)
    assert "notifications" in src
    assert "drop_table" in src or "execute" in src


def test_migration_downgrade_drops_policy():
    src = inspect.getsource(_load_migration().downgrade)
    assert "DROP POLICY" in src or "notifications_tenant_isolation" in src


# ---------------------------------------------------------------------------
# SQLAlchemy model tests
# ---------------------------------------------------------------------------


def test_notification_model_importable():
    from backend.app.models.notification import Notification  # noqa: PLC0415

    assert Notification is not None


def test_notification_model_tablename():
    from backend.app.models.notification import Notification  # noqa: PLC0415

    assert Notification.__tablename__ == "notifications"


def test_notification_model_has_required_columns():
    from backend.app.models.notification import Notification  # noqa: PLC0415
    from sqlalchemy import inspect as sa_inspect  # noqa: PLC0415

    cols = [c.key for c in sa_inspect(Notification).mapper.column_attrs]
    for required in (
        "id",
        "tenant_id",
        "user_id",
        "type",
        "title",
        "body",
        "read",
        "created_at",
    ):
        assert required in cols, f"Missing column: {required}"


def test_notification_model_in_models_init():
    from backend.app.models import Notification  # noqa: PLC0415

    assert Notification is not None
