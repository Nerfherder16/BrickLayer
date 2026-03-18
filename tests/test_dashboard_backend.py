"""
tests/test_dashboard_backend.py — TDD for Phase 6 Task 7: dashboard backend
parse_findings_index() Phase 6 fields.

Covers:
  - confidence: float | None — parsed from **Confidence**: 0.85
  - needs_human: bool — parsed from **Needs Human**: True/False
  - sharpened: bool — parsed from **Sharpened**: true/false
  - Defaults: confidence=None, needs_human=False, sharpened=False when fields absent
  - Existing fields still present (backward compat: verdict, severity, has_correction, modified)
  - Cache still functions correctly (new fields included in cached result)
  - parse_questions returns sharpened field for block-format questions
"""

import sys
from pathlib import Path

import pytest

# Ensure the backend module is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard" / "backend"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(tmp_path: Path, stem: str, content: str) -> Path:
    """Write a finding .md file to tmp_path/findings/."""
    findings_dir = tmp_path / "findings"
    findings_dir.mkdir(exist_ok=True)
    fpath = findings_dir / f"{stem}.md"
    fpath.write_text(content, encoding="utf-8")
    return fpath


# ---------------------------------------------------------------------------
# parse_findings_index — Phase 6 new fields
# ---------------------------------------------------------------------------


class TestParseFindingsIndexPhase6:
    def test_confidence_field_parsed(self, tmp_path):
        """**Confidence**: 0.85 → confidence=0.85"""
        _make_finding(
            tmp_path,
            "f1",
            "# Finding One\n**Verdict**: HEALTHY\n**Confidence**: 0.85\n**Needs Human**: False\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert len(results) == 1
        assert results[0]["confidence"] == pytest.approx(0.85)

    def test_confidence_none_when_absent(self, tmp_path):
        """No **Confidence** line → confidence=None"""
        _make_finding(
            tmp_path,
            "f2",
            "# Finding Two\n**Verdict**: WARNING\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["confidence"] is None

    def test_needs_human_true(self, tmp_path):
        """**Needs Human**: True → needs_human=True"""
        _make_finding(
            tmp_path,
            "f3",
            "# Finding Three\n**Verdict**: FAILURE\n**Confidence**: 0.3\n**Needs Human**: True\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["needs_human"] is True

    def test_needs_human_false(self, tmp_path):
        """**Needs Human**: False → needs_human=False"""
        _make_finding(
            tmp_path,
            "f4",
            "# Finding Four\n**Verdict**: HEALTHY\n**Confidence**: 0.9\n**Needs Human**: False\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["needs_human"] is False

    def test_needs_human_false_when_absent(self, tmp_path):
        """No **Needs Human** line → needs_human=False"""
        _make_finding(
            tmp_path,
            "f5",
            "# Finding Five\n**Verdict**: HEALTHY\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["needs_human"] is False

    def test_sharpened_true_lowercase(self, tmp_path):
        """**Sharpened**: true → sharpened=True (case-insensitive)"""
        _make_finding(
            tmp_path,
            "f6",
            "# Finding Six\n**Verdict**: HEALTHY\n**Sharpened**: true\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["sharpened"] is True

    def test_sharpened_true_titlecase(self, tmp_path):
        """**Sharpened**: True → sharpened=True"""
        _make_finding(
            tmp_path,
            "f7",
            "# Finding Seven\n**Verdict**: HEALTHY\n**Sharpened**: True\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["sharpened"] is True

    def test_sharpened_false_when_absent(self, tmp_path):
        """No **Sharpened** line → sharpened=False"""
        _make_finding(
            tmp_path,
            "f8",
            "# Finding Eight\n**Verdict**: HEALTHY\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["sharpened"] is False

    def test_needs_human_case_insensitive(self, tmp_path):
        """**Needs Human**: TRUE (uppercase) → needs_human=True"""
        _make_finding(
            tmp_path,
            "f9",
            "# Finding Nine\n**Verdict**: FAILURE\n**Needs Human**: TRUE\n",
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        assert results[0]["needs_human"] is True

    def test_all_three_fields_present(self, tmp_path):
        """All three new fields parsed correctly from single finding."""
        _make_finding(
            tmp_path,
            "f10",
            (
                "# Full Finding\n"
                "**Verdict**: WARNING\n"
                "**Severity**: HIGH\n"
                "**Confidence**: 0.6\n"
                "**Needs Human**: False\n"
                "**Sharpened**: true\n"
                "\n## Summary\nSome text.\n"
            ),
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        r = results[0]
        assert r["confidence"] == pytest.approx(0.6)
        assert r["needs_human"] is False
        assert r["sharpened"] is True

    # ------------------------------------------------------------------
    # Backward compat — existing fields must still be present
    # ------------------------------------------------------------------

    def test_existing_fields_still_present(self, tmp_path):
        """New fields don't break existing fields: id, title, verdict, severity,
        has_correction, modified."""
        _make_finding(
            tmp_path,
            "compat",
            (
                "# Compat Finding\n"
                "**Verdict**: HEALTHY\n"
                "**Severity**: LOW\n"
                "**Confidence**: 0.9\n"
                "**Needs Human**: False\n"
                "**Sharpened**: false\n"
            ),
        )
        from main import parse_findings_index  # noqa: PLC0415

        results = parse_findings_index(tmp_path)
        r = results[0]
        assert r["id"] == "compat"
        assert r["title"] == "Compat Finding"
        assert r["verdict"] == "HEALTHY"
        assert r["severity"] == "LOW"
        assert r["has_correction"] is False
        assert "modified" in r

    def test_empty_findings_dir_returns_empty_list(self, tmp_path):
        """Empty findings/ directory → empty list."""
        (tmp_path / "findings").mkdir()
        from main import parse_findings_index  # noqa: PLC0415

        assert parse_findings_index(tmp_path) == []

    def test_missing_findings_dir_returns_empty_list(self, tmp_path):
        """No findings/ directory → empty list."""
        from main import parse_findings_index  # noqa: PLC0415

        assert parse_findings_index(tmp_path) == []

    # ------------------------------------------------------------------
    # Cache — new fields must survive cache round-trip
    # ------------------------------------------------------------------

    def test_cached_result_includes_new_fields(self, tmp_path):
        """Cached result still contains confidence, needs_human, sharpened."""
        import main  # noqa: PLC0415

        # Clear cache for this path
        main._findings_cache.pop(str(tmp_path), None)

        _make_finding(
            tmp_path,
            "cached",
            "# Cached\n**Verdict**: HEALTHY\n**Confidence**: 0.7\n**Needs Human**: False\n**Sharpened**: true\n",
        )

        # First call — populates cache
        result1 = main.parse_findings_index(tmp_path)
        assert result1[0]["confidence"] == pytest.approx(0.7)

        # Second call — should come from cache
        result2 = main.parse_findings_index(tmp_path)
        assert result2[0]["confidence"] == pytest.approx(0.7)
        assert result2[0]["needs_human"] is False
        assert result2[0]["sharpened"] is True


# ---------------------------------------------------------------------------
# parse_questions — sharpened field
# ---------------------------------------------------------------------------


class TestParseQuestionsSharpened:
    """Questions parser (block format) should expose sharpened field."""

    def _make_questions_md(self, tmp_path: Path, content: str) -> Path:
        qfile = tmp_path / "questions.md"
        qfile.write_text(content, encoding="utf-8")
        return qfile

    def test_sharpened_true_in_question_block(self, tmp_path):
        """**Sharpened**: true in block question → sharpened=True"""
        self._make_questions_md(
            tmp_path,
            (
                "## Q1.1 [SIM] What is the failure boundary?\n"
                "**Mode**: simulate\n"
                "**Target**: x < 0\n"
                "**Hypothesis**: System breaks when x < 0\n"
                "**Status**: PENDING\n"
                "**Sharpened**: true\n"
            ),
        )
        from main import parse_questions  # noqa: PLC0415

        questions = parse_questions(tmp_path)
        assert len(questions) == 1
        assert questions[0].get("sharpened") is True

    def test_sharpened_false_when_absent_in_block(self, tmp_path):
        """No **Sharpened** in block question → sharpened=False"""
        self._make_questions_md(
            tmp_path,
            (
                "## Q1.1 [SIM] What is the failure boundary?\n"
                "**Mode**: simulate\n"
                "**Status**: PENDING\n"
            ),
        )
        from main import parse_questions  # noqa: PLC0415

        questions = parse_questions(tmp_path)
        assert len(questions) == 1
        assert questions[0].get("sharpened") is False

    def test_sharpened_false_not_present(self, tmp_path):
        """**Sharpened**: false → sharpened=False"""
        self._make_questions_md(
            tmp_path,
            (
                "## Q2.1 [SIM] Another question\n"
                "**Mode**: simulate\n"
                "**Status**: DONE\n"
                "**Sharpened**: false\n"
            ),
        )
        from main import parse_questions  # noqa: PLC0415

        questions = parse_questions(tmp_path)
        assert questions[0].get("sharpened") is False
