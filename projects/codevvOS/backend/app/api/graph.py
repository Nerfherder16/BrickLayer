"""Knowledge graph CRUD endpoints — /api/graph/."""
from __future__ import annotations

from backend.app.services.neo4j_client import VALID_NODE_TYPES, neo4j_client
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class NodeCreate(BaseModel):
    node_type: str
    title: str
    properties: dict = {}


class EdgeCreate(BaseModel):
    from_id: str
    to_id: str
    edge_type: str


@router.get("/nodes")
async def get_nodes() -> list[dict]:
    """Return all graph nodes."""
    try:
        return await neo4j_client.get_nodes()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j unavailable") from exc


@router.post("/nodes", status_code=201)
async def create_node(body: NodeCreate) -> dict:
    """Create a new node. node_type must be one of the four canonical types."""
    if body.node_type not in VALID_NODE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid node_type '{body.node_type}'. Must be one of {sorted(VALID_NODE_TYPES)}",
        )
    props = {"title": body.title, **body.properties}
    try:
        node_id = await neo4j_client.create_node(body.node_type, props)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j unavailable") from exc
    return {"id": node_id}


@router.post("/edges", status_code=201)
async def create_edge(body: EdgeCreate) -> dict:
    """Create a directed relationship between two existing nodes."""
    try:
        await neo4j_client.create_edge(body.from_id, body.to_id, body.edge_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j unavailable") from exc
    return {"created": True}


@router.get("/neighborhood/{node_id}")
async def get_neighborhood(node_id: str) -> dict:
    """Return a node and its 2-hop neighborhood."""
    try:
        result = await neo4j_client.get_neighborhood(node_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j unavailable") from exc
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.get("/decisions")
async def get_decisions() -> list[dict]:
    """Return all Decision nodes."""
    try:
        return await neo4j_client.get_decisions()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j unavailable") from exc
