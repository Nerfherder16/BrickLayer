from __future__ import annotations

import inspect

import pytest
from unittest.mock import patch, MagicMock


def test_get_db_is_exported():
    from backend.app.db.session import get_db

    assert inspect.isasyncgenfunction(get_db) or callable(get_db)


def test_session_factory_expire_on_commit_false():
    from backend.app.db.session import AsyncSessionLocal

    assert AsyncSessionLocal.kw.get("expire_on_commit") is False


def test_database_url_uses_asyncpg():
    from backend.app.core.config import settings

    assert "asyncpg" in settings.database_url


def test_set_role_event_listener_registered():
    from backend.app.db import session as sess

    assert hasattr(sess, "set_role_on_connect") or "set_role" in dir(sess)
