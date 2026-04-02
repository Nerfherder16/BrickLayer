"""Unit tests for PATCH /api/files/{path} file operations endpoint."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.auth import create_jwt


@pytest.fixture()
def workspace(tmp_path):
    """Temp workspace with a file and a subdirectory."""
    (tmp_path / "hello.txt").write_text("hello world")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.txt").write_text("nested content")
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


def _patch(client, workspace, rel_path, payload, token):
    abs_path = str(workspace / rel_path) if rel_path else str(workspace)
    return client.patch(
        f"/api/files/{abs_path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )


# ---------------------------------------------------------------------------
# action: read
# ---------------------------------------------------------------------------


def test_patch_read_returns_file_content(client, auth_token, workspace):
    """PATCH action:read returns the file's content."""
    resp = _patch(client, workspace, "hello.txt", {"action": "read"}, auth_token)
    assert resp.status_code == 200
    assert resp.json()["content"] == "hello world"


# ---------------------------------------------------------------------------
# action: write
# ---------------------------------------------------------------------------


def test_patch_write_updates_file_content(client, auth_token, workspace):
    """PATCH action:write overwrites the file with new content."""
    resp = _patch(
        client,
        workspace,
        "hello.txt",
        {"action": "write", "content": "updated"},
        auth_token,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "written"
    assert (workspace / "hello.txt").read_text() == "updated"


# ---------------------------------------------------------------------------
# action: rename
# ---------------------------------------------------------------------------


def test_patch_rename_renames_file(client, auth_token, workspace):
    """PATCH action:rename renames the file to new_name."""
    resp = _patch(
        client,
        workspace,
        "hello.txt",
        {"action": "rename", "new_name": "renamed.txt"},
        auth_token,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "renamed"
    assert (workspace / "renamed.txt").exists()
    assert not (workspace / "hello.txt").exists()


# ---------------------------------------------------------------------------
# action: delete
# ---------------------------------------------------------------------------


def test_patch_delete_deletes_file(client, auth_token, workspace):
    """PATCH action:delete removes the file from disk."""
    resp = _patch(client, workspace, "hello.txt", {"action": "delete"}, auth_token)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert not (workspace / "hello.txt").exists()


# ---------------------------------------------------------------------------
# action: create_dir
# ---------------------------------------------------------------------------


def test_patch_create_dir_creates_directory(client, auth_token, workspace):
    """PATCH action:create_dir creates a new directory."""
    resp = _patch(
        client, workspace, "newdir", {"action": "create_dir"}, auth_token
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    assert (workspace / "newdir").is_dir()


# ---------------------------------------------------------------------------
# path traversal
# ---------------------------------------------------------------------------


def test_patch_path_traversal_returns_400(client, auth_token):
    """Path escaping the workspace returns 400 for any action."""
    resp = client.patch(
        "/api/files//etc/passwd",
        json={"action": "read"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# authentication
# ---------------------------------------------------------------------------


def test_patch_unauthenticated_returns_401(client, workspace):
    """Request without Authorization header returns 401."""
    abs_path = str(workspace / "hello.txt")
    resp = client.patch(f"/api/files/{abs_path}", json={"action": "read"})
    assert resp.status_code == 401
