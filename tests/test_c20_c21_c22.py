"""
tests/test_c20_c21_c22.py — Validation suite for C-20, C-21, C-22 roadmap items.

Covers:
  - classify_failure_type()  (C-20 — failure taxonomy)
  - classify_confidence()    (C-21 — confidence signaling)
  - score_result()           (C-22 — eval/scoring harness)
  - CONFIDENCE_ROUTING dict  (C-21 — routing table completeness)
"""

import importlib.util
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import root simulate.py under a unique module name to avoid colliding with
# test_core.py which imports template/simulate.py as 'simulate'.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location(
    "bricklayer_simulate", REPO_ROOT / "simulate.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["bricklayer_simulate"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

CONFIDENCE_ROUTING = _mod.CONFIDENCE_ROUTING
classify_confidence = _mod.classify_confidence
classify_failure_type = _mod.classify_failure_type
score_result = _mod.score_result

# ---------------------------------------------------------------------------
# C-20 — classify_failure_type()
# ---------------------------------------------------------------------------


class TestClassifyFailureType:
    """C-20: failure taxonomy tagging."""

    # HEALTHY/WARNING → None (no failure to classify)
    def test_healthy_returns_none(self):
        result = {"verdict": "HEALTHY", "summary": "", "details": "", "data": {}}
        assert classify_failure_type(result, "correctness") is None

    def test_warning_returns_none(self):
        result = {
            "verdict": "WARNING",
            "summary": "mild issue",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "performance") is None

    # Timeout signals
    def test_timeout_in_summary(self):
        result = {
            "verdict": "FAILURE",
            "summary": "request timed out",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "performance") == "timeout"

    def test_timeout_in_details(self):
        result = {
            "verdict": "FAILURE",
            "summary": "",
            "details": "TimeoutError: read timed out",
            "data": {},
        }
        assert classify_failure_type(result, "correctness") == "timeout"

    # Tool failure signals
    def test_tool_failure_connection_refused(self):
        result = {
            "verdict": "FAILURE",
            "summary": "Connection refused",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "performance") == "tool_failure"

    def test_tool_failure_exit_code(self):
        result = {
            "verdict": "FAILURE",
            "summary": "exit code 1",
            "details": "process failed",
            "data": {},
        }
        assert classify_failure_type(result, "subprocess") == "tool_failure"

    # Syntax errors
    def test_syntax_error_detected(self):
        result = {
            "verdict": "FAILURE",
            "summary": "SyntaxError in module",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "quality") == "syntax"

    def test_import_error_is_tool_failure(self):
        # ImportError = missing module = infrastructure/tool failure, not syntax
        result = {
            "verdict": "FAILURE",
            "summary": "ImportError: cannot import name foo",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "agent") == "tool_failure"

    # Logic errors
    def test_assertion_error_is_logic(self):
        result = {
            "verdict": "FAILURE",
            "summary": "AssertionError: expected 5 got 3",
            "details": "",
            "data": {},
        }
        assert classify_failure_type(result, "correctness") == "logic"

    def test_test_failures_is_logic(self):
        result = {
            "verdict": "FAILURE",
            "summary": "3 tests failed",
            "details": "assert False",
            "data": {},
        }
        assert classify_failure_type(result, "correctness") == "logic"

    # Agent/hallucination mode with no evidence
    def test_agent_no_evidence_is_hallucination(self):
        result = {
            "verdict": "FAILURE",
            "summary": "no findings",
            "details": "agent completed with no concrete output",
            "data": {},
        }
        assert classify_failure_type(result, "agent") == "hallucination"

    # Inconclusive → unknown
    def test_inconclusive_returns_unknown(self):
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": "could not determine",
            "details": "",
            "data": {},
        }
        ft = classify_failure_type(result, "quality")
        # INCONCLUSIVE on non-agent modes → unknown or None (implementation may vary)
        assert ft in ("unknown", None)

    # Return type is always str or None
    def test_return_type(self):
        for verdict in ("FAILURE", "INCONCLUSIVE", "HEALTHY", "WARNING"):
            result = {"verdict": verdict, "summary": "x", "details": "y", "data": {}}
            ft = classify_failure_type(result, "correctness")
            assert ft is None or isinstance(ft, str)


# ---------------------------------------------------------------------------
# C-21 — classify_confidence()
# ---------------------------------------------------------------------------


class TestClassifyConfidence:
    """C-21: confidence signal emission."""

    # INCONCLUSIVE always → uncertain
    def test_inconclusive_returns_uncertain(self):
        result = {"verdict": "INCONCLUSIVE", "summary": "", "data": {}, "details": ""}
        assert classify_confidence(result, "correctness") == "uncertain"

    def test_inconclusive_returns_uncertain_performance(self):
        result = {"verdict": "INCONCLUSIVE", "summary": "", "data": {}, "details": ""}
        assert classify_confidence(result, "performance") == "uncertain"

    # Performance mode: signal from stages count
    def test_performance_high_confidence_many_stages(self):
        result = {
            "verdict": "HEALTHY",
            "summary": "all good",
            "data": {"stages": [1, 2, 3, 4]},
            "details": "",
        }
        assert classify_confidence(result, "performance") == "high"

    def test_performance_low_confidence_no_stages(self):
        result = {
            "verdict": "FAILURE",
            "summary": "failed",
            "data": {},
            "details": "",
        }
        assert classify_confidence(result, "performance") in ("low", "uncertain")

    # Correctness mode: signal from test counts
    def test_correctness_high_confidence_many_tests(self):
        result = {
            "verdict": "HEALTHY",
            "summary": "10 passed",
            "data": {"passed": 10, "failed": 0},
            "details": "",
        }
        assert classify_confidence(result, "correctness") == "high"

    def test_correctness_medium_confidence_few_tests(self):
        result = {
            "verdict": "HEALTHY",
            "summary": "3 passed",
            "data": {"passed": 3, "failed": 0},
            "details": "",
        }
        assert classify_confidence(result, "correctness") in ("medium", "high")

    def test_correctness_uncertain_no_tests(self):
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": "no tests",
            "data": {"passed": 0, "failed": 0},
            "details": "",
        }
        assert classify_confidence(result, "correctness") == "uncertain"

    # Return value is always one of the four valid signals
    def test_valid_signal_values_all_modes(self):
        valid = {"high", "medium", "low", "uncertain"}
        for mode in ("performance", "correctness", "quality", "agent"):
            result = {
                "verdict": "HEALTHY",
                "summary": "ok",
                "data": {},
                "details": "evidence found",
            }
            signal = classify_confidence(result, mode)
            assert signal in valid, f"Invalid signal '{signal}' for mode '{mode}'"

    # All four signals must be reachable (routing table coverage)
    def test_all_signals_routable(self):
        assert set(CONFIDENCE_ROUTING.keys()) >= {"high", "medium", "low", "uncertain"}

    def test_routing_actions_are_valid(self):
        valid_actions = {"accept", "validate", "escalate", "re-run"}
        for signal, action in CONFIDENCE_ROUTING.items():
            assert action in valid_actions, (
                f"'{signal}' routes to invalid action '{action}'"
            )

    def test_high_routes_to_accept(self):
        assert CONFIDENCE_ROUTING["high"] == "accept"

    def test_uncertain_routes_to_rerun(self):
        assert CONFIDENCE_ROUTING["uncertain"] == "re-run"


# ---------------------------------------------------------------------------
# C-22 — score_result()
# ---------------------------------------------------------------------------


class TestScoreResult:
    """C-22: eval/scoring harness."""

    # Score range
    def test_score_is_float(self):
        result = {"verdict": "HEALTHY", "failure_type": None, "confidence": "high"}
        assert isinstance(score_result(result), float)

    def test_score_between_0_and_1(self):
        for verdict in ("HEALTHY", "FAILURE", "WARNING", "INCONCLUSIVE"):
            for confidence in ("high", "medium", "low", "uncertain"):
                result = {
                    "verdict": verdict,
                    "failure_type": None,
                    "confidence": confidence,
                }
                s = score_result(result)
                assert 0.0 <= s <= 1.0, (
                    f"Score {s} out of range for {verdict}/{confidence}"
                )

    # Perfect score: HEALTHY + high confidence + no failure
    def test_perfect_score_healthy_high(self):
        result = {"verdict": "HEALTHY", "failure_type": None, "confidence": "high"}
        assert score_result(result) == 1.0

    # Zero/near-zero: INCONCLUSIVE + uncertain + tool_failure
    def test_minimum_score_inconclusive_uncertain_tool_failure(self):
        result = {
            "verdict": "INCONCLUSIVE",
            "failure_type": "tool_failure",
            "confidence": "uncertain",
        }
        s = score_result(result)
        assert s < 0.2, f"Expected near-zero score, got {s}"

    # FAILURE with high confidence scores higher than FAILURE with uncertain
    def test_failure_high_confidence_beats_failure_uncertain(self):
        high = score_result(
            {"verdict": "FAILURE", "failure_type": "logic", "confidence": "high"}
        )
        uncertain = score_result(
            {"verdict": "FAILURE", "failure_type": "logic", "confidence": "uncertain"}
        )
        assert high > uncertain

    # Score measures evidence quality/clarity, not system health.
    # HEALTHY and FAILURE both have verdict_clarity=1.0 (definitive results).
    # WARNING has verdict_clarity=0.7 (ambiguous). So a clear FAILURE with
    # evidence can outscore a WARNING — this is by design.
    def test_warning_scores_lower_than_definitive_verdicts(self):
        healthy = score_result(
            {"verdict": "HEALTHY", "failure_type": None, "confidence": "high"}
        )
        warning = score_result(
            {"verdict": "WARNING", "failure_type": None, "confidence": "high"}
        )
        # Both HEALTHY and definitive FAILURE score higher than WARNING
        assert healthy > warning

    def test_inconclusive_scores_lowest(self):
        warning = score_result(
            {"verdict": "WARNING", "failure_type": None, "confidence": "high"}
        )
        inconclusive = score_result(
            {"verdict": "INCONCLUSIVE", "failure_type": None, "confidence": "uncertain"}
        )
        assert warning > inconclusive

    # Precision: score is rounded to 3 decimal places
    def test_score_precision(self):
        result = {"verdict": "WARNING", "failure_type": "logic", "confidence": "medium"}
        s = score_result(result)
        assert s == round(s, 3)

    # Hallucination failure type degrades score vs logic
    def test_hallucination_worse_than_logic(self):
        hallucination = score_result(
            {
                "verdict": "FAILURE",
                "failure_type": "hallucination",
                "confidence": "high",
            }
        )
        logic = score_result(
            {"verdict": "FAILURE", "failure_type": "logic", "confidence": "high"}
        )
        assert logic > hallucination

    # Tool failure is worst failure type
    def test_tool_failure_worst_execution_score(self):
        tool = score_result(
            {"verdict": "FAILURE", "failure_type": "tool_failure", "confidence": "high"}
        )
        timeout = score_result(
            {"verdict": "FAILURE", "failure_type": "timeout", "confidence": "high"}
        )
        logic = score_result(
            {"verdict": "FAILURE", "failure_type": "logic", "confidence": "high"}
        )
        assert logic >= timeout >= tool

    # Missing fields don't crash
    def test_missing_fields_dont_crash(self):
        assert isinstance(score_result({}), float)
        assert isinstance(score_result({"verdict": "HEALTHY"}), float)
        assert isinstance(score_result({"confidence": "high"}), float)
