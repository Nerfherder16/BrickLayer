"""Tests for Docker secrets configuration via pydantic-settings."""
from pathlib import Path
import re


def test_settings_has_required_secret_fields():
    """Settings class must expose all five secret fields."""
    from backend.app.core.config import Settings

    required_fields = {
        "jwt_secret",
        "postgres_password",
        "anthropic_api_key",
        "recall_api_key",
        "bl_internal_secret",
    }
    model_fields = set(Settings.model_fields.keys())
    missing = required_fields - model_fields
    assert not missing, f"Settings is missing required fields: {missing}"


def test_settings_has_database_and_redis_urls():
    """Settings must provide database_url and redis_url properties."""
    from backend.app.core.config import Settings

    s = Settings()
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.redis_url.startswith("redis://")


def test_settings_uses_secrets_dir():
    """model_config must declare a secrets_dir so Docker secrets are picked up."""
    from backend.app.core.config import Settings

    assert "secrets_dir" in Settings.model_config, (
        "Settings.model_config must include secrets_dir='/run/secrets'"
    )


def test_no_plaintext_anthropic_key_in_compose():
    """docker-compose.yml must NOT contain ANTHROPIC_API_KEY= as a plaintext env var."""
    compose_path = Path(__file__).parents[2] / "docker-compose.yml"
    assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

    content = compose_path.read_text()
    # Look for the pattern that would indicate a hardcoded value assignment
    matches = re.findall(r"ANTHROPIC_API_KEY=\S+", content)
    assert not matches, (
        f"Found plaintext ANTHROPIC_API_KEY assignment in docker-compose.yml: {matches}. "
        "Use Docker secrets instead."
    )
