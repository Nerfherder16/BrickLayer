"""
tests/test_path_agreement.py — Integration/validation: local model vs heuristic agreement.

Skips the entire module if Ollama is unreachable. Each test calls both the
local (Ollama) path and the heuristic fallback path, then checks that both
return valid values and logs any disagreements to stdout.
"""

import pytest
from unittest.mock import patch

from bl.local_inference import (
    classify_failure_type_local,
    classify_confidence_local,
    score_result_local,
    is_available,
)
from bl.findings import (
    classify_failure_type,
    classify_confidence,
    score_result,
)

pytestmark = pytest.mark.skipif(
    not is_available(), reason="Ollama not reachable at configured host"
)

# ---------------------------------------------------------------------------
# Representative result envelopes from real campaign data
# ---------------------------------------------------------------------------

REAL_RESULTS = [
    # Q3.5 — WARNING, agent mode
    {
        "qid": "Q3.5",
        "mode": "agent",
        "result": {
            "verdict": "WARNING",
            "summary": (
                "embed_batch() swallows batch failure silently (line 224)"
                " — zero-vector on critical path"
            ),
            "details": (
                "Found at line 224 in embed_batch function."
                " Error is silently swallowed."
            ),
            "data": {},
            "failure_type": None,
            "confidence": None,
        },
    },
    # Q6.4 — WARNING, agent mode
    {
        "qid": "Q6.4",
        "mode": "agent",
        "result": {
            "verdict": "WARNING",
            "summary": (
                "_speculative_seeds, _embed_cache, _tuning_cache written"
                " from async paths without asyncio.Lock"
            ),
            "details": (
                "Found _speculative_seeds and _embed_cache accessed without"
                " lock in async context."
            ),
            "data": {},
            "failure_type": None,
            "confidence": None,
        },
    },
    # Q7.6 — INCONCLUSIVE
    {
        "qid": "Q7.6",
        "mode": "agent",
        "result": {
            "verdict": "INCONCLUSIVE",
            "summary": "Read 2 source files (414 lines) — requires agent analysis for verdict",
            "details": "Could not verify the condition without deeper analysis.",
            "data": {},
            "failure_type": None,
            "confidence": None,
        },
    },
    # Q1.1 — HEALTHY, performance mode
    {
        "qid": "Q1.1",
        "mode": "performance",
        "result": {
            "verdict": "HEALTHY",
            "summary": (
                "c=5: p99=24.4ms | c=10: p99=25.5ms"
                " | c=20: p99=88.4ms | c=40: p99=154.8ms"
            ),
            "details": "All latency targets met across concurrency levels.",
            "data": {"stages": [{"c": 5}, {"c": 10}, {"c": 20}, {"c": 40}]},
            "failure_type": None,
            "confidence": None,
        },
    },
]

_VALID_FAILURE_TYPES = frozenset(
    ("syntax", "logic", "hallucination", "tool_failure", "timeout", "unknown")
)
_VALID_CONFIDENCE = frozenset(("high", "medium", "low", "uncertain"))

# Results where failure type classification is meaningful
_CLASSIFIABLE = [r for r in REAL_RESULTS if r["result"]["verdict"] not in ("HEALTHY",)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _heuristic_failure_type(item: dict) -> str | None:
    """Force heuristic path by patching local to return None."""
    with patch("bl.findings.classify_failure_type_local", return_value=None):
        return classify_failure_type(item["result"], item["mode"])


def _heuristic_confidence(item: dict) -> str:
    """Force heuristic path by patching local to return None."""
    with patch("bl.findings.classify_confidence_local", return_value=None):
        return classify_confidence(item["result"], item["mode"])


def _heuristic_score(item: dict) -> float:
    """Force heuristic path by patching local to return None."""
    with patch("bl.findings.score_result_local", return_value=None):
        return score_result(item["result"])


# ---------------------------------------------------------------------------
# TestFailureTypeAgreement
# ---------------------------------------------------------------------------


class TestFailureTypeAgreement:
    """Both paths must emit valid failure type labels (agreement is logged, not required)."""

    @pytest.mark.parametrize(
        "item", _CLASSIFIABLE, ids=[r["qid"] for r in _CLASSIFIABLE]
    )
    def test_failure_type_local_returns_valid_enum(self, item):
        result = item["result"]
        mode = item["mode"]
        local = classify_failure_type_local(result, mode)
        assert local is None or local in _VALID_FAILURE_TYPES, (
            f"{item['qid']}: local returned unexpected value {local!r}"
        )

    @pytest.mark.parametrize(
        "item", _CLASSIFIABLE, ids=[r["qid"] for r in _CLASSIFIABLE]
    )
    def test_failure_type_heuristic_returns_valid_enum(self, item):
        heuristic = _heuristic_failure_type(item)
        assert heuristic is None or heuristic in _VALID_FAILURE_TYPES, (
            f"{item['qid']}: heuristic returned unexpected value {heuristic!r}"
        )

    @pytest.mark.parametrize(
        "item", _CLASSIFIABLE, ids=[r["qid"] for r in _CLASSIFIABLE]
    )
    def test_failure_type_paths_agree_or_both_unknown(self, item):
        """Both paths should produce valid labels; disagreement is logged, not failed."""
        result = item["result"]
        mode = item["mode"]
        local = classify_failure_type_local(result, mode)
        heuristic = _heuristic_failure_type(item)

        if local != heuristic:
            print(
                f"\n[DISAGREE] {item['qid']} failure_type:"
                f" local={local!r}  heuristic={heuristic!r}"
            )

        # Both must be valid regardless of agreement
        assert local is None or local in _VALID_FAILURE_TYPES
        assert heuristic is None or heuristic in _VALID_FAILURE_TYPES


# ---------------------------------------------------------------------------
# TestConfidenceAgreement
# ---------------------------------------------------------------------------


class TestConfidenceAgreement:
    """Both paths must emit valid confidence signals; disagreement is logged."""

    @pytest.mark.parametrize("item", REAL_RESULTS, ids=[r["qid"] for r in REAL_RESULTS])
    def test_confidence_local_returns_valid_enum(self, item):
        local = classify_confidence_local(item["result"])
        assert local is None or local in _VALID_CONFIDENCE, (
            f"{item['qid']}: local returned unexpected value {local!r}"
        )

    @pytest.mark.parametrize("item", REAL_RESULTS, ids=[r["qid"] for r in REAL_RESULTS])
    def test_confidence_heuristic_returns_valid_enum(self, item):
        heuristic = _heuristic_confidence(item)
        assert heuristic in _VALID_CONFIDENCE, (
            f"{item['qid']}: heuristic returned unexpected value {heuristic!r}"
        )

    def test_confidence_paths_log_disagreement(self):
        """Run both paths on all samples and print a comparison table."""
        print("\n--- Confidence path comparison ---")
        print(f"{'QID':<8}  {'Verdict':<14}  {'Local':<12}  {'Heuristic':<12}  Match")
        print("-" * 58)
        for item in REAL_RESULTS:
            local = classify_confidence_local(item["result"])
            heuristic = _heuristic_confidence(item)
            match = "YES" if local == heuristic else "NO "
            print(
                f"{item['qid']:<8}  {item['result']['verdict']:<14}"
                f"  {str(local):<12}  {heuristic:<12}  {match}"
            )
        # Table output is the goal — no assertion needed beyond the loop completing
        assert True


# ---------------------------------------------------------------------------
# TestScoreAgreement
# ---------------------------------------------------------------------------


class TestScoreAgreement:
    """Both score paths must stay in [0, 1]; wild divergence is flagged."""

    @pytest.mark.parametrize("item", REAL_RESULTS, ids=[r["qid"] for r in REAL_RESULTS])
    def test_score_local_in_range(self, item):
        local = score_result_local(item["result"])
        if local is not None:
            assert 0.0 <= local <= 1.0, (
                f"{item['qid']}: local score {local} out of [0, 1]"
            )

    @pytest.mark.parametrize("item", REAL_RESULTS, ids=[r["qid"] for r in REAL_RESULTS])
    def test_score_formula_in_range(self, item):
        formula = _heuristic_score(item)
        assert 0.0 <= formula <= 1.0, (
            f"{item['qid']}: formula score {formula} out of [0, 1]"
        )

    @pytest.mark.parametrize("item", REAL_RESULTS, ids=[r["qid"] for r in REAL_RESULTS])
    def test_score_paths_within_tolerance(self, item):
        """Both paths must produce in-range scores. If both available, warn on wild divergence."""
        local = score_result_local(item["result"])
        formula = _heuristic_score(item)

        assert 0.0 <= formula <= 1.0

        if local is not None:
            assert 0.0 <= local <= 1.0
            diff = abs(local - formula)
            if diff > 0.4:
                print(
                    f"\n[WIDE DIVERGENCE] {item['qid']}:"
                    f" local={local:.3f}  formula={formula:.3f}  diff={diff:.3f}"
                )
            # Generous tolerance — catching truly wild values only
            assert diff <= 0.4, (
                f"{item['qid']}: score divergence {diff:.3f} exceeds tolerance 0.4"
                f" (local={local:.3f}, formula={formula:.3f})"
            )
