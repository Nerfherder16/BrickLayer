"""Unit tests for artifact persistence endpoints and recall_client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client() -> TestClient:
    from backend.app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# POST /api/artifacts/persist
# ---------------------------------------------------------------------------


def test_persist_calls_recall_and_returns_id() -> None:
    """Persist endpoint calls recall_client and returns the memory ID."""
    with patch(
        "backend.app.api.artifacts.recall_client.persist_artifact",
        new_callable=AsyncMock,
        return_value="mem-abc123",
    ) as mock_persist:
        client = _make_client()
        response = client.post(
            "/api/artifacts/persist",
            json={
                "artifact_id": "art-1",
                "title": "My Artifact",
                "jsx": "<div>hello</div>",
                "compiled": "React.createElement('div', null, 'hello')",
            },
        )
    assert response.status_code == 200
    assert response.json() == {"id": "mem-abc123"}
    mock_persist.assert_awaited_once_with(
        "art-1",
        "My Artifact",
        "<div>hello</div>",
        "React.createElement('div', null, 'hello')",
    )


def test_persist_with_null_compiled() -> None:
    """Persist endpoint accepts compiled=None."""
    with patch(
        "backend.app.api.artifacts.recall_client.persist_artifact",
        new_callable=AsyncMock,
        return_value="mem-xyz",
    ) as mock_persist:
        client = _make_client()
        response = client.post(
            "/api/artifacts/persist",
            json={
                "artifact_id": "art-2",
                "title": "Uncompiled",
                "jsx": "<span/>",
                "compiled": None,
            },
        )
    assert response.status_code == 200
    assert response.json()["id"] == "mem-xyz"
    mock_persist.assert_awaited_once_with("art-2", "Uncompiled", "<span/>", None)


def test_persist_missing_required_field_returns_422() -> None:
    """Persist endpoint validates required fields."""
    client = _make_client()
    response = client.post(
        "/api/artifacts/persist",
        json={"title": "Missing artifact_id and jsx"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/artifacts/history
# ---------------------------------------------------------------------------


def test_history_returns_list_sorted_by_timestamp_desc() -> None:
    """History endpoint returns list from recall_client (already sorted)."""
    fake_history = [
        {"id": "m2", "timestamp": "2024-02-01T00:00:00Z", "metadata": {"title": "B"}},
        {"id": "m1", "timestamp": "2024-01-01T00:00:00Z", "metadata": {"title": "A"}},
    ]
    with patch(
        "backend.app.api.artifacts.recall_client.get_artifact_history",
        new_callable=AsyncMock,
        return_value=fake_history,
    ):
        client = _make_client()
        response = client.get("/api/artifacts/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "m2"
    assert data[1]["id"] == "m1"


def test_history_returns_empty_list_when_recall_unavailable() -> None:
    """History endpoint returns [] (not 503) when Recall connection fails."""
    with patch(
        "backend.app.api.artifacts.recall_client.get_artifact_history",
        new_callable=AsyncMock,
        return_value=[],
    ):
        client = _make_client()
        response = client.get("/api/artifacts/history")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# recall_client unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recall_client_persist_artifact_posts_to_recall() -> None:
    """persist_artifact POSTs to RECALL_BASE_URL/memory and returns id."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"id": "recall-id-1"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("backend.app.services.recall_client.httpx.AsyncClient", return_value=mock_client):
        from backend.app.services.recall_client import persist_artifact  # noqa: PLC0415

        result = await persist_artifact("art-1", "Title", "<div/>", "compiled")

    assert result == "recall-id-1"
    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args
    assert "/memory" in call_kwargs.args[0]


@pytest.mark.asyncio
async def test_recall_client_get_artifact_history_returns_empty_on_error() -> None:
    """get_artifact_history returns [] when Recall is unreachable."""
    with patch(
        "backend.app.services.recall_client.httpx.AsyncClient",
        side_effect=Exception("Connection refused"),
    ):
        from backend.app.services.recall_client import get_artifact_history  # noqa: PLC0415

        result = await get_artifact_history()

    assert result == []


@pytest.mark.asyncio
async def test_recall_client_get_artifact_history_sorts_desc() -> None:
    """get_artifact_history sorts items by timestamp descending."""
    items = [
        {"id": "a", "timestamp": "2024-01-01T00:00:00Z"},
        {"id": "c", "timestamp": "2024-03-01T00:00:00Z"},
        {"id": "b", "timestamp": "2024-02-01T00:00:00Z"},
    ]
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = items

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("backend.app.services.recall_client.httpx.AsyncClient", return_value=mock_client):
        from backend.app.services.recall_client import get_artifact_history  # noqa: PLC0415

        result = await get_artifact_history()

    assert [r["id"] for r in result] == ["c", "b", "a"]
