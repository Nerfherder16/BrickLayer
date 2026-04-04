import configparser
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_alembic_ini_script_location():
    ini_path = PROJECT_ROOT / "alembic.ini"
    assert ini_path.exists(), f"alembic.ini not found at {ini_path}"
    config = configparser.ConfigParser()
    config.read(ini_path)
    assert config["alembic"]["script_location"] == "migrations"


def test_migrations_env_defines_run_migrations_online():
    import migrations.env as env  # noqa: PLC0415

    assert hasattr(env, "run_migrations_online"), (
        "migrations/env.py must define run_migrations_online"
    )
    assert callable(env.run_migrations_online)


def test_base_has_metadata():
    from backend.app.models.base import Base  # noqa: PLC0415

    assert hasattr(Base, "metadata"), "Base must have a metadata attribute"
