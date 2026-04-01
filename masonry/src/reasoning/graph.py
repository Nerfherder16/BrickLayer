"""Pattern co-occurrence graph — local JSON adjacency list + optional Neo4j.

CLI usage:
    python graph.py <project> <task_id> <pattern_id1> [pattern_id2 ...]

Reads:  .autopilot/pattern-confidence.json  (pattern scores, optional)
Writes: ~/.mas/pattern_graph.json           (adjacency list primary store)
        Neo4j CITES edges                   (if neo4j driver available)
"""

from __future__ import annotations

import itertools
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

try:
    from neo4j import GraphDatabase
    if TYPE_CHECKING:
        from neo4j import Driver
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False
    if TYPE_CHECKING:
        Driver = Any  # type: ignore[assignment,misc]

_DEFAULT_HTTP = "http://100.70.195.84:8200"
_DEFAULT_AUTH = ("neo4j", "password")

# Local JSON graph store
_MAS_DIR = Path.home() / ".mas"
_GRAPH_FILE = _MAS_DIR / "pattern_graph.json"


# ---------------------------------------------------------------------------
# Local JSON adjacency list helpers
# ---------------------------------------------------------------------------

def _load_local_graph() -> dict[str, dict[str, float]]:
    """Load the adjacency list from ~/.mas/pattern_graph.json."""
    if _GRAPH_FILE.exists():
        try:
            with _GRAPH_FILE.open() as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_local_graph(graph: dict[str, dict[str, float]]) -> None:
    """Write the adjacency list atomically to ~/.mas/pattern_graph.json."""
    _MAS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=_MAS_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as fh:
            json.dump(graph, fh, indent=2)
        os.replace(tmp_path, _GRAPH_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def record_local(pattern_ids: list[str]) -> int:
    """Record co-occurrence edges for *pattern_ids* in the local JSON graph.

    For each pair, increments edge weight by 1 in both directions.
    If fewer than 2 patterns, ensures each appears as a solo node.
    Returns number of edges updated.
    """
    graph = _load_local_graph()

    if len(pattern_ids) < 2:
        # Solo node — ensure it exists with no edges
        for pid in pattern_ids:
            graph.setdefault(pid, {})
        _save_local_graph(graph)
        return 0

    pairs = list(itertools.combinations(pattern_ids, 2))
    for p1, p2 in pairs:
        graph.setdefault(p1, {})
        graph.setdefault(p2, {})
        graph[p1][p2] = graph[p1].get(p2, 0.0) + 1.0
        graph[p2][p1] = graph[p2].get(p1, 0.0) + 1.0

    _save_local_graph(graph)
    return len(pairs)


# ---------------------------------------------------------------------------
# Neo4j-backed graph (optional)
# ---------------------------------------------------------------------------

def _to_bolt_uri(uri: str) -> str:
    """Convert an http:// URI to bolt://, preserving host and port."""
    if uri.startswith("http://"):
        return "bolt://" + uri[len("http://"):]
    return uri


class PatternGraph:
    """Weighted CITES graph between co-occurring patterns.

    Primary storage: ~/.mas/pattern_graph.json (always written).
    Secondary storage: Neo4j CITES edges (written only when available).
    """

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

    def record_success(self, task_id: str, pattern_ids: list[str]) -> int:
        """Record co-occurrence for *pattern_ids* from a successful task.

        Always writes to the local JSON graph. Also writes to Neo4j when
        the driver is available.

        Returns the number of edges created or updated in the local graph.
        """
        local_edges = record_local(pattern_ids)

        if self._available and self._driver is not None and len(pattern_ids) >= 2:
            pairs = list(itertools.combinations(pattern_ids, 2))
            with self._driver.session() as session:
                for p1_id, p2_id in pairs:
                    try:
                        session.execute_write(
                            self._upsert_edge, p1_id, p2_id, task_id, self.project
                        )
                    except Exception:
                        pass

        return local_edges

    def get_related(self, pattern_id: str, top_k: int = 5) -> list[str]:
        """Return up to *top_k* pattern IDs most co-cited with *pattern_id*.

        Reads from local JSON graph; falls back to Neo4j when available.
        """
        graph = _load_local_graph()
        neighbors = graph.get(pattern_id, {})
        if neighbors:
            sorted_ids = sorted(neighbors, key=lambda k: neighbors[k], reverse=True)
            return sorted_ids[:top_k]

        if self._available and self._driver is not None:
            with self._driver.session() as session:
                return session.execute_read(
                    self._query_related, pattern_id, self.project, top_k
                )

        return []

    # ------------------------------------------------------------------
    # Internal helpers
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

    @staticmethod
    def _upsert_edge(
        tx: Any,
        p1_id: str,
        p2_id: str,
        task_id: str,
        project: str,
    ) -> None:
        """MERGE a CITES edge; increment weight if it already exists."""
        tx.run(
            """
            MERGE (p1:Pattern {id: $p1_id, project: $project})
            MERGE (p2:Pattern {id: $p2_id, project: $project})
            MERGE (p1)-[r:CITES {task: $task_id}]->(p2)
            ON CREATE SET r.weight = 1
            ON MATCH  SET r.weight = r.weight + 1
            """,
            p1_id=p1_id,
            p2_id=p2_id,
            task_id=task_id,
            project=project,
        )

    @staticmethod
    def _query_related(
        tx: Any,
        pattern_id: str,
        project: str,
        top_k: int,
    ) -> list[str]:
        """Return the top-k co-cited patterns ordered by total weight."""
        result = tx.run(
            """
            MATCH (p:Pattern {id: $pattern_id, project: $project})-[r:CITES]-(other:Pattern)
            WHERE other.project = $project
            RETURN other.id AS id, sum(r.weight) AS total_weight
            ORDER BY total_weight DESC
            LIMIT $top_k
            """,
            pattern_id=pattern_id,
            project=project,
            top_k=top_k,
        )
        return [record["id"] for record in result]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(json.dumps({
            "success": False,
            "error": "Usage: graph.py <project> <task_id> [pattern_id ...]",
        }))
        sys.exit(1)

    project = sys.argv[1]
    task_id = sys.argv[2]
    pattern_ids = sys.argv[3:]

    g = PatternGraph(project=project)
    edges = g.record_success(task_id, pattern_ids)
    print(json.dumps({
        "success": True,
        "edges_recorded": edges,
        "patterns": pattern_ids,
        "graph_file": str(_GRAPH_FILE),
    }))
