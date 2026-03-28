# Requires: neo4j Python driver. Install: pip install neo4j

from __future__ import annotations

import itertools
import os
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


def _to_bolt_uri(uri: str) -> str:
    """Convert an http:// URI to bolt://, preserving host and port."""
    if uri.startswith("http://"):
        return "bolt://" + uri[len("http://"):]
    return uri


class PatternGraph:
    """Weighted CITES graph between co-occurring patterns in Neo4j.

    When a task T succeeds using patterns A, B, C — creates weighted CITES
    edges between all pairs (A→B, A→C, B→C) scoped to *project*.
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
        self._driver: Any = None  # neo4j.Driver when connected, None otherwise
        self._connect()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_success(self, task_id: str, pattern_ids: list[str]) -> int:
        """Create/increment CITES edges between all pairs in *pattern_ids*.

        Returns the number of edges created or updated. No-op if the
        Neo4j driver is unavailable.
        """
        if not self._available or self._driver is None or len(pattern_ids) < 2:
            return 0

        pairs = list(itertools.combinations(pattern_ids, 2))
        count = 0
        with self._driver.session() as session:
            for p1_id, p2_id in pairs:
                session.execute_write(
                    self._upsert_edge, p1_id, p2_id, task_id, self.project
                )
                count += 1
        return count

    def get_related(self, pattern_id: str, top_k: int = 5) -> list[str]:
        """Return up to *top_k* pattern IDs most co-cited with *pattern_id*.

        Falls back to [] if the driver is unavailable.
        """
        if not self._available or self._driver is None:
            return []

        with self._driver.session() as session:
            result: list[str] = session.execute_read(
                self._query_related, pattern_id, self.project, top_k
            )
        return result

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
