"""
tests/test_question_sharpener.py — Unit tests for bl/question_sharpener.py.

Uses tmp_path fixtures only. No filesystem side-effects.
"""

from pathlib import Path

from bl.question_sharpener import (
    sharpen_pending_questions,
    _extract_finding_mode,
    _finding_keyword,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

QUESTIONS_MD = """\
# Question Bank

### Q1.1 — Why does cache invalidation fail under load?

**Status**: PENDING
**Mode**: diagnose
**Hypothesis**: Cache invalidation is racy under high concurrency.

---

### Q2.1 — Measure throughput under 1000 RPS

**Status**: PENDING
**Mode**: benchmark
**Hypothesis**: Throughput degrades above 800 RPS.

---

### Q3.1 — Audit logging coverage

**Status**: PENDING
**Mode**: audit
**Hypothesis**: Audit logs are incomplete.

---
"""

FINDING_INCONCLUSIVE_DIAGNOSE = """\
# Q1 — Cache invalidation finding

**Verdict**: INCONCLUSIVE
**Mode**: diagnose

## Summary

Cache invalidation causes race condition under sustained load.

## Details

Extended test run did not converge on a stable verdict.
"""

FINDING_HEALTHY_BENCHMARK = """\
# Q2 — Throughput finding

**Verdict**: HEALTHY
**Mode**: benchmark

## Summary

Throughput stable at 1000 RPS.
"""


def _setup_project(tmp_path: Path, questions_text=QUESTIONS_MD, findings=None):
    """Write questions.md and optional finding files to tmp_path."""
    (tmp_path / "questions.md").write_text(questions_text, encoding="utf-8")
    findings_dir = tmp_path / "findings"
    findings_dir.mkdir()
    if findings:
        for name, content in findings.items():
            (findings_dir / name).write_text(content, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# _extract_finding_mode
# ---------------------------------------------------------------------------


class TestExtractFindingMode:
    def test_extracts_mode(self):
        content = "**Verdict**: INCONCLUSIVE\n**Mode**: benchmark\n"
        assert _extract_finding_mode(content) == "benchmark"

    def test_extracts_diagnose(self):
        content = "**Mode**: diagnose\nsome other stuff"
        assert _extract_finding_mode(content) == "diagnose"

    def test_no_mode_returns_none(self):
        content = "**Verdict**: INCONCLUSIVE\nNo mode here."
        assert _extract_finding_mode(content) is None

    def test_mode_with_surrounding_whitespace(self):
        content = "**Mode**:   audit  \n"
        assert _extract_finding_mode(content) == "audit"


# ---------------------------------------------------------------------------
# _finding_keyword
# ---------------------------------------------------------------------------


class TestFindingKeyword:
    def test_first_three_words(self):
        content = "## Summary\n\nCache invalidation causes race condition"
        result = _finding_keyword(content)
        assert result == "cache-invalidation-causes"

    def test_lowercase(self):
        content = "## Summary\n\nHigh Memory Usage Detected"
        result = _finding_keyword(content)
        assert result == "high-memory-usage"

    def test_no_summary_section(self):
        content = "## Details\n\nSome text here."
        assert _finding_keyword(content) == "inconclusive"

    def test_empty_summary_section(self):
        content = "## Summary\n\n\n## Details"
        assert _finding_keyword(content) == "inconclusive"

    def test_fewer_than_three_words(self):
        content = "## Summary\n\nTwo words"
        result = _finding_keyword(content)
        assert result == "two-words"

    def test_strips_punctuation_words(self):
        """Words should come through cleanly lowercased."""
        content = "## Summary\n\nCache invalidation causes race"
        result = _finding_keyword(content)
        assert "cache" in result
        assert "-" in result


# ---------------------------------------------------------------------------
# sharpen_pending_questions — main function
# ---------------------------------------------------------------------------


class TestSharpenPendingQuestions:
    def test_returns_modified_question_ids(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        result = sharpen_pending_questions(tmp_path)
        assert "Q1.1" in result

    def test_sharpened_flag_written_to_questions(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        sharpen_pending_questions(tmp_path)
        text = (tmp_path / "questions.md").read_text(encoding="utf-8")
        assert "**Sharpened**: true" in text

    def test_narrowed_annotation_on_title_line(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        sharpen_pending_questions(tmp_path)
        text = (tmp_path / "questions.md").read_text(encoding="utf-8")
        assert "[narrowed:" in text

    def test_only_matching_mode_sharpened(self, tmp_path):
        """benchmark and audit questions should not be sharpened (only diagnose INCONCLUSIVE)."""
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        sharpen_pending_questions(tmp_path)
        text = (tmp_path / "questions.md").read_text(encoding="utf-8")
        # Count occurrences of Sharpened flag — only one question should be sharpened
        assert text.count("**Sharpened**: true") == 1

    def test_dry_run_does_not_modify_file(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        original = (tmp_path / "questions.md").read_text(encoding="utf-8")
        result = sharpen_pending_questions(tmp_path, dry_run=True)
        after = (tmp_path / "questions.md").read_text(encoding="utf-8")
        assert after == original
        assert "Q1.1" in result  # still reports what would be sharpened

    def test_idempotent_does_not_re_sharpen(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q1.md": FINDING_INCONCLUSIVE_DIAGNOSE},
        )
        first = sharpen_pending_questions(tmp_path)
        second = sharpen_pending_questions(tmp_path)
        assert "Q1.1" in first
        assert "Q1.1" not in second  # already sharpened, skip
        text = (tmp_path / "questions.md").read_text(encoding="utf-8")
        assert text.count("**Sharpened**: true") == 1

    def test_no_inconclusive_findings_returns_empty(self, tmp_path):
        _setup_project(
            tmp_path,
            findings={"Q2.md": FINDING_HEALTHY_BENCHMARK},
        )
        result = sharpen_pending_questions(tmp_path)
        assert result == []
        text = (tmp_path / "questions.md").read_text(encoding="utf-8")
        assert "**Sharpened**: true" not in text

    def test_no_findings_dir_returns_empty(self, tmp_path):
        (tmp_path / "questions.md").write_text(QUESTIONS_MD, encoding="utf-8")
        # No findings/ directory created
        result = sharpen_pending_questions(tmp_path)
        assert result == []

    def test_empty_findings_dir_returns_empty(self, tmp_path):
        _setup_project(tmp_path, findings={})
        result = sharpen_pending_questions(tmp_path)
        assert result == []

    def test_max_sharpen_respected(self, tmp_path):
        """If multiple questions match, stop at max_sharpen."""
        # Two INCONCLUSIVE diagnose findings → two matching questions
        questions_md = """\
### Q1.1 — Question one

**Status**: PENDING
**Mode**: diagnose

---

### Q1.2 — Question two

**Status**: PENDING
**Mode**: diagnose

---
"""
        finding_a = FINDING_INCONCLUSIVE_DIAGNOSE
        finding_b = """\
# Q1.2 — another finding

**Verdict**: INCONCLUSIVE
**Mode**: diagnose

## Summary

Memory leak under stress test observed
"""
        (tmp_path / "questions.md").write_text(questions_md, encoding="utf-8")
        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "Q1a.md").write_text(finding_a, encoding="utf-8")
        (findings_dir / "Q1b.md").write_text(finding_b, encoding="utf-8")

        result = sharpen_pending_questions(tmp_path, max_sharpen=1)
        assert len(result) == 1

    def test_case_insensitive_mode_matching(self, tmp_path):
        questions_md = """\
### Q1.1 — Question about diagnosis

**Status**: PENDING
**Mode**: Diagnose

---
"""
        finding = """\
**Verdict**: INCONCLUSIVE
**Mode**: diagnose

## Summary

Intermittent failure observed
"""
        (tmp_path / "questions.md").write_text(questions_md, encoding="utf-8")
        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "Q1.md").write_text(finding, encoding="utf-8")

        result = sharpen_pending_questions(tmp_path)
        assert "Q1.1" in result

    def test_no_questions_file_returns_empty(self, tmp_path):
        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "Q1.md").write_text(
            FINDING_INCONCLUSIVE_DIAGNOSE, encoding="utf-8"
        )
        result = sharpen_pending_questions(tmp_path)
        assert result == []
