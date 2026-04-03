"""Tests for masonry.src.reasoning.bank.ReasoningBank."""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so the masonry package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from masonry.src.reasoning.bank import ReasoningBank


@pytest.fixture()
def tmp_bank(tmp_path):
    db = tmp_path / "test_reasoning.db"
    return ReasoningBank(db_path=db)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_db_file(self, tmp_path):
        db = tmp_path / "sub" / "reasoning.db"
        ReasoningBank(db_path=db)
        assert db.exists()

    def test_creates_parent_dir(self, tmp_path):
        db = tmp_path / "a" / "b" / "c" / "reasoning.db"
        ReasoningBank(db_path=db)
        assert db.parent.is_dir()

    def test_default_path_resolves(self):
        bank = ReasoningBank()
        expected = Path.home() / ".masonry" / "reasoning.db"
        assert bank._db_path == expected

    def test_double_init_is_idempotent(self, tmp_path):
        db = tmp_path / "r.db"
        ReasoningBank(db_path=db)
        # Second init on same file must not raise
        ReasoningBank(db_path=db)


# ---------------------------------------------------------------------------
# store()
# ---------------------------------------------------------------------------

class TestStore:
    def test_returns_pattern_id(self, tmp_bank):
        pid = tmp_bank.store({"content": "hello world"})
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_auto_generates_uuid_when_missing(self, tmp_bank):
        pid = tmp_bank.store({"content": "no id given"})
        assert len(pid) == 32  # uuid4().hex is 32 hex chars

    def test_respects_explicit_pattern_id(self, tmp_bank):
        pid = tmp_bank.store({"pattern_id": "fixed-id-123", "content": "explicit"})
        assert pid == "fixed-id-123"

    def test_default_confidence(self, tmp_bank):
        pid = tmp_bank.store({"content": "default conf"})
        results = tmp_bank.query("default conf")
        assert results[0]["confidence"] == pytest.approx(0.7)

    def test_custom_confidence(self, tmp_bank):
        tmp_bank.store({"content": "high conf", "confidence": 0.95})
        results = tmp_bank.query("high conf")
        assert results[0]["confidence"] == pytest.approx(0.95)

    def test_domain_stored(self, tmp_bank):
        tmp_bank.store({"content": "domain test", "domain": "finance"})
        results = tmp_bank.query("domain test")
        assert results[0]["domain"] == "finance"

    def test_default_domain_is_general(self, tmp_bank):
        tmp_bank.store({"content": "no domain"})
        results = tmp_bank.query("no domain")
        assert results[0]["domain"] == "general"

    def test_upsert_updates_existing(self, tmp_bank):
        tmp_bank.store({"pattern_id": "dup", "content": "v1", "confidence": 0.5})
        tmp_bank.store({"pattern_id": "dup", "content": "v2", "confidence": 0.9})
        results = tmp_bank.query("v2")
        assert results[0]["pattern_id"] == "dup"
        assert results[0]["confidence"] == pytest.approx(0.9)

    def test_store_with_embedding(self, tmp_bank):
        embedding = [0.1] * 384
        pid = tmp_bank.store({"content": "with embedding", "embedding": embedding})
        assert isinstance(pid, str)

    def test_created_at_populated(self, tmp_bank):
        pid = tmp_bank.store({"content": "ts check"})
        results = tmp_bank.query("ts check")
        assert results[0]["created_at"] is not None
        assert "T" in results[0]["created_at"]  # ISO-8601 format


# ---------------------------------------------------------------------------
# query()
# ---------------------------------------------------------------------------

class TestQuery:
    def test_returns_list(self, tmp_bank):
        result = tmp_bank.query("anything")
        assert isinstance(result, list)

    def test_empty_db_returns_empty(self, tmp_bank):
        result = tmp_bank.query("missing")
        assert result == []

    def test_finds_matching_content(self, tmp_bank):
        tmp_bank.store({"content": "unique phrase xyz"})
        results = tmp_bank.query("unique phrase xyz")
        assert len(results) == 1
        assert results[0]["content"] == "unique phrase xyz"

    def test_no_match_returns_empty(self, tmp_bank):
        tmp_bank.store({"content": "something unrelated"})
        results = tmp_bank.query("zzz_no_match_zzz")
        assert results == []

    def test_top_k_limits_results(self, tmp_bank):
        for i in range(10):
            tmp_bank.store({"content": f"common keyword item {i}", "confidence": i / 10})
        results = tmp_bank.query("common keyword", top_k=3)
        assert len(results) <= 3

    def test_ordered_by_confidence_desc(self, tmp_bank):
        tmp_bank.store({"content": "score test low", "confidence": 0.2})
        tmp_bank.store({"content": "score test mid", "confidence": 0.6})
        tmp_bank.store({"content": "score test high", "confidence": 0.9})
        results = tmp_bank.query("score test")
        confidences = [r["confidence"] for r in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_result_has_expected_keys(self, tmp_bank):
        tmp_bank.store({"content": "key check"})
        results = tmp_bank.query("key check")
        expected = {"pattern_id", "content", "domain", "confidence", "created_at", "last_used"}
        assert expected.issubset(results[0].keys())


# ---------------------------------------------------------------------------
# _text_to_embedding()
# ---------------------------------------------------------------------------

class TestTextToEmbedding:
    def test_returns_list_of_floats(self, tmp_bank):
        emb = tmp_bank._text_to_embedding("hello")
        assert isinstance(emb, list)
        assert all(isinstance(v, float) for v in emb)

    def test_correct_dimension(self, tmp_bank):
        emb = tmp_bank._text_to_embedding("test text")
        assert len(emb) == 384

    def test_repeatable(self, tmp_bank):
        e1 = tmp_bank._text_to_embedding("same text")
        e2 = tmp_bank._text_to_embedding("same text")
        assert e1 == e2

    def test_different_texts_differ(self, tmp_bank):
        e1 = tmp_bank._text_to_embedding("text A")
        e2 = tmp_bank._text_to_embedding("text B")
        assert e1 != e2


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_stores(self, tmp_bank):
        import threading
        errors = []

        def _store(i):
            try:
                tmp_bank.store({"content": f"thread item {i}", "confidence": 0.5})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_store, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        results = tmp_bank.query("thread item")
        assert len(results) > 0
