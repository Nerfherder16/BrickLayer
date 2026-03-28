# Requires: neo4j Python driver. Install: pip install neo4j

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from neo4j import GraphDatabase  # type: ignore[import-untyped]
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False

_DEFAULT_HTTP = "http://100.70.195.84:8200"
_DEFAULT_AUTH = ("neo4j", "password")
_PAGERANK_BOOST = 0.05
_PAGERANK_THRESHOLD = 0.5
_DAMPING = 0.85
_ITERATIONS = 20


def _to_bolt_uri(uri: str) -> str:
    """Convert an http:// URI to bolt://, preserving host and port."""
    if uri.startswith("http://"):
        return "bolt://" + uri[len("http://"):]
    return uri


class PatternPageRank:
    """Run PageRank on the CITES graph and update pattern confidence scores."""

    def __init__(
        self,
        project: str,
        uri: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> None:
        self.project = project
        raw_uri = uri or os.environ.get("RECALL_HOST", _DEFAULT_HTTP)
        self._uri = _to_bolt_uri(raw_uri)
        self._auth = auth or _DEFAULT_AUTH
        self._available = False
        self._driver = None
        self._connect()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, confidence_path: str) -> dict:
        """Run PageRank and apply confidence boosts to patterns with rank > 0.5.

        Reads *confidence_path* (a JSON dict mapping pattern_id → confidence
        float), applies +0.05 to patterns whose PageRank score exceeds 0.5
        (capped at 1.0), then writes the updated dict back.

        Returns a summary dict. If unavailable, returns
        ``{skipped: True, reason: "neo4j unavailable"}``.
        """
        if not self._available:
            return {"skipped": True, "reason": "neo4j unavailable"}

        with self._driver.session() as session:
            ranks = self._run_gds_pagerank(session)

        if not ranks:
            return {"patterns_updated": 0, "highest_rank_pattern": None}

        path = Path(confidence_path)
        if path.exists():
            with path.open() as fh:
                confidences: dict[str, float] = json.load(fh)
        else:
            confidences = {}

        updated = 0
        highest_id = max(ranks, key=lambda k: ranks[k])

        for pattern_id, rank_score in ranks.items():
            if rank_score > _PAGERANK_THRESHOLD:
                current = confidences.get(pattern_id, 0.0)
                confidences[pattern_id] = min(1.0, current + _PAGERANK_BOOST)
                updated += 1

        with path.open("w") as fh:
            json.dump(confidences, fh, indent=2)

        return {"patterns_updated": updated, "highest_rank_pattern": highest_id}

    # ------------------------------------------------------------------
    # PageRank strategies
    # ------------------------------------------------------------------

    def _run_gds_pagerank(self, session) -> dict[str, float]:
        """Try GDS PageRank; fall back to manual implementation."""
        try:
            return session.execute_read(self._gds_query, self.project)
        except Exception:
            return session.execute_read(self._manual_query, self.project)

    @staticmethod
    def _gds_query(tx, project: str) -> dict[str, float]:
        """Execute GDS pageRank.stream and return id → score mapping."""
        result = tx.run(
            """
            CALL gds.pageRank.stream({
                nodeQuery: 'MATCH (p:Pattern {project: $project}) RETURN id(p) AS id',
                relationshipQuery: 'MATCH (p1:Pattern {project: $project})-[r:CITES]->(p2:Pattern {project: $project}) RETURN id(p1) AS source, id(p2) AS target, r.weight AS weight',
                relationshipWeightProperty: 'weight'
            })
            YIELD nodeId, score
            WITH gds.util.asNode(nodeId) AS node, score
            RETURN node.id AS pattern_id, score
            """,
            project=project,
        )
        return {record["pattern_id"]: record["score"] for record in result}

    @staticmethod
    def _manual_query(tx, project: str) -> dict[str, float]:
        """Fetch all CITES edges and compute PageRank manually."""
        result = tx.run(
            """
            MATCH (p1:Pattern {project: $project})-[r:CITES]->(p2:Pattern {project: $project})
            RETURN p1.id AS source, p2.id AS target, r.weight AS weight
            """,
            project=project,
        )
        edges = [(rec["source"], rec["target"], rec["weight"]) for rec in result]
        return _pagerank_manual(edges)

    def _run_manual_pagerank(self, session) -> dict[str, float]:
        """Public fallback entry point for manual PageRank."""
        return session.execute_read(self._manual_query, self.project)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        """Create the Neo4j driver and verify connectivity."""
        if not _NEO4J_AVAILABLE:
            return
        try:
            driver = GraphDatabase.driver(self._uri, auth=self._auth)
            driver.verify_connectivity()
            self._driver = driver
            self._available = True
        except Exception:
            self._available = False


# ---------------------------------------------------------------------------
# Pure-Python PageRank helper (no Neo4j GDS required)
# ---------------------------------------------------------------------------

def _pagerank_manual(
    edges: list[tuple[str, str, float]],
    damping: float = _DAMPING,
    iterations: int = _ITERATIONS,
) -> dict[str, float]:
    """Compute PageRank for a weighted directed graph.

    *edges* is a list of (source_id, target_id, weight) tuples.
    Returns a dict of node_id → rank score (not normalised).
    """
    if not edges:
        return {}

    # Collect all nodes and build out-edge adjacency
    nodes: set[str] = set()
    out_edges: dict[str, list[tuple[str, float]]] = {}
    out_weight: dict[str, float] = {}

    for src, tgt, weight in edges:
        nodes.add(src)
        nodes.add(tgt)
        out_edges.setdefault(src, []).append((tgt, float(weight)))
        out_weight[src] = out_weight.get(src, 0.0) + float(weight)

    n = len(nodes)
    rank: dict[str, float] = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_rank: dict[str, float] = {node: (1.0 - damping) / n for node in nodes}
        for src, targets in out_edges.items():
            total = out_weight.get(src, 1.0) or 1.0
            for tgt, weight in targets:
                new_rank[tgt] = new_rank.get(tgt, 0.0) + damping * rank[src] * (weight / total)
        rank = new_rank

    return rank


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Usage: python pagerank.py <project> <confidence_json_path>
    if len(sys.argv) < 3:
        print("Usage: python pagerank.py <project> <confidence_json_path>", file=sys.stderr)
        sys.exit(1)

    project_arg = sys.argv[1]
    confidence_arg = sys.argv[2]

    pr = PatternPageRank(project=project_arg)
    summary = pr.run(confidence_arg)
    print(json.dumps(summary, indent=2))
