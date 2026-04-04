"""Tests for Docker HEALTHCHECK directives and compose service health dependencies."""
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent

DOCKERFILES = [
    PROJECT_ROOT / "docker" / "backend" / "Dockerfile",
    PROJECT_ROOT / "docker" / "frontend" / "Dockerfile",
    PROJECT_ROOT / "docker" / "yjs" / "Dockerfile",
    PROJECT_ROOT / "docker" / "nginx" / "Dockerfile",
]


def test_dockerfiles_have_healthcheck():
    for path in DOCKERFILES:
        content = path.read_text()
        assert "HEALTHCHECK" in content, f"{path} is missing a HEALTHCHECK directive"


def test_compose_has_no_wait_for_healthy_script():
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    content = compose_path.read_text()
    assert "wait-for-healthy.sh" not in content, (
        "docker-compose.yml references wait-for-healthy.sh — use condition: service_healthy instead"
    )


def test_backend_depends_on_postgres_and_redis_service_healthy():
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    with compose_path.open() as f:
        compose = yaml.safe_load(f)

    backend = compose["services"]["backend"]
    depends_on = backend.get("depends_on", {})

    assert "postgres" in depends_on, "backend.depends_on missing postgres"
    assert depends_on["postgres"].get("condition") == "service_healthy", (
        "backend depends_on postgres must use condition: service_healthy"
    )

    assert "redis" in depends_on, "backend.depends_on missing redis"
    assert depends_on["redis"].get("condition") == "service_healthy", (
        "backend depends_on redis must use condition: service_healthy"
    )
