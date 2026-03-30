"""Tests for fresh_eyes_verify.py."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def mock_synthesis(tmp_path: Path) -> Path:
    synthesis = tmp_path / "synthesis.md"
    synthesis.write_text(
        "# Synthesis Report\n\n"
        "## Key Findings\n\n"
        "The ADBP credit system achieves 50% purchasing power amplification "
        "through a dual-currency model where employees spend tokens at "
        "participating vendors. Vendor adoption reaches critical mass at "
        "15% penetration. The admin fee of 2.5% sustains operations above "
        "500 monthly active users.\n\n"
        "## Risk Assessment\n\n"
        "Primary risk: vendor liquidity crunch if redemption rate exceeds "
        "80% in any 30-day period. Secondary risk: regulatory classification "
        "as a security if credit-to-cash conversion is permitted.\n\n"
        "## Recommendations\n\n"
        "1. Cap redemption at 70% per period\n"
        "2. Implement graduated vendor onboarding\n"
        "3. Maintain 3-month reserve fund\n",
        encoding="utf-8",
    )
    return synthesis


class TestFreshEyesVerify:
    """Test the fresh-eyes verification module."""

    def test_generate_questions_returns_list(self, mock_synthesis: Path) -> None:
        from masonry.scripts.fresh_eyes_verify import generate_questions

        content = mock_synthesis.read_text(encoding="utf-8")
        questions = generate_questions(content)
        assert isinstance(questions, list)
        assert len(questions) >= 3
        assert all(isinstance(q, dict) for q in questions)
        assert all("question" in q for q in questions)
        assert all("expected_answer" in q for q in questions)

    def test_generate_questions_covers_key_content(self, mock_synthesis: Path) -> None:
        from masonry.scripts.fresh_eyes_verify import generate_questions

        content = mock_synthesis.read_text(encoding="utf-8")
        questions = generate_questions(content)
        # Questions should reference actual content from the synthesis
        all_text = " ".join(
            q["question"] + " " + q["expected_answer"] for q in questions
        )
        # At least some key terms from the synthesis should appear
        key_terms = ["credit", "vendor", "risk", "redemption", "admin", "amplification"]
        matches = sum(1 for term in key_terms if term.lower() in all_text.lower())
        assert matches >= 2, f"Only {matches} key terms found in questions"

    def test_score_answer_returns_float(self) -> None:
        from masonry.scripts.fresh_eyes_verify import score_answer

        score = score_answer(
            expected="50% purchasing power amplification",
            actual="The system provides 50% amplification of purchasing power",
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_answer_high_for_matching(self) -> None:
        from masonry.scripts.fresh_eyes_verify import score_answer

        score = score_answer(
            expected="Vendor adoption reaches critical mass at 15%",
            actual="Critical mass for vendor adoption is reached at 15% penetration",
        )
        assert score >= 0.6

    def test_score_answer_low_for_wrong(self) -> None:
        from masonry.scripts.fresh_eyes_verify import score_answer

        score = score_answer(
            expected="Cap redemption at 70% per period",
            actual="The system has no caps on anything and runs freely",
        )
        assert score < 0.5

    def test_build_report_structure(self) -> None:
        from masonry.scripts.fresh_eyes_verify import build_report

        results = [
            {
                "question": "What is the amplification rate?",
                "expected_answer": "50%",
                "actual_answer": "50% purchasing power",
                "score": 0.9,
            },
            {
                "question": "What is the primary risk?",
                "expected_answer": "vendor liquidity crunch",
                "actual_answer": "liquidity issues with vendors",
                "score": 0.7,
            },
        ]
        report = build_report(results)
        assert "question" in report.lower() or "verification" in report.lower()
        assert "50%" in report
        assert "amplification" in report or "purchasing" in report
