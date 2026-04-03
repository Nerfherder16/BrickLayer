import sys
import os
import pytest
import pytest_asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as sidecar_server
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def reset_state():
    """Reset module-level process state between tests."""
    sidecar_server._active_state["process"] = None
    sidecar_server._active_state["command"] = None
    yield
    # Kill any lingering process
    proc = sidecar_server._active_state.get("process")
    if proc is not None:
        try:
            proc.kill()
        except Exception:
            pass
    sidecar_server._active_state["process"] = None
    sidecar_server._active_state["command"] = None


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=sidecar_server.app), base_url="http://test"
    )


@pytest.mark.anyio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_run_valid_command_returns_event_stream(client):
    response = await client.post(
        "/run",
        json={"command": "echo", "args": ["hello"]},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.anyio
async def test_run_unknown_command_returns_400(client):
    response = await client.post(
        "/run",
        json={"command": "rm", "args": ["-rf", "/"]},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_status_idle_returns_not_active(client):
    response = await client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False
    assert data["command"] is None
