"""
tests/test_synthesizer.py — Unit tests for bl/synthesizer.py.

All Claude subprocess calls are mocked. No real network traffic.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import bl.synthesizer as synth


# ---------------------------------------------------------------------------
# TestParseRecommendation
# ---------------------------------------------------------------------------


class TestParseRecommendation(unittest.TestCase):
    """parse_recommendation() — keyword detection, case handling, defaults."""

    def test_continue_detected(self):
        text = "## Recommended Next Action\nCONTINUE\nMore testing needed."
        assert synth.parse_recommendation(text) == "CONTINUE"

    def test_stop_detected(self):
        text = "## Recommended Next Action\nSTOP\nCampaign is complete."
        assert synth.parse_recommendation(text) == "STOP"

    def test_pivot_detected(self):
        text = (
            "Some findings.\n\n## Recommended Next Action\nPIVOT\nNew direction needed."
        )
        assert synth.parse_recommendation(text) == "PIVOT"

    def test_default_continue(self):
        text = "No recommendation keyword anywhere in this text."
        assert synth.parse_recommendation(text) == "CONTINUE"

    def test_case_insensitive(self):
        text = "Recommended action: stop"
        assert synth.parse_recommendation(text) == "STOP"

    def test_stop_priority_over_continue(self):
        # STOP should match before CONTINUE when STOP appears first
        text = "STOP is recommended. CONTINUE is not applicable."
        assert synth.parse_recommendation(text) == "STOP"


# ---------------------------------------------------------------------------
# TestBuildFindingsCorpus
# ---------------------------------------------------------------------------


class TestBuildFindingsCorpus(unittest.TestCase):
    """_build_findings_corpus() — file reading, corpus assembly, size cap."""

    def test_empty_findings_dir(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            findings_dir = project_dir / "findings"
            findings_dir.mkdir()
            results_tsv = project_dir / "results.tsv"
            corpus = synth._build_findings_corpus(findings_dir, results_tsv)
            assert isinstance(corpus, str)
            assert len(corpus) > 0  # graceful — returns something

    def test_reads_findings_files(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            findings_dir = project_dir / "findings"
            findings_dir.mkdir()
            (findings_dir / "Q1.1.md").write_text(
                "Finding alpha content", encoding="utf-8"
            )
            (findings_dir / "Q1.2.md").write_text(
                "Finding beta content", encoding="utf-8"
            )
            results_tsv = project_dir / "results.tsv"
            corpus = synth._build_findings_corpus(findings_dir, results_tsv)
            assert "Finding alpha content" in corpus
            assert "Finding beta content" in corpus

    def test_reads_results_tsv(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            findings_dir = project_dir / "findings"
            findings_dir.mkdir()
            results_tsv = project_dir / "results.tsv"
            results_tsv.write_text(
                "qid\tverdict\tsummary\nQ1.1\tHEALTHY\tall good\n",
                encoding="utf-8",
            )
            corpus = synth._build_findings_corpus(findings_dir, results_tsv)
            assert "Q1.1" in corpus

    def test_corpus_size_capped(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            findings_dir = project_dir / "findings"
            findings_dir.mkdir()
            results_tsv = project_dir / "results.tsv"
            # Create findings totalling well over 12000 chars
            for i in range(20):
                (findings_dir / f"Q1.{i + 1:02d}.md").write_text(
                    "X" * 1000, encoding="utf-8"
                )
            corpus = synth._build_findings_corpus(findings_dir, results_tsv)
            # Allow small overhead for headers/formatting
            assert len(corpus) <= 12500


# ---------------------------------------------------------------------------
# TestSynthesize
# ---------------------------------------------------------------------------


class TestSynthesize(unittest.TestCase):
    """synthesize() — mocked Claude, file writing, recommendation logging."""

    _VALID_SYNTHESIS = """# Campaign Synthesis — Wave 3

## Core Hypothesis Verdict
PARTIALLY CONFIRMED — some things work.

## Validated Bets
- Memory store: Q1.1, Q1.2 — confidence high

## Dead Ends
None identified.

## Unvalidated Bets
- Concurrent load: not yet tested

## Recommended Next Action
CONTINUE

The campaign is making progress and several questions remain unanswered.
"""

    def test_dry_run_prints_output(self, capsys=None):
        import tempfile
        from io import StringIO

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            (project_dir / "findings").mkdir()

            with patch(
                "bl.synthesizer._call_claude", return_value=self._VALID_SYNTHESIS
            ):
                captured = StringIO()
                old_stdout = sys.stdout
                sys.stdout = captured
                try:
                    result = synth.synthesize(project_dir, wave=3, dry_run=True)
                finally:
                    sys.stdout = old_stdout

            assert result is None
            assert "Campaign Synthesis" in captured.getvalue()

    def test_writes_synthesis_md(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            (project_dir / "findings").mkdir()

            with patch(
                "bl.synthesizer._call_claude", return_value=self._VALID_SYNTHESIS
            ):
                result = synth.synthesize(project_dir, wave=3)

            assert result is not None
            synthesis_path = project_dir / "synthesis.md"
            assert synthesis_path.exists()
            assert "Campaign Synthesis" in synthesis_path.read_text(encoding="utf-8")

    def test_stop_recommendation_logged(self):
        import tempfile
        from io import StringIO

        stop_synthesis = self._VALID_SYNTHESIS.replace(
            "## Recommended Next Action\nCONTINUE", "## Recommended Next Action\nSTOP"
        )

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            (project_dir / "findings").mkdir()

            with patch("bl.synthesizer._call_claude", return_value=stop_synthesis):
                captured_err = StringIO()
                old_stderr = sys.stderr
                sys.stderr = captured_err
                try:
                    synth.synthesize(project_dir, wave=3)
                finally:
                    sys.stderr = old_stderr

            assert "STOP" in captured_err.getvalue()

    def test_claude_failure_returns_none(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            (project_dir / "findings").mkdir()

            with patch("bl.synthesizer._call_claude", return_value=None):
                result = synth.synthesize(project_dir, wave=3)

            assert result is None
            assert not (project_dir / "synthesis.md").exists()


# ---------------------------------------------------------------------------
# TestReadDoctrine
# ---------------------------------------------------------------------------


class TestReadDoctrine(unittest.TestCase):
    """_read_doctrine() — file presence/absence."""

    def test_no_doctrine_returns_empty(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            result = synth._read_doctrine(project_dir)
            assert result == ""

    def test_reads_doctrine_content(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td)
            doctrine_path = project_dir / "doctrine.md"
            doctrine_path.write_text("This is the project doctrine.", encoding="utf-8")
            result = synth._read_doctrine(project_dir)
            assert result == "This is the project doctrine."
