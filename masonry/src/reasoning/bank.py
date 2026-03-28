"""
# Requirements: sqlite3 (stdlib). Optional: hnswlib-python for fast vector search.
# Install hnswlib: pip install hnswlib
# Without hnswlib, falls back to SQLite-only text search (LIKE queries).
"""

import hashlib
import sqlite3
import struct
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import hnswlib  # type: ignore[import]
    _HNSWLIB_AVAILABLE = True
except ImportError:
    _HNSWLIB_AVAILABLE = False

_EMBEDDING_DIM = 384
_HNSW_EF_CONSTRUCTION = 200
_HNSW_M = 16


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReasoningBank:
    """Persistent store for reasoning patterns with optional HNSW vector search."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".masonry" / "reasoning.db"
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._use_hnsw = _HNSWLIB_AVAILABLE
        self._hnsw_index = None
        self._hnsw_id_map: dict[int, str] = {}  # int label -> pattern_id
        self._hnsw_next_label: int = 0

        self._init_db()

        if self._use_hnsw:
            self._init_hnsw()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    content    TEXT,
                    domain     TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 0.7,
                    embedding  BLOB,
                    created_at TEXT,
                    last_used  TEXT
                )
            """)
            conn.commit()

    def _init_hnsw(self) -> None:
        self._hnsw_index = hnswlib.Index(space="cosine", dim=_EMBEDDING_DIM)
        index_path = str(self._db_path) + ".hnswlib"
        if Path(index_path).exists():
            self._load_index()
        else:
            self._hnsw_index.init_index(
                max_elements=10_000,
                ef_construction=_HNSW_EF_CONSTRUCTION,
                M=_HNSW_M,
            )
            self._hnsw_index.set_ef(50)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, pattern: dict) -> str:
        """Store a pattern and return its pattern_id."""
        pattern_id: str = pattern.get("pattern_id") or uuid.uuid4().hex
        content: str = pattern.get("content", "")
        domain: str = pattern.get("domain", "general")
        confidence: float = float(pattern.get("confidence", 0.7))
        embedding: Optional[list] = pattern.get("embedding")
        now = _now_iso()

        embedding_blob: Optional[bytes] = None
        if embedding is not None:
            embedding_blob = _floats_to_blob(embedding)

        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO patterns
                        (pattern_id, content, domain, confidence, embedding, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pattern_id) DO UPDATE SET
                        content    = excluded.content,
                        domain     = excluded.domain,
                        confidence = excluded.confidence,
                        embedding  = excluded.embedding,
                        last_used  = excluded.last_used
                    """,
                    (pattern_id, content, domain, confidence, embedding_blob, now, now),
                )
                conn.commit()

            if self._use_hnsw and embedding is not None and self._hnsw_index is not None:
                import numpy as np  # type: ignore[import]
                vec = np.array(embedding, dtype="float32").reshape(1, -1)
                label = self._hnsw_next_label
                self._hnsw_next_label += 1
                self._hnsw_id_map[label] = pattern_id
                self._hnsw_index.add_items(vec, [label])
                self._save_index()

        return pattern_id

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Return up to top_k patterns matching text, ordered by confidence desc."""
        if self._use_hnsw and self._hnsw_index is not None and self._hnsw_index.get_current_count() > 0:
            return self._query_hnsw(text, top_k)
        return self._query_sqlite(text, top_k)

    # ------------------------------------------------------------------
    # Private query methods
    # ------------------------------------------------------------------

    def _query_hnsw(self, text: str, top_k: int) -> list[dict]:
        import numpy as np  # type: ignore[import]
        embedding = self._text_to_embedding(text)
        vec = np.array(embedding, dtype="float32").reshape(1, -1)
        k = min(top_k, self._hnsw_index.get_current_count())
        labels, _ = self._hnsw_index.knn_query(vec, k=k)
        pattern_ids = [self._hnsw_id_map[label] for label in labels[0] if label in self._hnsw_id_map]
        if not pattern_ids:
            return []
        placeholders = ",".join("?" * len(pattern_ids))
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM patterns WHERE pattern_id IN ({placeholders}) ORDER BY confidence DESC",
                pattern_ids,
            ).fetchall()
        return [dict(row) for row in rows]

    def _query_sqlite(self, text: str, top_k: int) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM patterns WHERE content LIKE ? ORDER BY confidence DESC LIMIT ?",
                (f"%{text}%", top_k),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Embedding stub
    # ------------------------------------------------------------------

    def _text_to_embedding(self, text: str) -> list[float]:
        # TODO: replace with a real embedding model (e.g. sentence-transformers all-MiniLM-L6-v2)
        # This is a repeatable hash-based stub that produces 384 floats in [-1, 1].
        digest = hashlib.sha512(text.encode("utf-8")).digest()  # 64 bytes
        # Tile digest to fill 384 floats (384 * 4 = 1536 bytes needed; tile digest)
        repetitions = (_EMBEDDING_DIM * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repetitions)[: _EMBEDDING_DIM * 4]
        values = struct.unpack(f"{_EMBEDDING_DIM}f", raw)
        # Normalise to [-1, 1] by mapping uint range to float range
        max_abs = max(abs(v) for v in values) or 1.0
        return [v / max_abs for v in values]

    # ------------------------------------------------------------------
    # HNSW persistence
    # ------------------------------------------------------------------

    def _save_index(self) -> None:
        if self._hnsw_index is None:
            return
        index_path = str(self._db_path) + ".hnswlib"
        self._hnsw_index.save_index(index_path)

    def _load_index(self) -> None:
        if self._hnsw_index is None:
            return
        index_path = str(self._db_path) + ".hnswlib"
        self._hnsw_index.load_index(index_path, max_elements=10_000)
        self._hnsw_index.set_ef(50)
        # Rebuild id_map from DB
        with self._get_conn() as conn:
            rows = conn.execute("SELECT pattern_id FROM patterns").fetchall()
        # Labels are assigned in insertion order; reconstruct mapping
        for i, row in enumerate(rows):
            self._hnsw_id_map[i] = row["pattern_id"]
        self._hnsw_next_label = len(rows)


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _floats_to_blob(floats: list) -> bytes:
    return struct.pack(f"{len(floats)}f", *[float(v) for v in floats])
