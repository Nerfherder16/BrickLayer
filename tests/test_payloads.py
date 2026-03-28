"""
Tests for masonry/src/schemas/payloads.py — PatternRecord and existing schemas.

Run with: python -m pytest tests/test_payloads.py --capture=no -q
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masonry.src.schemas.payloads import PatternRecord  # noqa: E402


class TestPatternRecord:
    def test_default_confidence(self):
        p = PatternRecord(pattern_id="p1", content="some pattern")
        assert p.confidence == 0.7

    def test_default_domain(self):
        p = PatternRecord(pattern_id="p1", content="some pattern")
        assert p.domain == "general"

    def test_last_used_defaults_none(self):
        p = PatternRecord(pattern_id="p1", content="some pattern")
        assert p.last_used is None

    def test_created_at_auto_populated(self):
        p = PatternRecord(pattern_id="p1", content="some pattern")
        assert p.created_at is not None
        assert len(p.created_at) > 0

    def test_custom_confidence(self):
        p = PatternRecord(pattern_id="p1", content="c", confidence=0.85)
        assert p.confidence == 0.85

    def test_confidence_lower_bound(self):
        p = PatternRecord(pattern_id="p1", content="c", confidence=0.0)
        assert p.confidence == 0.0

    def test_confidence_upper_bound(self):
        p = PatternRecord(pattern_id="p1", content="c", confidence=1.0)
        assert p.confidence == 1.0

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            PatternRecord(pattern_id="p1", content="c", confidence=-0.01)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            PatternRecord(pattern_id="p1", content="c", confidence=1.01)

    def test_initial_confidence_class_var(self):
        assert PatternRecord.INITIAL_CONFIDENCE == 0.7

    def test_prune_threshold_class_var(self):
        assert PatternRecord.PRUNE_THRESHOLD == 0.2

    def test_full_construction(self):
        p = PatternRecord(
            pattern_id="p2",
            content="retry after failure",
            domain="autoresearch",
            confidence=0.9,
            last_used="2026-03-27T00:00:00",
        )
        assert p.domain == "autoresearch"
        assert p.last_used == "2026-03-27T00:00:00"
        assert p.confidence == 0.9

    def test_missing_pattern_id_rejected(self):
        with pytest.raises(ValidationError):
            PatternRecord(content="some pattern")

    def test_missing_content_rejected(self):
        with pytest.raises(ValidationError):
            PatternRecord(pattern_id="p1")
