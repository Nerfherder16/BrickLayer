"""
Task 1.2 — Docker Network Isolation
Verifies network segmentation, logging, and resource limits in docker-compose.yml.
"""
import pathlib
import pytest
import yaml


COMPOSE_PATH = pathlib.Path(__file__).parents[2] / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose():
    with open(COMPOSE_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def services(compose):
    return compose["services"]


def test_postgres_not_on_frontend_network(services):
    """postgres must be isolated to the backend network only."""
    postgres_networks = list(services["postgres"].get("networks", {}) or [])
    assert "frontend" not in postgres_networks, (
        f"postgres must NOT be on the frontend network, got: {postgres_networks}"
    )


def test_nginx_on_both_networks(services):
    """nginx is the only service that bridges frontend and backend."""
    nginx_networks = list(services["nginx"].get("networks", {}) or [])
    assert "frontend" in nginx_networks, "nginx must be on the frontend network"
    assert "backend" in nginx_networks, "nginx must be on the backend network"


def test_all_services_have_logging(services):
    """Every service must declare a logging driver (prevents unbounded log growth)."""
    missing = [
        name for name, cfg in services.items()
        if not cfg.get("logging")
    ]
    assert not missing, f"Services missing 'logging' key: {missing}"


def test_all_services_have_memory_limit(services):
    """Every service must declare deploy.resources.limits.memory."""
    missing = []
    for name, cfg in services.items():
        try:
            _ = cfg["deploy"]["resources"]["limits"]["memory"]
        except (KeyError, TypeError):
            missing.append(name)
    assert not missing, f"Services missing memory limit: {missing}"
