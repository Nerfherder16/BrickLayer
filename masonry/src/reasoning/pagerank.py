"""PageRank over the local pattern co-occurrence graph.

CLI usage:
    python pagerank.py <project> <confidence_json_path>

Reads:  ~/.mas/pattern_graph.json           (adjacency list from graph.py)
Writes: <confidence_json_path>              (blended confidence scores)

Blending formula: new_conf = 0.6 * existing + 0.4 * pagerank_score
Prints: "PageRank updated N patterns"
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False

_DEFAULT_HTTP = os.environ.get("RECALL_HOST", "http://localhost:8200")
_DEFAULT_AUTH = ("neo4j", "password")

# PageRank hyper-parameters
_DAMPING = 0.85
_MAX_ITER = 100
_TOL = 1e-6

# Confidence blending weights
_EXISTING_WEIGHT = 0.6
_PAGERANK_WEIGHT = 0.4

# Local graph file (shared with graph.py)
_MAS_DIR = Path.home() / ".mas"
_GRAPH_FILE = _MAS_DIR / "pattern_graph.json"


# ---------------------------------------------------------------------------
# Local JSON graph helpers
# ---------------------------------------------------------------------------

def _load_local_graph() -> dict[str, dict[str, float]]:
    """Load adjacency list from ~/.mas/pattern_graph.json."""
    if not _GRAPH_FILE.exists():
        return {}
    try:
        with _GRAPH_FILE.open() as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _adjacency_to_edge_list(
    graph: dict[str, dict[str, float]],
) -> list[tuple[str, str, float]]:
    """Convert adjacency dict to (source, target, weight) edge list.

    To avoid double-counting undirected edges, only emit (a, b) where a < b.
    """
    edges: list[tuple[str, str, float]] = []
    seen: set[tuple[str, str]] = set()
    for src, neighbors in graph.items():
        for tgt, weight in neighbors.items():
            key = (min(src, tgt), max(src, tgt))
            if key not in seen:
                seen.add(key)
                edges.append((src, tgt, weight))
    return edges


# ---------------------------------------------------------------------------
# Pure-Python PageRank (no networkx required)
# ---------------------------------------------------------------------------

def _pagerank(
    edges: list[tuple[str, str, float]],
    damping: float = _DAMPING,
    max_iter: int = _MAX_ITER,
    tol: float = _TOL,
) -> dict[str, float]:
    """Compute PageRank for a weighted undirected graph.

    *edges* is a list of (source_id, target_id, weight) tuples.
    Returns a dict of node_id -> normalized score in [0, 1].
    """
    if not edges:
        return {}

    # Build node set and out-edges (treat undirected as bidirectional)
    nodes: set[str] = set()
    out_edges: dict[str, list[tuple[str, float]]] = {}
    out_weight: dict[str, float] = {}

    for src, tgt, weight in edges:
        w = float(weight)
        nodes.add(src)
        nodes.add(tgt)
        out_edges.setdefault(src, []).append((tgt, w))
        out_edges.setdefault(tgt, []).append((src, w))
        out_weight[src] = out_weight.get(src, 0.0) + w
        out_weight[tgt] = out_weight.get(tgt, 0.0) + w

    n = len(nodes)
    rank: dict[str, float] = {node: 1.0 / n for node in nodes}

    for _ in range(max_iter):
        new_rank: dict[str, float] = {
            node: (1.0 - damping) / n for node in nodes
        }
        for src, targets in out_edges.items():
            total = out_weight.get(src, 1.0) or 1.0
            for tgt, w in targets:
                new_rank[tgt] = new_rank.get(tgt, 0.0) + damping * rank[src] * (w / total)

        # Check convergence
        delta = sum(abs(new_rank[nd] - rank[nd]) for nd in nodes)
        rank = new_rank
        if delta < tol:
            break

    # Normalize to [0, 1]
    max_score = max(rank.values()) if rank else 1.0
    if max_score > 0:
        return {nd: score / max_score for nd, score in rank.items()}
    return {nd: 0.0 for nd in rank}


# ---------------------------------------------------------------------------
# Atomic file write helper
# ---------------------------------------------------------------------------

def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Write *data* as JSON to *path* atomically via a temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run_local(confidence_path: str) -> int:
    """Run PageRank on the local JSON graph and blend into confidence scores.

    Returns the number of patterns updated.
    Exits silently (returns 0) if the graph is empty or missing.
    """
    graph = _load_local_graph()
    if not graph:
        return 0

    edges = _adjacency_to_edge_list(graph)
    if not edges:
        # Only solo nodes — no PageRank signal
        return 0

    pr_scores = _pagerank(edges)
    if not pr_scores:
        return 0

    conf_path = Path(confidence_path)
    if conf_path.exists():
        try:
            with conf_path.open() as fh:
                confidences: dict[str, float] = json.load(fh)
        except (json.JSONDecodeError, OSError):
            confidences = {}
    else:
        confidences = {}

    updated = 0
    for pattern_id, pr_score in pr_scores.items():
        existing = confidences.get(pattern_id, 0.0)
        confidences[pattern_id] = _EXISTING_WEIGHT * existing + _PAGERANK_WEIGHT * pr_score
        updated += 1

    _write_json_atomic(conf_path, confidences)
    return updated


# ---------------------------------------------------------------------------
# Neo4j-backed PageRank (optional, legacy)
# ---------------------------------------------------------------------------

def _to_bolt_uri(uri: str) -> str:
    """Convert an http:// URI to bolt://, preserving host and port."""
    if uri.startswith("http://"):
        return "bolt://" + uri[len("http://"):]
    return uri


def _pagerank_manual(
    edges: list[tuple[str, str, float]],
    damping: float = _DAMPING,
    iterations: int = _MAX_ITER,
) -> dict[str, float]:
    """Compute PageRank for a weighted directed graph (Neo4j fallback).

    Returns unnormalized scores (legacy behavior for Neo4j path).
    """
    if not edges:
        return {}

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
            for tgt, w in targets:
                new_rank[tgt] = new_rank.get(tgt, 0.0) + damping * rank[src] * (w / total)
        rank = new_rank

    return rank


class PatternPageRank:
    """Run PageRank on the pattern graph and update confidence scores.

    Primary: reads ~/.mas/pattern_graph.json (always works offline).
    Secondary: tries Neo4j GDS PageRank when driver is available.
    """

    _PAGERANK_BOOST = 0.05
    _PAGERANK_THRESHOLD = 0.5

    def __init__(
        self,
        project: str,
        uri: Optional[str] = None,
        auth: Optional[tuple[str, str]] = None,
    ) -> None:
        self.project = project
        raw_uri = uri or os.environ.get("RECALL_HOST", _DEFAULT_HTTP)
        self._uri = _to_bolt_uri(raw_uri)
        self._auth = auth or _DEFAULT_AUTH
        self._available: bool = False
        self._driver: Any = None
        self._connect()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, confidence_path: str) -> dict[str, Any]:
        """Run PageRank and update confidence scores.

        Tries Neo4j GDS first; falls back to local JSON graph.
        Returns a summary dict.
        """
        # Try Neo4j path first (legacy)
        if self._available and self._driver is not None:
            try:
                return self._run_neo4j(confidence_path)
            except Exception:
                pass

        # Primary path: local JSON graph
        updated = run_local(confidence_path)
        return {"patterns_updated": updated, "source": "local_graph"}

    # ------------------------------------------------------------------
    # Neo4j path
    # ------------------------------------------------------------------

    def _run_neo4j(self, confidence_path: str) -> dict[str, Any]:
        """Run PageRank via Neo4j and apply confidence boosts."""
        with self._driver.session() as session:
            ranks = self._run_gds_pagerank(session)

        if not ranks:
            return {"patterns_updated": 0, "highest_rank_pattern": None}

        conf_path = Path(confidence_path)
        if conf_path.exists():
            with conf_path.open() as fh:
                confidences: dict[str, float] = json.load(fh)
        else:
            confidences = {}

        updated = 0
        highest_id = max(ranks, key=lambda k: ranks[k])

        for pattern_id, rank_score in ranks.items():
            if rank_score > self._PAGERANK_THRESHOLD:
                current = confidences.get(pattern_id, 0.0)
                confidences[pattern_id] = min(1.0, current + self._PAGERANK_BOOST)
                updated += 1

        _write_json_atomic(Path(confidence_path), confidences)
        return {"patterns_updated": updated, "highest_rank_pattern": highest_id}

    def _run_gds_pagerank(self, session: Any) -> dict[str, float]:
        """Try GDS PageRank; fall back to manual implementation."""
        try:
            return session.execute_read(self._gds_query, self.project)  # type: ignore[no-any-return]
        except Exception:
            return session.execute_read(self._manual_query, self.project)  # type: ignore[no-any-return]

    @staticmethod
    def _gds_query(tx: Any, project: str) -> dict[str, float]:
        """Execute GDS pageRank.stream and return id -> score mapping."""
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
    def _manual_query(tx: Any, project: str) -> dict[str, float]:
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
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "success": False,
            "error": "Usage: pagerank.py <project> <confidence_json_path>",
        }))
        sys.exit(1)

    project_arg = sys.argv[1]
    confidence_arg = sys.argv[2]

    pr = PatternPageRank(project=project_arg)
    summary = pr.run(confidence_arg)
    print(f"PageRank updated {summary.get('patterns_updated', 0)} patterns")
    print(json.dumps(summary))
