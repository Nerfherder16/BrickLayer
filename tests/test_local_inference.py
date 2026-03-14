"""
tests/test_local_inference.py — Unit tests for bl/local_inference.py.

All Ollama HTTP calls are mocked. No real network traffic.
"""

import unittest
from unittest.mock import MagicMock, patch

import httpx

import bl.local_inference as li


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_post_response(text: str, status: int = 200) -> MagicMock:
    """Build a mock httpx.Response for httpx.post."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"response": text}
    resp.raise_for_status = MagicMock()
    return resp


def _mock_get_response(status: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# TestClassifyFailureTypeLocal
# ---------------------------------------------------------------------------


class TestClassifyFailureTypeLocal(unittest.TestCase):
    """classify_failure_type_local() — valid responses, invalid responses, guard clauses."""

    def _result(self, verdict: str = "FAILURE") -> dict:
        return {
            "verdict": verdict,
            "summary": "something went wrong",
            "details": "detailed trace here",
            "data": {},
        }

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_syntax(self, mock_post):
        mock_post.return_value = _mock_post_response("syntax")
        assert li.classify_failure_type_local(self._result(), "quality") == "syntax"

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_logic(self, mock_post):
        mock_post.return_value = _mock_post_response("logic")
        assert li.classify_failure_type_local(self._result(), "correctness") == "logic"

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_tool_failure(self, mock_post):
        mock_post.return_value = _mock_post_response("tool_failure")
        assert li.classify_failure_type_local(self._result(), "agent") == "tool_failure"

    @patch("bl.local_inference.httpx.post")
    def test_invalid_word_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("banana")
        assert li.classify_failure_type_local(self._result(), "agent") is None

    @patch("bl.local_inference.httpx.post")
    def test_empty_response_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("")
        assert li.classify_failure_type_local(self._result(), "agent") is None

    @patch("bl.local_inference.httpx.post")
    def test_http_exception_returns_none(self, mock_post):
        mock_post.side_effect = httpx.HTTPError("fail")
        assert li.classify_failure_type_local(self._result(), "agent") is None

    def test_skips_healthy_verdict(self):
        """HEALTHY verdict: must return None without making any HTTP call."""
        result = {
            "verdict": "HEALTHY",
            "summary": "all good",
            "details": "",
            "data": {},
        }
        with patch("bl.local_inference.httpx.post") as mock_post:
            out = li.classify_failure_type_local(result, "correctness")
        assert out is None
        mock_post.assert_not_called()

    @patch("bl.local_inference.httpx.post")
    def test_warning_verdict_returns_none(self, mock_post):
        """WARNING is also not a failure — should skip Ollama call and return None."""
        result = {"verdict": "WARNING", "summary": "mild", "details": "", "data": {}}
        out = li.classify_failure_type_local(result, "agent")
        assert out is None
        mock_post.assert_not_called()

    @patch("bl.local_inference.httpx.post")
    def test_inconclusive_verdict_calls_ollama(self, mock_post):
        """INCONCLUSIVE is a classifiable failure state — should call Ollama."""
        mock_post.return_value = _mock_post_response("unknown")
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": "no data",
            "details": "",
            "data": {},
        }
        out = li.classify_failure_type_local(result, "agent")
        assert out == "unknown"
        mock_post.assert_called_once()

    @patch("bl.local_inference.httpx.post")
    def test_all_valid_labels_accepted(self, mock_post):
        """Every label in the allowed set must be accepted."""
        valid = (
            "syntax",
            "logic",
            "hallucination",
            "tool_failure",
            "timeout",
            "unknown",
        )
        result = self._result()
        for label in valid:
            mock_post.return_value = _mock_post_response(label)
            assert li.classify_failure_type_local(result, "agent") == label, label


# ---------------------------------------------------------------------------
# TestClassifyConfidenceLocal
# ---------------------------------------------------------------------------


class TestClassifyConfidenceLocal(unittest.TestCase):
    """classify_confidence_local() — valid signals, invalid signals, whitespace."""

    def _result(self, verdict: str = "FAILURE") -> dict:
        return {
            "verdict": verdict,
            "summary": "some finding",
            "details": "details here",
            "data": {},
        }

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_high(self, mock_post):
        mock_post.return_value = _mock_post_response("high")
        assert li.classify_confidence_local(self._result()) == "high"

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_uncertain(self, mock_post):
        mock_post.return_value = _mock_post_response("uncertain")
        assert li.classify_confidence_local(self._result()) == "uncertain"

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_medium(self, mock_post):
        mock_post.return_value = _mock_post_response("medium")
        assert li.classify_confidence_local(self._result()) == "medium"

    @patch("bl.local_inference.httpx.post")
    def test_valid_response_low(self, mock_post):
        mock_post.return_value = _mock_post_response("low")
        assert li.classify_confidence_local(self._result()) == "low"

    @patch("bl.local_inference.httpx.post")
    def test_invalid_word_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("maybe")
        assert li.classify_confidence_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_http_exception_returns_none(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("fail")
        assert li.classify_confidence_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_extra_whitespace_handled(self, mock_post):
        """Leading/trailing whitespace in response should still match."""
        mock_post.return_value = _mock_post_response("  medium  ")
        assert li.classify_confidence_local(self._result()) == "medium"

    @patch("bl.local_inference.httpx.post")
    def test_empty_response_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("")
        assert li.classify_confidence_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_all_valid_labels_accepted(self, mock_post):
        result = self._result()
        for label in ("high", "medium", "low", "uncertain"):
            mock_post.return_value = _mock_post_response(label)
            assert li.classify_confidence_local(result) == label, label


# ---------------------------------------------------------------------------
# TestScoreResultLocal
# ---------------------------------------------------------------------------


class TestScoreResultLocal(unittest.TestCase):
    """score_result_local() — numeric parsing, range validation, error cases."""

    def _result(self, verdict: str = "FAILURE") -> dict:
        return {
            "verdict": verdict,
            "summary": "some finding",
            "details": "details here",
            "data": {},
        }

    @patch("bl.local_inference.httpx.post")
    def test_valid_score(self, mock_post):
        mock_post.return_value = _mock_post_response("0.85")
        result = li.score_result_local(self._result())
        assert result == 0.85

    @patch("bl.local_inference.httpx.post")
    def test_score_at_lower_boundary(self, mock_post):
        mock_post.return_value = _mock_post_response("0.0")
        assert li.score_result_local(self._result()) == 0.0

    @patch("bl.local_inference.httpx.post")
    def test_score_at_upper_boundary(self, mock_post):
        mock_post.return_value = _mock_post_response("1.0")
        assert li.score_result_local(self._result()) == 1.0

    @patch("bl.local_inference.httpx.post")
    def test_score_out_of_range_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("1.5")
        assert li.score_result_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_negative_score_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("-0.1")
        assert li.score_result_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_non_numeric_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("good")
        assert li.score_result_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_http_exception_returns_none(self, mock_post):
        mock_post.side_effect = httpx.HTTPError("connection failed")
        assert li.score_result_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_empty_response_returns_none(self, mock_post):
        mock_post.return_value = _mock_post_response("")
        assert li.score_result_local(self._result()) is None

    @patch("bl.local_inference.httpx.post")
    def test_score_rounded_to_2_decimals(self, mock_post):
        """Implementation rounds to 2 dp — verify precision contract."""
        mock_post.return_value = _mock_post_response("0.678")
        score = li.score_result_local(self._result())
        # score_result_local rounds to 2 dp; 0.678 -> 0.68
        assert score == round(score, 2)


# ---------------------------------------------------------------------------
# TestIsAvailable
# ---------------------------------------------------------------------------


class TestIsAvailable(unittest.TestCase):
    """is_available() — reachability check via /api/tags."""

    @patch("bl.local_inference.httpx.get")
    def test_available_when_200(self, mock_get):
        mock_get.return_value = _mock_get_response(200)
        assert li.is_available() is True

    @patch("bl.local_inference.httpx.get")
    def test_unavailable_when_non_200(self, mock_get):
        mock_get.return_value = _mock_get_response(503)
        assert li.is_available() is False

    @patch("bl.local_inference.httpx.get")
    def test_unavailable_on_exception(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("refused")
        assert li.is_available() is False

    @patch("bl.local_inference.httpx.get")
    def test_unavailable_on_timeout(self, mock_get):
        mock_get.side_effect = httpx.TimeoutException("timed out")
        assert li.is_available() is False

    @patch("bl.local_inference.httpx.get")
    def test_available_checks_correct_path(self, mock_get):
        """Confirm the call hits /api/tags (not /health or some other path)."""
        mock_get.return_value = _mock_get_response(200)
        li.is_available()
        call_url = mock_get.call_args[0][0]
        assert call_url.endswith("/api/tags"), f"Unexpected URL: {call_url}"
