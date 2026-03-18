"""
tests/test_question_weights_quality.py

TDD tests for quality_score integration in bl/question_weights.py.
Phase 6 — Campaign Quality Intelligence, Task 3.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bl.question_weights import QuestionWeight, load_weights, record_result


# ---------------------------------------------------------------------------
# 1. Low-quality INCONCLUSIVE gets a weight bump (+0.3)
# ---------------------------------------------------------------------------


def test_low_quality_inconclusive_gets_weight_bump(tmp_path: Path) -> None:
    """quality_score=0.2 < 0.4 → weight is higher than INCONCLUSIVE with no quality_score."""
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    bumped_dir = tmp_path / "bumped"
    bumped_dir.mkdir()

    # Baseline: INCONCLUSIVE with no quality_score
    baseline = record_result(str(baseline_dir), "Q1", "INCONCLUSIVE")
    baseline_weight = baseline.weight

    # Low-quality INCONCLUSIVE: should get the +0.3 bump
    bumped = record_result(str(bumped_dir), "Q1", "INCONCLUSIVE", quality_score=0.2)
    assert bumped.weight > baseline_weight, (
        f"Expected bumped weight ({bumped.weight}) > baseline ({baseline_weight}) "
        "when quality_score=0.2 (< 0.4)"
    )


# ---------------------------------------------------------------------------
# 2. High-quality INCONCLUSIVE does NOT get a bump
# ---------------------------------------------------------------------------


def test_high_quality_inconclusive_no_bump(tmp_path: Path) -> None:
    """quality_score=0.8 >= 0.4 → no bump; weight same as plain INCONCLUSIVE."""
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    no_bump_dir = tmp_path / "no_bump"
    no_bump_dir.mkdir()

    baseline = record_result(str(baseline_dir), "Q1", "INCONCLUSIVE")
    no_bump = record_result(str(no_bump_dir), "Q1", "INCONCLUSIVE", quality_score=0.8)

    assert no_bump.weight == baseline.weight, (
        f"Expected no bump when quality_score=0.8 (>= 0.4). "
        f"Got weight={no_bump.weight}, baseline={baseline.weight}"
    )


# ---------------------------------------------------------------------------
# 3. Low-quality non-INCONCLUSIVE verdicts do NOT get a bump
# ---------------------------------------------------------------------------


def test_low_quality_healthy_no_bump(tmp_path: Path) -> None:
    """quality_score=0.2 with HEALTHY verdict → no bump (rule only applies to INCONCLUSIVE)."""
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    no_bump_dir = tmp_path / "no_bump"
    no_bump_dir.mkdir()

    baseline = record_result(str(baseline_dir), "Q1", "HEALTHY")
    no_bump = record_result(str(no_bump_dir), "Q1", "HEALTHY", quality_score=0.2)

    assert no_bump.weight == baseline.weight, (
        f"HEALTHY with quality_score=0.2 should not trigger a bump. "
        f"Got weight={no_bump.weight}, baseline={baseline.weight}"
    )


def test_low_quality_failure_no_bump(tmp_path: Path) -> None:
    """quality_score=0.1 with FAILURE → no bump (rule only applies to INCONCLUSIVE)."""
    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    no_bump_dir = tmp_path / "no_bump"
    no_bump_dir.mkdir()

    baseline = record_result(str(baseline_dir), "Q1", "FAILURE")
    no_bump = record_result(str(no_bump_dir), "Q1", "FAILURE", quality_score=0.1)

    assert no_bump.weight == baseline.weight, (
        f"FAILURE with quality_score=0.1 should not trigger a bump. "
        f"Got weight={no_bump.weight}, baseline={baseline.weight}"
    )


# ---------------------------------------------------------------------------
# 4. last_quality_score persists through JSON round-trip
# ---------------------------------------------------------------------------


def test_last_quality_score_persisted(tmp_path: Path) -> None:
    """last_quality_score=0.7 should survive save → load round-trip."""
    record_result(str(tmp_path), "Q1", "INCONCLUSIVE", quality_score=0.7)

    reloaded = load_weights(str(tmp_path))
    assert "Q1" in reloaded
    assert reloaded["Q1"].last_quality_score == pytest.approx(0.7), (
        f"Expected last_quality_score=0.7, got {reloaded['Q1'].last_quality_score}"
    )


def test_last_quality_score_none_persisted(tmp_path: Path) -> None:
    """Calling record_result without quality_score → last_quality_score persists as None."""
    record_result(str(tmp_path), "Q1", "INCONCLUSIVE")

    reloaded = load_weights(str(tmp_path))
    assert reloaded["Q1"].last_quality_score is None


# ---------------------------------------------------------------------------
# 5. Backward compatibility: existing JSON without last_quality_score field
# ---------------------------------------------------------------------------


def test_backward_compat_missing_last_quality_score(tmp_path: Path) -> None:
    """Loading a .bl-weights.json that lacks last_quality_score → defaults to None, no error."""
    # Write a JSON file in the old format (no last_quality_score key)
    old_format = {
        "Q1": {
            "question_id": "Q1",
            "runs": 2,
            "failures": 1,
            "warnings": 0,
            "healthys": 1,
            "inconclusives": 0,
            "last_verdict": "HEALTHY",
            "weight": 1.5,
            "last_updated": "2025-01-01T00:00:00+00:00",
        }
    }
    (tmp_path / ".bl-weights.json").write_text(
        json.dumps(old_format, indent=2), encoding="utf-8"
    )

    # Should load without raising
    weights = load_weights(str(tmp_path))
    assert "Q1" in weights
    assert weights["Q1"].last_quality_score is None, (
        "Old-format entries without last_quality_score should default to None"
    )
    # Other fields should load correctly
    assert weights["Q1"].runs == 2
    assert weights["Q1"].failures == 1
    assert weights["Q1"].weight == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# 6. Weight bump respects the 3.0 cap
# ---------------------------------------------------------------------------


def test_bump_respects_cap(tmp_path: Path) -> None:
    """Even if +0.3 would exceed 3.0, weight is capped at 3.0."""
    # Drive weight close to 3.0 with failures first
    for _ in range(5):
        record_result(str(tmp_path), "Q1", "FAILURE")

    # Now record low-quality INCONCLUSIVE — should not exceed 3.0
    result = record_result(str(tmp_path), "Q1", "INCONCLUSIVE", quality_score=0.1)
    assert result.weight <= 3.0, f"Weight must be capped at 3.0, got {result.weight}"


# ---------------------------------------------------------------------------
# 7. QuestionWeight dataclass has last_quality_score field
# ---------------------------------------------------------------------------


def test_dataclass_has_last_quality_score_field() -> None:
    """QuestionWeight must have last_quality_score field defaulting to None."""
    qw = QuestionWeight(question_id="Q1")
    assert hasattr(qw, "last_quality_score"), (
        "QuestionWeight missing last_quality_score field"
    )
    assert qw.last_quality_score is None


def test_dataclass_last_quality_score_settable() -> None:
    """last_quality_score can be set to a float."""
    qw = QuestionWeight(question_id="Q1", last_quality_score=0.55)
    assert qw.last_quality_score == pytest.approx(0.55)
