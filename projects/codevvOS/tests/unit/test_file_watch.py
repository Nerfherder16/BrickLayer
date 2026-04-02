"""Unit tests for GET /api/files/watch SSE endpoint."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.auth import create_jwt


@pytest.fixture()
def workspace(tmp_path):
    """Real temp workspace with files."""
    (tmp_path / "README.md").write_text("hello")
    (tmp_path / "src").mkdir()
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


def test_watch_returns_sse_stream(client, auth_token, workspace):
    """GET /api/files/watch with valid auth returns 200 with text/event-stream."""
    with client.stream(
        "GET",
        f"/api/files/watch?path={workspace}",
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]


def test_watch_unauthenticated_returns_401(client, workspace):
    """GET /api/files/watch without auth returns 401."""
    resp = client.get(f"/api/files/watch?path={workspace}")
    assert resp.status_code == 401


def test_watch_references_watchfiles():
    """watchfiles is referenced in the files module (imported or referenced)."""
    import inspect

    import backend.app.api.files as files_module

    source = inspect.getsource(files_module)
    assert "watchfiles" in source
