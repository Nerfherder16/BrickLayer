"""Structural tests for docker/yjs/ — TDD Task 1.23."""
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
YJS_DIR = PROJECT_ROOT / "docker" / "yjs"


def test_yjs_index_js_exists():
    assert (YJS_DIR / "index.js").exists(), "docker/yjs/index.js must exist"


def test_yjs_package_json_exists():
    assert (YJS_DIR / "package.json").exists(), "docker/yjs/package.json must exist"


def test_yjs_dockerfile_uses_node22_alpine():
    dockerfile = (YJS_DIR / "Dockerfile").read_text()
    assert "node:22-alpine" in dockerfile, "Dockerfile must use node:22-alpine"


def test_yjs_dockerfile_has_healthcheck():
    dockerfile = (YJS_DIR / "Dockerfile").read_text()
    assert "HEALTHCHECK" in dockerfile, "Dockerfile must contain HEALTHCHECK"


def test_yjs_index_js_has_auth():
    content = (YJS_DIR / "index.js").read_text()
    assert "verifyJwt" in content or "auth" in content, \
        "index.js must contain verifyJwt or auth"


def test_yjs_index_js_has_port_1234():
    content = (YJS_DIR / "index.js").read_text()
    assert "1234" in content, "index.js must reference port 1234"


def test_yjs_index_js_has_health_endpoint():
    content = (YJS_DIR / "index.js").read_text()
    assert "health" in content, "index.js must contain health endpoint"
