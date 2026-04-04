"""
Task 1.19 — Structural tests for the ptyHost WebSocket service.
Verifies docker/ptyhost/ directory layout and key file contents.
"""
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PTYHOST_DIR = os.path.join(PROJECT_ROOT, "docker", "ptyhost")


def test_ptyhost_directory_exists():
    assert os.path.isdir(PTYHOST_DIR), f"docker/ptyhost/ directory not found at {PTYHOST_DIR}"


def test_package_json_exists():
    path = os.path.join(PTYHOST_DIR, "package.json")
    assert os.path.isfile(path), "docker/ptyhost/package.json not found"


def test_index_js_exists():
    index_root = os.path.join(PTYHOST_DIR, "index.js")
    index_src = os.path.join(PTYHOST_DIR, "src", "index.js")
    assert os.path.isfile(index_root) or os.path.isfile(index_src), (
        "Neither docker/ptyhost/index.js nor docker/ptyhost/src/index.js found"
    )


def test_dockerfile_exists():
    path = os.path.join(PTYHOST_DIR, "Dockerfile")
    assert os.path.isfile(path), "docker/ptyhost/Dockerfile not found"


def test_dockerfile_uses_node22_alpine():
    path = os.path.join(PTYHOST_DIR, "Dockerfile")
    content = open(path).read()
    assert "node:22-alpine" in content, "Dockerfile must use node:22-alpine base image"


def test_dockerfile_has_healthcheck():
    path = os.path.join(PTYHOST_DIR, "Dockerfile")
    content = open(path).read()
    assert "HEALTHCHECK" in content, "Dockerfile must include a HEALTHCHECK instruction"


def _read_index_js():
    index_root = os.path.join(PTYHOST_DIR, "index.js")
    index_src = os.path.join(PTYHOST_DIR, "src", "index.js")
    if os.path.isfile(index_root):
        return open(index_root).read()
    return open(index_src).read()


def test_index_js_has_auth():
    content = _read_index_js()
    assert "wsAuthMiddleware" in content or "verifyJwt" in content, (
        "index.js must reference wsAuthMiddleware or verifyJwt"
    )


def test_index_js_has_node_pty():
    content = _read_index_js()
    assert "node-pty" in content or "pty" in content, (
        "index.js must reference node-pty or pty"
    )


def test_index_js_exposes_port_3001():
    content = _read_index_js()
    assert "3001" in content, "index.js must reference port 3001"
