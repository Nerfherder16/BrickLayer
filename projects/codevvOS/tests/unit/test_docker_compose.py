"""Tests for docker-compose.yml scaffold correctness."""
import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose():
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"
    with open(COMPOSE_FILE) as f:
        return yaml.safe_load(f)


def test_only_nginx_has_ports(compose):
    """Only nginx may expose host ports; all other services use expose only."""
    services = compose["services"]
    for name, svc in services.items():
        if name == "nginx":
            assert "ports" in svc, "nginx must have a 'ports' key"
        else:
            assert "ports" not in svc, f"Service '{name}' must not have 'ports' (use 'expose' only)"


def test_all_services_have_restart(compose):
    services = compose["services"]
    for name, svc in services.items():
        assert "restart" in svc, f"Service '{name}' is missing 'restart' key"


def test_all_services_have_logging(compose):
    services = compose["services"]
    for name, svc in services.items():
        assert "logging" in svc, f"Service '{name}' is missing 'logging' key"


def test_secrets_section_exists(compose):
    """Top-level secrets block must define all five required secrets."""
    assert "secrets" in compose, "No top-level 'secrets' section found"
    secrets = compose["secrets"]
    required = {"jwt_secret", "postgres_password", "anthropic_api_key", "recall_api_key", "bl_internal_secret"}
    missing = required - set(secrets.keys())
    assert not missing, f"Missing secrets: {missing}"


def test_only_sandbox_manager_mounts_docker_sock(compose):
    """No service other than sandbox-manager may reference docker.sock."""
    services = compose["services"]
    for name, svc in services.items():
        if name == "sandbox-manager":
            continue
        volumes = svc.get("volumes", [])
        for vol in volumes:
            vol_str = str(vol)
            assert "docker.sock" not in vol_str, (
                f"Service '{name}' references docker.sock — only sandbox-manager may do this"
            )


def test_backend_networks_include_backend(compose):
    services = compose["services"]
    backend_svc = services.get("backend", {})
    networks = backend_svc.get("networks", [])
    assert "backend" in networks, "backend service must be on the 'backend' network"


def test_nginx_networks_include_frontend(compose):
    services = compose["services"]
    nginx_svc = services.get("nginx", {})
    networks = nginx_svc.get("networks", [])
    assert "frontend" in networks, "nginx service must be on the 'frontend' network"


def test_postgres_env_references_codevv_app(compose):
    """POSTGRES_USER or POSTGRES_DB must contain 'codevv_app'."""
    services = compose["services"]
    pg = services.get("postgres", {})
    env = pg.get("environment", {})
    if isinstance(env, list):
        env_str = " ".join(env)
        assert "codevv_app" in env_str, "postgres environment must reference codevv_app"
    else:
        user = str(env.get("POSTGRES_USER", ""))
        db = str(env.get("POSTGRES_DB", ""))
        assert "codevv_app" in user or "codevv_app" in db, (
            "POSTGRES_USER or POSTGRES_DB must contain 'codevv_app'"
        )
