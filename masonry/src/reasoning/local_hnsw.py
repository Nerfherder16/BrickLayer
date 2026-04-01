"""
Local HNSW vector store — fallback when Qdrant is unavailable.
Uses hnswlib if installed, otherwise falls back to brute-force cosine similarity with numpy.
Persists to ~/.mas/reasoning_bank/ as .npy + .json index files.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import hnswlib  # type: ignore[import]
    _HNSWLIB_AVAILABLE = True
except ImportError:
    _HNSWLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

_DEFAULT_STORE_DIR = Path.home() / ".mas" / "reasoning_bank"
_VECTORS_FILE = "vectors.npy"
_INDEX_FILE = "index.json"
_HNSW_FILE = "hnsw.bin"
_EMBEDDING_DIM = 384
_HNSW_EF_CONSTRUCTION = 200
_HNSW_M = 16
_HNSW_MAX_ELEMENTS = 10_000


class LocalHNSW:
    """
    Local vector store with optional hnswlib acceleration.

    When hnswlib is available, uses an HNSW index for fast approximate nearest neighbour
    search. When it is not available, falls back to exact brute-force cosine similarity
    using numpy (always installed).

    All data is persisted to *store_dir* between process restarts.
    """

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        self._store_dir = Path(store_dir) if store_dir is not None else _DEFAULT_STORE_DIR
        self._store_dir.mkdir(parents=True, exist_ok=True)

        # In-memory structures (always kept in sync with disk)
        self._vectors: list[list[float]] = []       # one vector per entry (insertion order)
        self._ids: list[str] = []                   # pattern_id per entry
        self._meta: list[dict] = []                 # metadata per entry
        self._id_to_idx: dict[str, int] = {}        # pattern_id -> index in above lists
        self._deleted: set[str] = set()             # soft-deleted ids

        self._hnsw_index = None

        self._load_from_disk()

        if _HNSWLIB_AVAILABLE:
            self._init_hnsw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, pattern_id: str, text: str, vector: list[float], metadata: dict) -> None:
        """Persist a vector with associated metadata."""
        if pattern_id in self._id_to_idx:
            # Update existing entry in-place
            idx = self._id_to_idx[pattern_id]
            self._vectors[idx] = list(vector)
            self._meta[idx] = dict(metadata)
            self._deleted.discard(pattern_id)
        else:
            idx = len(self._ids)
            self._ids.append(pattern_id)
            self._vectors.append(list(vector))
            self._meta.append(dict(metadata))
            self._id_to_idx[pattern_id] = idx
            self._deleted.discard(pattern_id)

            if _HNSWLIB_AVAILABLE and self._hnsw_index is not None:
                vec = np.array(vector, dtype="float32").reshape(1, -1)
                self._hnsw_index.add_items(vec, [idx])

        self._save_to_disk()

    def query(self, vector: list[float], top_k: int = 5) -> list[dict]:
        """
        Return up to *top_k* entries ordered by descending cosine similarity.

        Each result is a dict with keys: pattern_id, score, metadata.
        Soft-deleted entries are excluded.
        """
        active_indices = [i for i, pid in enumerate(self._ids) if pid not in self._deleted]
        if not active_indices:
            return []

        top_k = min(top_k, len(active_indices))

        if _HNSWLIB_AVAILABLE and self._hnsw_index is not None and self._hnsw_index.get_current_count() > 0:
            return self._query_hnsw(vector, top_k)

        return self._query_brute_force(vector, active_indices, top_k)

    def count(self) -> int:
        """Return the number of non-deleted entries."""
        return len(self._ids) - len(self._deleted)

    def delete(self, pattern_id: str) -> bool:
        """Soft-delete an entry by pattern_id. Returns True if found, False otherwise."""
        if pattern_id in self._id_to_idx and pattern_id not in self._deleted:
            self._deleted.add(pattern_id)
            self._save_to_disk()
            return True
        return False

    # ------------------------------------------------------------------
    # Internal query implementations
    # ------------------------------------------------------------------

    def _query_hnsw(self, vector: list[float], top_k: int) -> list[dict]:
        vec = np.array(vector, dtype="float32").reshape(1, -1)
        # Request more than needed to compensate for deleted items
        k = min(top_k * 2, self._hnsw_index.get_current_count())
        k = max(k, top_k)
        labels, distances = self._hnsw_index.knn_query(vec, k=k)
        results: list[dict] = []
        for label, distance in zip(labels[0], distances[0]):
            label = int(label)
            if label >= len(self._ids):
                continue
            pid = self._ids[label]
            if pid in self._deleted:
                continue
            # hnswlib cosine distance = 1 - cosine_similarity
            score = float(1.0 - distance)
            results.append({
                "pattern_id": pid,
                "score": score,
                "metadata": dict(self._meta[label]),
            })
            if len(results) >= top_k:
                break
        return results

    def _query_brute_force(self, vector: list[float], active_indices: list[int], top_k: int) -> list[dict]:
        query_vec = np.array(vector, dtype="float32")
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0.0:
            query_norm = 1.0
        query_vec = query_vec / query_norm

        active_vecs = np.array([self._vectors[i] for i in active_indices], dtype="float32")
        norms = np.linalg.norm(active_vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        active_vecs = active_vecs / norms

        scores = active_vecs @ query_vec  # cosine similarities
        # Sort descending
        order = np.argsort(-scores)[:top_k]

        results: list[dict] = []
        for rank_idx in order:
            global_idx = active_indices[rank_idx]
            pid = self._ids[global_idx]
            results.append({
                "pattern_id": pid,
                "score": float(scores[rank_idx]),
                "metadata": dict(self._meta[global_idx]),
            })
        return results

    # ------------------------------------------------------------------
    # hnswlib lifecycle
    # ------------------------------------------------------------------

    def _init_hnsw(self) -> None:
        hnsw_path = self._store_dir / _HNSW_FILE
        self._hnsw_index = hnswlib.Index(space="cosine", dim=_EMBEDDING_DIM)  # type: ignore[name-defined]
        if hnsw_path.exists() and len(self._ids) > 0:
            self._hnsw_index.load_index(str(hnsw_path), max_elements=_HNSW_MAX_ELEMENTS)
            self._hnsw_index.set_ef(50)
        else:
            self._hnsw_index.init_index(
                max_elements=_HNSW_MAX_ELEMENTS,
                ef_construction=_HNSW_EF_CONSTRUCTION,
                M=_HNSW_M,
            )
            self._hnsw_index.set_ef(50)
            # Re-add all active vectors from restored state
            for idx, pid in enumerate(self._ids):
                if pid not in self._deleted and idx < len(self._vectors):
                    vec = np.array(self._vectors[idx], dtype="float32").reshape(1, -1)
                    self._hnsw_index.add_items(vec, [idx])

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_to_disk(self) -> None:
        vectors_path = self._store_dir / _VECTORS_FILE
        index_path = self._store_dir / _INDEX_FILE

        if self._vectors:
            np.save(str(vectors_path), np.array(self._vectors, dtype="float32"))
        else:
            # Write empty placeholder
            np.save(str(vectors_path), np.zeros((0, _EMBEDDING_DIM), dtype="float32"))

        index_data = {
            "ids": self._ids,
            "meta": self._meta,
            "deleted": list(self._deleted),
        }
        index_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

        if _HNSWLIB_AVAILABLE and self._hnsw_index is not None:
            hnsw_path = self._store_dir / _HNSW_FILE
            self._hnsw_index.save_index(str(hnsw_path))

    def _load_from_disk(self) -> None:
        vectors_path = self._store_dir / _VECTORS_FILE
        index_path = self._store_dir / _INDEX_FILE

        if not index_path.exists():
            return

        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            self._ids = index_data.get("ids", [])
            self._meta = index_data.get("meta", [])
            self._deleted = set(index_data.get("deleted", []))
            self._id_to_idx = {pid: i for i, pid in enumerate(self._ids)}
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            logger.warning("LocalHNSW: could not load index.json — starting fresh: %s", exc)
            return

        if vectors_path.exists() and self._ids:
            try:
                arr = np.load(str(vectors_path))
                self._vectors = arr.tolist()
            except (OSError, ValueError) as exc:
                logger.warning("LocalHNSW: could not load vectors.npy — starting fresh: %s", exc)
                self._ids = []
                self._meta = []
                self._deleted = set()
                self._id_to_idx = {}
