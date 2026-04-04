"""
Task 1.24 — Sandbox Manager Scaffold
Tests that the sandbox-manager service is correctly scaffolded.
Written BEFORE the service is created — they will fail until the
developer implements the service.
"""

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
SANDBOX_DIR = PROJECT_ROOT / "docker" / "sandbox-manager"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose():
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"
    with open(COMPOSE_FILE) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# 1. Directory and file existence
# ---------------------------------------------------------------------------


def test_sandbox_manager_directory_exists():
    assert SANDBOX_DIR.is_dir(), f"Missing directory: {SANDBOX_DIR}"


def test_sandbox_manager_dockerfile_exists():
    assert (SANDBOX_DIR / "Dockerfile").is_file(), (
        f"Missing file: {SANDBOX_DIR / 'Dockerfile'}"
    )


# ---------------------------------------------------------------------------
# 2. Dockerfile does NOT use docker-py (sync client blocks event loop)
# ---------------------------------------------------------------------------


def test_sandbox_manager_no_docker_py():
    """No source file in sandbox-manager may import the sync docker-py library."""
    py_files = list(SANDBOX_DIR.rglob("*.py"))
    assert py_files, f"No Python files found in {SANDBOX_DIR}"
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(("import docker", "from docker import", "from docker ")):
                # Allow "aiodocker" references — only flag the sync docker-py
                assert "aiodocker" in stripped, (
                    f"{py_file.relative_to(PROJECT_ROOT)}:{lineno} uses sync docker-py. "
                    f"Use aiodocker instead: {line!r}"
                )


# ---------------------------------------------------------------------------
# 3. docker-compose.yml — backend service does NOT mount docker.sock
# ---------------------------------------------------------------------------


def test_backend_service_does_not_mount_docker_sock(compose):
    """backend service must not reference docker.sock in any volume."""
    backend = compose.get("services", {}).get("backend", {})
    volumes = backend.get("volumes", [])
    for vol in volumes:
        assert "docker.sock" not in str(vol), (
            f"backend service mounts docker.sock — this is forbidden. "
            f"docker.sock access must be isolated to sandbox-manager only."
        )


# ---------------------------------------------------------------------------
# 4. Health endpoint present in app.py / main.py
# ---------------------------------------------------------------------------


def test_sandbox_manager_has_health_endpoint():
    """app.py or main.py must define a /health endpoint."""
    candidates = [SANDBOX_DIR / "app.py", SANDBOX_DIR / "main.py"]
    found_file = next((p for p in candidates if p.is_file()), None)
    assert found_file is not None, (
        f"Neither app.py nor main.py found in {SANDBOX_DIR}"
    )
    content = found_file.read_text(encoding="utf-8")
    assert "/health" in content or '"health"' in content, (
        f"{found_file.name} does not define a /health endpoint"
    )


# ---------------------------------------------------------------------------
# 5. Some file references aiodocker (async docker client)
# ---------------------------------------------------------------------------


def test_sandbox_manager_uses_aiodocker():
    """At least one file in sandbox-manager must reference aiodocker."""
    all_files = list(SANDBOX_DIR.rglob("*"))
    text_files = [f for f in all_files if f.is_file()]
    found = False
    for f in text_files:
        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        if "aiodocker" in content:
            found = True
            break
    assert found, (
        f"No file in {SANDBOX_DIR} references 'aiodocker'. "
        "The sandbox-manager must use the async aiodocker client."
    )
