"""Tests for the Constitutional AI critique-revise pass in optimize_with_claude.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from masonry.scripts.optimize_with_claude import (
    CONSTITUTIONAL_ANTIPATTERNS,
    run_constitutional_critique,
)


# ── Anti-pattern constant tests ──────────────────────────────────────────────


def test_antipatterns_has_exactly_10_items():
    assert len(CONSTITUTIONAL_ANTIPATTERNS) == 10


def test_antipatterns_are_all_strings():
    for item in CONSTITUTIONAL_ANTIPATTERNS:
        assert isinstance(item, str), f"Expected str, got {type(item)}: {item!r}"


def test_antipatterns_are_nonempty():
    for item in CONSTITUTIONAL_ANTIPATTERNS:
        assert item.strip(), "Anti-pattern string must not be blank"


# ── Return type tests ────────────────────────────────────────────────────────


def _make_run_result(stdout: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.returncode = returncode
    return result


def test_run_constitutional_critique_returns_tuple(tmp_path):
    """Return type must be (str, int, bool)."""
    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.return_value = _make_run_result("CONSTITUTIONAL_PASS")
        result = run_constitutional_critique("some instructions", tmp_path)

    assert isinstance(result, tuple), "Must return a tuple"
    assert len(result) == 3, "Tuple must have 3 elements"
    instructions, rounds, passed = result
    assert isinstance(instructions, str)
    assert isinstance(rounds, int)
    assert isinstance(passed, bool)


# ── CONSTITUTIONAL_PASS path ─────────────────────────────────────────────────


def test_rounds_zero_on_constitutional_pass(tmp_path):
    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.return_value = _make_run_result("CONSTITUTIONAL_PASS")
        _, rounds, passed = run_constitutional_critique("instructions", tmp_path)

    assert rounds == 0
    assert passed is True


def test_original_instructions_returned_on_pass(tmp_path):
    original = "Do the thing properly."
    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.return_value = _make_run_result("CONSTITUTIONAL_PASS")
        instructions, _, _ = run_constitutional_critique(original, tmp_path)

    assert instructions == original


# ── Violation path ───────────────────────────────────────────────────────────


def test_rounds_bounded_by_max_rounds(tmp_path):
    """Critique must not loop more than max_rounds times."""
    # Always return violations so it loops until the cap
    violation_response = "CONSTITUTIONAL_VIOLATIONS\n1. Bad pattern found."
    revised_response = "CONSTITUTIONAL_VIOLATIONS\n1. Still bad."

    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        # All calls keep reporting violations; revised call returns something
        mock_run.side_effect = [
            _make_run_result(violation_response),
            _make_run_result("revised instructions"),  # revision call
            _make_run_result(violation_response),
            _make_run_result("revised instructions"),
            _make_run_result(violation_response),
            _make_run_result("revised instructions"),
        ]
        _, rounds, passed = run_constitutional_critique(
            "original", tmp_path, max_rounds=3
        )

    assert rounds <= 3
    assert passed is False


def test_revised_instructions_returned_on_violations(tmp_path):
    """When violations are found, the revised instructions must be returned."""
    violation_response = "CONSTITUTIONAL_VIOLATIONS\n1. Uses absolute language."
    revised = "Improved instructions without absolute language."

    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.side_effect = [
            _make_run_result(violation_response),
            _make_run_result(revised),
            _make_run_result("CONSTITUTIONAL_PASS"),
        ]
        instructions, rounds, passed = run_constitutional_critique(
            "original", tmp_path, max_rounds=3
        )

    assert instructions == revised
    assert rounds == 1
    assert passed is True


def test_passed_false_when_violations_persist_to_max_rounds(tmp_path):
    violation_response = "CONSTITUTIONAL_VIOLATIONS\n1. Something bad."
    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.side_effect = [
            _make_run_result(violation_response),
            _make_run_result("revised v1"),
            _make_run_result(violation_response),
            _make_run_result("revised v2"),
        ]
        _, rounds, passed = run_constitutional_critique(
            "original", tmp_path, max_rounds=2
        )

    assert passed is False
    assert rounds == 2


def test_subprocess_error_returns_original_instructions(tmp_path):
    """If claude -p fails (non-zero exit), return original instructions unchanged."""
    original = "original instructions"
    with patch("masonry.scripts.optimize_with_claude.subprocess.run") as mock_run:
        mock_run.return_value = _make_run_result("", returncode=1)
        instructions, rounds, passed = run_constitutional_critique(
            original, tmp_path, max_rounds=3
        )

    assert instructions == original
    assert rounds == 0
    assert passed is False
