"""
Tests for LocalHNSW — local vector store fallback.

Run: python masonry/src/reasoning/test_local_hnsw.py
Expected: exits 0 with all tests passing.
"""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

# Ensure repo root is on sys.path so `masonry` package is importable
# regardless of the working directory when this script is invoked.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _make_store(tmp_dir: Path):
    from masonry.src.reasoning.local_hnsw import LocalHNSW
    return LocalHNSW(store_dir=tmp_dir)


def _vec(seed: int, dim: int = 384) -> list[float]:
    """Return a reproducible non-zero unit-ish vector."""
    import math
    values = [math.sin(seed * 0.1 + i * 0.07) for i in range(dim)]
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def test_store_and_query_top_k() -> None:
    """Store 3 vectors, query top-2, verify returned IDs are in the stored set."""
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store(Path(tmp))

        ids = [uuid.uuid4().hex for _ in range(3)]
        for i, pid in enumerate(ids):
            store.store(
                pattern_id=pid,
                text=f"pattern {i}",
                vector=_vec(i),
                metadata={"index": i},
            )

        assert store.count() == 3, f"Expected 3, got {store.count()}"

        # Query with the first vector — should surface at least those 2 closest
        results = store.query(vector=_vec(0), top_k=2)
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"

        returned_ids = {r["pattern_id"] for r in results}
        assert returned_ids.issubset(set(ids)), f"Unexpected IDs in results: {returned_ids - set(ids)}"

        for r in results:
            assert "score" in r, "Result missing 'score'"
            assert "metadata" in r, "Result missing 'metadata'"

    print("PASS test_store_and_query_top_k")


def test_delete_reduces_count() -> None:
    """Delete one entry and verify count decreases by 1."""
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store(Path(tmp))

        ids = [uuid.uuid4().hex for _ in range(3)]
        for i, pid in enumerate(ids):
            store.store(
                pattern_id=pid,
                text=f"pattern {i}",
                vector=_vec(i + 10),
                metadata={},
            )

        assert store.count() == 3

        deleted = store.delete(ids[1])
        assert deleted is True, "delete() should return True for an existing ID"
        assert store.count() == 2, f"Expected count 2 after delete, got {store.count()}"

        # Deleted ID must not appear in query results
        results = store.query(vector=_vec(11), top_k=5)
        returned_ids = {r["pattern_id"] for r in results}
        assert ids[1] not in returned_ids, "Deleted ID appeared in query results"

    print("PASS test_delete_reduces_count")


def test_delete_nonexistent_returns_false() -> None:
    """Deleting an ID that was never stored returns False."""
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store(Path(tmp))
        result = store.delete("this-id-does-not-exist")
        assert result is False, f"Expected False, got {result}"
    print("PASS test_delete_nonexistent_returns_false")


def test_query_empty_store() -> None:
    """Querying an empty store returns an empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store(Path(tmp))
        results = store.query(vector=_vec(0), top_k=5)
        assert results == [], f"Expected [], got {results}"
    print("PASS test_query_empty_store")


def test_persistence_across_instances() -> None:
    """Data stored in one instance is readable in a new instance pointing at the same dir."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pid = uuid.uuid4().hex
        vec = _vec(99)

        store1 = _make_store(tmp_path)
        store1.store(pattern_id=pid, text="hello", vector=vec, metadata={"key": "val"})
        del store1

        store2 = _make_store(tmp_path)
        assert store2.count() == 1, f"Expected 1 after reload, got {store2.count()}"
        results = store2.query(vector=vec, top_k=1)
        assert len(results) == 1
        assert results[0]["pattern_id"] == pid
        assert results[0]["metadata"] == {"key": "val"}

    print("PASS test_persistence_across_instances")


def test_count_zero_on_empty() -> None:
    """count() returns 0 for a fresh store."""
    with tempfile.TemporaryDirectory() as tmp:
        store = _make_store(Path(tmp))
        assert store.count() == 0
    print("PASS test_count_zero_on_empty")


def _run_all() -> None:
    tests = [
        test_store_and_query_top_k,
        test_delete_reduces_count,
        test_delete_nonexistent_returns_false,
        test_query_empty_store,
        test_persistence_across_instances,
        test_count_zero_on_empty,
    ]
    failures: list[str] = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"FAIL {test.__name__}: {exc}")
            print(f"FAIL {test.__name__}: {exc}", file=sys.stderr)

    print(f"\n{len(tests) - len(failures)}/{len(tests)} tests passed")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    _run_all()
