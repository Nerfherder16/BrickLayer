"""Unit tests for /api/graph/ endpoints — mocks neo4j_client entirely."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def mock_client():
    with patch("backend.app.api.graph.neo4j_client") as mock:
        mock.get_nodes = AsyncMock(return_value=[])
        mock.create_node = AsyncMock(return_value="node-123")
        mock.create_edge = AsyncMock(return_value=True)
        mock.get_neighborhood = AsyncMock(
            return_value={"node": {"id": "node-123", "title": "Root"}, "neighbors": []}
        )
        mock.get_decisions = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def client(mock_client):
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/graph/nodes
# ---------------------------------------------------------------------------

def test_get_nodes_returns_empty_list(client):
    resp = client.get("/api/graph/nodes")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /api/graph/nodes
# ---------------------------------------------------------------------------

def test_create_node_returns_id(client, mock_client):
    resp = client.post(
        "/api/graph/nodes",
        json={"node_type": "Decision", "title": "Use Neo4j", "properties": {}},
    )
    assert resp.status_code == 201
    assert resp.json() == {"id": "node-123"}
    mock_client.create_node.assert_awaited_once()


def test_create_node_invalid_type_returns_400(client):
    resp = client.post(
        "/api/graph/nodes",
        json={"node_type": "BadType", "title": "oops"},
    )
    assert resp.status_code == 400
    assert "Invalid node_type" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/graph/edges
# ---------------------------------------------------------------------------

def test_create_edge_returns_created(client, mock_client):
    resp = client.post(
        "/api/graph/edges",
        json={"from_id": "node-1", "to_id": "node-2", "edge_type": "SUPPORTS"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"created": True}
    mock_client.create_edge.assert_awaited_once_with("node-1", "node-2", "SUPPORTS")


# ---------------------------------------------------------------------------
# GET /api/graph/neighborhood/{id}
# ---------------------------------------------------------------------------

def test_get_neighborhood_returns_node_and_neighbors(client):
    resp = client.get("/api/graph/neighborhood/node-123")
    assert resp.status_code == 200
    data = resp.json()
    assert "node" in data
    assert "neighbors" in data


def test_get_neighborhood_not_found_returns_404(client, mock_client):
    mock_client.get_neighborhood = AsyncMock(return_value={})
    resp = client.get("/api/graph/neighborhood/missing-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/graph/decisions
# ---------------------------------------------------------------------------

def test_get_decisions_returns_empty_list(client):
    resp = client.get("/api/graph/decisions")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Neo4j connection error → 503
# ---------------------------------------------------------------------------

def test_create_node_neo4j_error_returns_503(mock_client):
    mock_client.create_node = AsyncMock(side_effect=Exception("Connection refused"))
    with TestClient(app) as c:
        resp = c.post(
            "/api/graph/nodes",
            json={"node_type": "Decision", "title": "Fail"},
        )
    assert resp.status_code == 503
    assert "Neo4j unavailable" in resp.json()["detail"]
