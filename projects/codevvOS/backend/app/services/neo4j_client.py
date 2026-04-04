"""Neo4j async client — wraps the neo4j Python driver for knowledge graph operations."""
from __future__ import annotations

import os

from neo4j import AsyncGraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "codevvos")

VALID_NODE_TYPES: frozenset[str] = frozenset({"Decision", "Assumption", "Evidence", "CodeFile"})
VALID_EDGE_TYPES: frozenset[str] = frozenset({"BASED_ON", "CONTRADICTS", "SUPPORTS", "REFERENCES"})


class Neo4jClient:
    """Async Neo4j client used as a FastAPI lifespan singleton."""

    def __init__(self) -> None:
        self._driver = None

    async def connect(self) -> None:
        self._driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()

    async def get_nodes(self) -> list[dict]:
        """Return all nodes as plain dicts."""
        async with self._driver.session() as session:
            result = await session.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props")
            return [
                {"id": r["id"], "labels": r["labels"], **r["props"]}
                async for r in result
            ]

    async def create_node(self, node_type: str, properties: dict) -> str:
        """Create a node and return its element ID."""
        async with self._driver.session() as session:
            result = await session.run(
                f"CREATE (n:{node_type} $props) RETURN elementId(n) AS id",
                props=properties,
            )
            record = await result.single()
            return record["id"]

    async def create_edge(self, from_id: str, to_id: str, edge_type: str) -> bool:
        """Create a relationship between two nodes. Returns True on success."""
        async with self._driver.session() as session:
            await session.run(
                f"MATCH (a) WHERE elementId(a) = $from_id "
                f"MATCH (b) WHERE elementId(b) = $to_id "
                f"CREATE (a)-[:{edge_type}]->(b)",
                from_id=from_id,
                to_id=to_id,
            )
        return True

    async def get_neighborhood(self, node_id: str, hops: int = 2) -> dict:
        """Return a node and all nodes/edges within `hops` hops."""
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (n) WHERE elementId(n) = $node_id "
                "OPTIONAL MATCH path = (n)-[*1..$hops]-(neighbor) "
                "RETURN n, collect(DISTINCT neighbor) AS neighbors, "
                "       collect(DISTINCT relationships(path)) AS rels",
                node_id=node_id,
                hops=hops,
            )
            record = await result.single()
            if record is None:
                return {}
            root = dict(record["n"])
            root["id"] = node_id
            neighbors = [
                {"id": nb.element_id, "labels": list(nb.labels), **dict(nb)}
                for nb in (record["neighbors"] or [])
                if nb is not None
            ]
            return {"node": root, "neighbors": neighbors}

    async def get_decisions(self) -> list[dict]:
        """Return all Decision nodes."""
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (n:Decision) RETURN elementId(n) AS id, properties(n) AS props"
            )
            return [{"id": r["id"], **r["props"]} async for r in result]


# Singleton used by FastAPI lifespan and route handlers
neo4j_client = Neo4jClient()
