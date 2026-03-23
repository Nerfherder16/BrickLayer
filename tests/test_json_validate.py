"""
tests/test_json_validate.py — Tests for bl/json_validate.py.

Covers:
  - validate_finding_json: happy path, missing required fields, malformed JSON,
    no JSON block, multiple JSON blocks (last wins), extra fields allowed,
    empty object.
  - is_retry: PENDING_RETRY, FORMAT-RETRY, and non-retry statuses.

Written before implementation. All tests must fail until developer completes task.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bl.json_validate import validate_finding_json, is_retry  # noqa: E402


# ---------------------------------------------------------------------------
# validate_finding_json
# ---------------------------------------------------------------------------


class TestValidateFindingJson:
    def test_valid_json_block_returns_dict(self):
        """Valid JSON with both required fields returns (dict, None)."""
        text = (
            "Some prose analysis here.\n\n"
            "```json\n"
            '{"verdict": "HEALTHY", "question_id": "Q1.1", "summary": "All good"}\n'
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert error is None
        assert result is not None
        assert isinstance(result, dict)
        assert result["verdict"] == "HEALTHY"
        assert result["question_id"] == "Q1.1"

    def test_missing_verdict_returns_error(self):
        """JSON block missing 'verdict' returns (None, error message mentioning verdict)."""
        text = (
            "```json\n"
            '{"question_id": "Q2.1", "summary": "No verdict here"}\n'
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert result is None
        assert error is not None
        assert "verdict" in error.lower()

    def test_missing_question_id_returns_error(self):
        """JSON block missing 'question_id' returns (None, error message mentioning question_id)."""
        text = (
            "```json\n"
            '{"verdict": "FAILURE", "summary": "No question_id here"}\n'
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert result is None
        assert error is not None
        assert "question_id" in error.lower()

    def test_malformed_json_returns_parse_error(self):
        """Truncated/malformed JSON block returns (None, error starting with 'JSON parse error')."""
        text = (
            "```json\n"
            '{"verdict": "HEALTHY", "question_id": "Q1.1"\n'  # missing closing brace
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert result is None
        assert error is not None
        assert error.lower().startswith("json parse error")

    def test_no_json_block_returns_none_none(self):
        """Prose finding with no JSON block returns (None, None) — not an error."""
        text = (
            "## Finding\n\n"
            "The simulation ran and everything looked fine.\n"
            "No structured output was produced.\n"
        )
        result, error = validate_finding_json(text)
        assert result is None
        assert error is None

    def test_multiple_json_blocks_uses_last(self):
        """When multiple JSON blocks exist, the LAST one is parsed."""
        text = (
            "Intermediate thinking:\n"
            "```json\n"
            '{"verdict": "INTERMEDIATE", "question_id": "Q0.0"}\n'
            "```\n\n"
            "Final answer:\n"
            "```json\n"
            '{"verdict": "FAILURE", "question_id": "Q3.2", "summary": "Final block"}\n'
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert error is None
        assert result is not None
        assert result["verdict"] == "FAILURE"
        assert result["question_id"] == "Q3.2"

    def test_extra_fields_beyond_required_are_allowed(self):
        """JSON block with extra fields beyond verdict and question_id is valid."""
        text = (
            "```json\n"
            '{"verdict": "HEALTHY", "question_id": "Q4.1", '
            '"confidence": "high", "summary": "All systems nominal", '
            '"data": {"revenue": 120000}}\n'
            "```\n"
        )
        result, error = validate_finding_json(text)
        assert error is None
        assert result is not None
        assert result["confidence"] == "high"
        assert result["data"]["revenue"] == 120000

    def test_empty_json_object_returns_error(self):
        """Empty JSON object {} is missing both required fields — returns (None, error)."""
        text = "```json\n{}\n```\n"
        result, error = validate_finding_json(text)
        assert result is None
        assert error is not None
        # Should mention at least one of the missing required fields
        assert "verdict" in error.lower() or "question_id" in error.lower()


# ---------------------------------------------------------------------------
# is_retry
# ---------------------------------------------------------------------------


class TestIsRetry:
    def test_pending_is_not_retry(self):
        """Plain 'PENDING' status is not a retry."""
        assert is_retry("PENDING") is False

    def test_pending_retry_is_retry(self):
        """'PENDING_RETRY' status signals a format retry."""
        assert is_retry("PENDING_RETRY") is True

    def test_done_format_retry_timestamp_is_retry(self):
        """'DONE [FORMAT-RETRY: 2026-03-20]' status signals a retry."""
        assert is_retry("DONE [FORMAT-RETRY: 2026-03-20]") is True

    def test_done_is_not_retry(self):
        """Plain 'DONE' status is not a retry."""
        assert is_retry("DONE") is False

    def test_empty_string_is_not_retry(self):
        """Empty string status is not a retry."""
        assert is_retry("") is False
