"""
Phase 5 Integration Smoke Tests — Graduation gate for Phase 5 API surface.

Tests all 5 Phase 5 endpoints using the FastAPI ASGI transport (no live server).
External dependencies (LLM, Neo4j, Recall) are mocked.

Tests:
  1. POST /api/ai/inline-edit with valid body → 200 text/event-stream
  2. POST /api/artifacts/compile with valid JSX → 200 with compiled/error field
  3. GET /api/graph/nodes → 200 with list
  4. POST /api/graph/nodes with valid body → 201
  5. GET /api/artifacts/history → 200 with list
  6. All 5 endpoints are registered in the FastAPI app
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio  # noqa: F401 — needed for anyio mode detection
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    from backend.app.main import app as fastapi_app  # noqa: PLC0415

    return fastapi_app


# ---------------------------------------------------------------------------
# 1. POST /api/ai/inline-edit → 200 text/event-stream (mock LLM)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_inline_edit_returns_event_stream(app) -> None:
    """POST /api/ai/inline-edit with valid body returns 200 text/event-stream."""

    async def _mock_stream(*_args: object, **_kwargs: object) -> AsyncIterator[str]:
        yield "corrected code"

    with patch(
        "backend.app.services.llm_service.stream_inline_edit",
        side_effect=_mock_stream,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/ai/inline-edit",
                json={
                    "prompt": "fix the bug",
                    "document": "const x = 1",
                    "language": "typescript",
                },
            )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# 2. POST /api/artifacts/compile with valid JSX → 200 with compiled/error field
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_compile_artifact_returns_compiled_or_error(app) -> None:
    """POST /api/artifacts/compile returns 200 with compiled or error field."""
    with patch(
        "backend.app.api.artifacts.compile_jsx",
        new_callable=AsyncMock,
        return_value=("React.createElement('div', null, 'hello')", None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/artifacts/compile",
                json={"jsx": "<div>hello</div>", "dependencies": []},
            )
    assert response.status_code == 200
    body = response.json()
    # Response must have exactly the compiled or error field
    assert "compiled" in body or "error" in body


# ---------------------------------------------------------------------------
# 3. GET /api/graph/nodes → 200 with list (mock Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_graph_nodes_returns_list(app) -> None:
    """GET /api/graph/nodes returns 200 with a list."""
    with patch(
        "backend.app.api.graph.neo4j_client.get_nodes",
        new_callable=AsyncMock,
        return_value=[{"id": "node-1", "node_type": "Decision", "title": "Use Neo4j"}],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/graph/nodes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# 4. POST /api/graph/nodes → 201 (mock Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_graph_node_returns_201(app) -> None:
    """POST /api/graph/nodes with valid body returns 201."""
    with patch(
        "backend.app.api.graph.neo4j_client.create_node",
        new_callable=AsyncMock,
        return_value="node-new-123",
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/graph/nodes",
                json={
                    "node_type": "Decision",
                    "title": "Choose database",
                    "properties": {},
                },
            )
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# 5. GET /api/artifacts/history → 200 with list (mock Recall)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_artifact_history_returns_list(app) -> None:
    """GET /api/artifacts/history returns 200 with a list."""
    with patch(
        "backend.app.api.artifacts.recall_client.get_artifact_history",
        new_callable=AsyncMock,
        return_value=[],
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/artifacts/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# 6. All 5 endpoints are registered in the FastAPI app
# ---------------------------------------------------------------------------


def test_all_phase5_endpoints_are_registered(app) -> None:
    """All 5 Phase 5 endpoints are registered in the FastAPI app routes."""
    route_patterns = {(r.path, m) for r in app.routes for m in getattr(r, "methods", set())}

    assert ("/api/ai/inline-edit", "POST") in route_patterns, (
        "POST /api/ai/inline-edit not registered"
    )
    assert ("/api/artifacts/compile", "POST") in route_patterns, (
        "POST /api/artifacts/compile not registered"
    )
    assert ("/api/graph/nodes", "GET") in route_patterns, (
        "GET /api/graph/nodes not registered"
    )
    assert ("/api/graph/nodes", "POST") in route_patterns, (
        "POST /api/graph/nodes not registered"
    )
    assert ("/api/artifacts/history", "GET") in route_patterns, (
        "GET /api/artifacts/history not registered"
    )
