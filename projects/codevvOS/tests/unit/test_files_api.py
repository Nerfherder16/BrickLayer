"""Unit tests for GET /api/files/tree endpoint."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.auth import create_jwt


@pytest.fixture()
def workspace(tmp_path):
    """Real temp workspace with files and a .git dir."""
    (tmp_path / "README.md").write_text("hello")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
    return tmp_path


@pytest.fixture()
def auth_token():
    return create_jwt(user_id="u1", tenant_id="t1", role="member")


@pytest.fixture()
def client(workspace, monkeypatch):
    import backend.app.api.files as files_module

    monkeypatch.setattr(files_module, "WORKSPACE_ROOT", str(workspace))
    app = FastAPI()
    app.include_router(files_module.router)
    return TestClient(app, raise_server_exceptions=False)


def test_tree_returns_directory_listing(client, auth_token, workspace):
    """GET /api/files/tree with valid auth returns correct tree structure."""
    resp = client.get(
        f"/api/files/tree?path={workspace}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "dir"
    children_names = [e["name"] for e in data["children"]]
    assert "README.md" in children_names
    assert "src" in children_names


def test_tree_excludes_git_directory(client, auth_token, workspace):
    """.git directory is excluded from tree results."""
    resp = client.get(
        f"/api/files/tree?path={workspace}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    children_names = [e["name"] for e in resp.json()["children"]]
    assert ".git" not in children_names


def test_tree_path_traversal_returns_400(client, auth_token):
    """Path outside workspace root returns 400."""
    resp = client.get(
        "/api/files/tree?path=/etc/passwd",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 400


def test_tree_unauthenticated_returns_401(client):
    """Request without Authorization header returns 401."""
    resp = client.get("/api/files/tree?path=/tmp")
    assert resp.status_code == 401


def test_tree_nonexistent_path_returns_404(client, auth_token, workspace):
    """Path that does not exist on disk returns 404."""
    nonexistent = str(workspace / "does_not_exist")
    resp = client.get(
        f"/api/files/tree?path={nonexistent}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404
