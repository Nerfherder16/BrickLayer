"""Tests for masonry/scripts/score_findings.py."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from masonry.scripts.score_findings import (
    discover_findings,
    score_finding,
    extract_finding_fields,
    write_jsonl,
    run,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_FINDING = textwrap.dedent("""\
    # Finding: Q1.1 — Some analysis

    **Agent**: quantitative-analyst
    **Question**: What is the failure boundary?
    **Verdict**: WARNING
    **Severity**: High
    **Confidence**: 0.75

    ## Evidence

    The threshold was breached at 2.8%/mo churn rate giving a 7.97x velocity.
    Critical boundary calculated at exactly 2.78%/month with 500 employees.

    ## Mitigation

    Keep churn below 1.5%.
""")

CRITICAL_HIGH_CONF_FINDING = textwrap.dedent("""\
    # Finding: Q2.1 — Critical failure

    **Agent**: quantitative-analyst
    **Verdict**: FAILURE
    **Severity**: Critical
    **Confidence**: 0.90

    ## Evidence

    System failed in 90% of Monte Carlo runs. Revenue dropped below $0 at month 18.
    Treasury depleted by factor of 3.5x in worst case scenario.
""")

INFO_LOW_CONF_FINDING = textwrap.dedent("""\
    # Finding: Q3.1 — Minor observation

    **Agent**: quantitative-analyst
    **Verdict**: HEALTHY
    **Severity**: Info
    **Confidence**: 0.55

    ## Evidence

    The system appeared stable under all tested conditions with no major anomalies detected.
    Baseline scenario produced nominal results within expected parameters.
""")

MISSING_VERDICT_FINDING = textwrap.dedent("""\
    # Finding: Q4.1 — Incomplete

    **Agent**: quantitative-analyst
    **Severity**: Medium

    ## Evidence

    Some evidence here but verdict is missing from this finding file.
""")

MISSING_CONFIDENCE_FINDING = textwrap.dedent("""\
    # Finding: Q5.1 — No confidence

    **Agent**: quantitative-analyst
    **Verdict**: HEALTHY
    **Severity**: Info

    ## Evidence

    Short evidence.
""")

THIN_EVIDENCE_FINDING = textwrap.dedent("""\
    # Finding: Q6.1 — Thin evidence

    **Agent**: quantitative-analyst
    **Verdict**: WARNING
    **Severity**: High
    **Confidence**: 0.70

    ## Evidence

    Bad.
""")

NO_NUMBERS_FINDING = textwrap.dedent("""\
    # Finding: Q7.1 — No numbers in evidence

    **Agent**: quantitative-analyst
    **Verdict**: WARNING
    **Severity**: High
    **Confidence**: 0.70

    ## Evidence

    The system showed signs of instability during the stress test run with several failures.
    Multiple retries were needed to get through the scenario successfully.
""")


# ---------------------------------------------------------------------------
# score_finding — confidence calibration dimension
# ---------------------------------------------------------------------------


class TestScoreFindingConfidenceCalibration:
    def test_has_confidence_field_scores_points(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        # Has confidence: +10, in range 0.5-0.95: +15
        assert result["score_breakdown"]["confidence_calibration"] >= 25

    def test_extreme_confidence_0_loses_mid_range_points(self, tmp_path):
        content = FULL_FINDING.replace("**Confidence**: 0.75", "**Confidence**: 0.05")
        f = tmp_path / "q.md"
        f.write_text(content, encoding="utf-8")
        result = score_finding(f)
        # Has confidence (+10), but out of range (0 for mid-range)
        assert result["score_breakdown"]["confidence_calibration"] < 25

    def test_extreme_confidence_1_loses_mid_range_points(self, tmp_path):
        content = FULL_FINDING.replace("**Confidence**: 0.75", "**Confidence**: 0.99")
        f = tmp_path / "q.md"
        f.write_text(content, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["confidence_calibration"] < 25

    def test_missing_confidence_field_scores_zero_on_calibration(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(MISSING_CONFIDENCE_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["confidence_calibration"] == 0

    def test_critical_high_conf_gets_full_calibration_score(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(CRITICAL_HIGH_CONF_FINDING, encoding="utf-8")
        result = score_finding(f)
        # FAILURE/Critical with 0.90 conf: +10 (has field) +15 (in range) +15 (match) = 40
        assert result["score_breakdown"]["confidence_calibration"] == 40

    def test_info_low_conf_gets_full_calibration_score(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(INFO_LOW_CONF_FINDING, encoding="utf-8")
        result = score_finding(f)
        # HEALTHY/Info with 0.55 conf: +10 +15 +15 = 40
        assert result["score_breakdown"]["confidence_calibration"] == 40


# ---------------------------------------------------------------------------
# score_finding — evidence quality dimension
# ---------------------------------------------------------------------------


class TestScoreFindingEvidenceQuality:
    def test_has_evidence_section_with_content_scores_points(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["evidence_quality"] >= 10

    def test_evidence_50_plus_chars_scores_extra_points(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["evidence_quality"] >= 25

    def test_thin_evidence_loses_length_bonus(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(THIN_EVIDENCE_FINDING, encoding="utf-8")
        result = score_finding(f)
        # Has evidence (+10), but too short (no +15), may lack numbers
        assert result["score_breakdown"]["evidence_quality"] <= 10

    def test_evidence_with_numbers_scores_full_40(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        # Has evidence (+10), 50+ chars (+15), has numbers (+15) = 40
        assert result["score_breakdown"]["evidence_quality"] == 40

    def test_evidence_without_numbers_loses_number_bonus(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(NO_NUMBERS_FINDING, encoding="utf-8")
        result = score_finding(f)
        # Has evidence (+10), 50+ chars (+15), no numbers (0) = 25
        assert result["score_breakdown"]["evidence_quality"] == 25


# ---------------------------------------------------------------------------
# score_finding — verdict clarity dimension
# ---------------------------------------------------------------------------


class TestScoreFindingVerdictClarity:
    def test_verdict_present_scores_10(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["verdict_clarity"] >= 10

    def test_valid_verdict_from_known_set_scores_20(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["verdict_clarity"] == 20

    def test_missing_verdict_scores_zero(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(MISSING_VERDICT_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score_breakdown"]["verdict_clarity"] == 0

    def test_unknown_verdict_scores_only_10(self, tmp_path):
        content = FULL_FINDING.replace(
            "**Verdict**: WARNING", "**Verdict**: BOGUS_VERDICT"
        )
        f = tmp_path / "q.md"
        f.write_text(content, encoding="utf-8")
        result = score_finding(f)
        # Has verdict field (+10), but not in known set (0 for valid set)
        assert result["score_breakdown"]["verdict_clarity"] == 10


# ---------------------------------------------------------------------------
# score_finding — total score and threshold
# ---------------------------------------------------------------------------


class TestScoreFindingTotal:
    def test_full_quality_finding_scores_100(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score"] == 100

    def test_total_is_sum_of_dimensions(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        breakdown = result["score_breakdown"]
        expected = (
            breakdown["confidence_calibration"]
            + breakdown["evidence_quality"]
            + breakdown["verdict_clarity"]
        )
        assert result["score"] == expected

    def test_low_quality_finding_scores_below_60(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(MISSING_VERDICT_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score"] < 60

    def test_missing_confidence_scores_below_60(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(MISSING_CONFIDENCE_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score"] < 60

    def test_score_capped_at_100(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        result = score_finding(f)
        assert result["score"] <= 100

    def test_score_minimum_is_0(self, tmp_path):
        content = "# Finding: Q9.1\n\nNothing useful here at all.\n"
        f = tmp_path / "q.md"
        f.write_text(content, encoding="utf-8")
        result = score_finding(f)
        assert result["score"] >= 0


# ---------------------------------------------------------------------------
# extract_finding_fields
# ---------------------------------------------------------------------------


class TestExtractFindingFields:
    def test_extracts_question_id_from_header(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["question_id"] == "Q1.1"

    def test_extracts_agent_field(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["agent"] == "quantitative-analyst"

    def test_extracts_verdict_field(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["verdict"] == "WARNING"

    def test_extracts_severity_field(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["severity"] == "High"

    def test_extracts_confidence_as_float(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["confidence"] == 0.75

    def test_extracts_question_text_from_question_header(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert "failure boundary" in fields["question_text"].lower()

    def test_extracts_summary_from_content(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert isinstance(fields["summary"], str)
        assert len(fields["summary"]) > 0

    def test_extracts_evidence_section(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(FULL_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert (
            "threshold" in fields["evidence"].lower()
            or "churn" in fields["evidence"].lower()
        )

    def test_question_id_inferred_from_filename_when_no_header(self, tmp_path):
        content = "**Verdict**: HEALTHY\n**Severity**: Info\n**Confidence**: 0.70\n\n## Evidence\n\nOK.\n"
        f = tmp_path / "Q2.3.md"
        f.write_text(content, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["question_id"] == "Q2.3"

    def test_missing_agent_field_returns_unknown(self, tmp_path):
        content = "# Finding: Q1.1\n\n**Verdict**: HEALTHY\n\n## Evidence\n\nOK.\n"
        f = tmp_path / "q.md"
        f.write_text(content, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["agent"] == "unknown"

    def test_missing_confidence_returns_none(self, tmp_path):
        f = tmp_path / "q.md"
        f.write_text(MISSING_CONFIDENCE_FINDING, encoding="utf-8")
        fields = extract_finding_fields(f)
        assert fields["confidence"] is None


# ---------------------------------------------------------------------------
# discover_findings
# ---------------------------------------------------------------------------


class TestDiscoverFindings:
    def test_finds_findings_in_project_subdirs(self, tmp_path):
        proj = tmp_path / "myproject" / "findings"
        proj.mkdir(parents=True)
        (proj / "q1.md").write_text("# Finding\n", encoding="utf-8")
        results = discover_findings(tmp_path)
        assert any("q1.md" in str(p) for p in results)

    def test_finds_findings_in_root_findings_dir(self, tmp_path):
        root_findings = tmp_path / "findings"
        root_findings.mkdir()
        (root_findings / "Q1.1.md").write_text("# Finding\n", encoding="utf-8")
        results = discover_findings(tmp_path)
        assert any("Q1.1.md" in str(p) for p in results)

    def test_returns_list_of_paths(self, tmp_path):
        results = discover_findings(tmp_path)
        assert isinstance(results, list)

    def test_empty_dir_returns_empty_list(self, tmp_path):
        results = discover_findings(tmp_path)
        assert results == []

    def test_excludes_non_md_files(self, tmp_path):
        proj = tmp_path / "project" / "findings"
        proj.mkdir(parents=True)
        (proj / "notes.txt").write_text("not a finding", encoding="utf-8")
        (proj / "q1.md").write_text("# Finding\n", encoding="utf-8")
        results = discover_findings(tmp_path)
        assert all(p.suffix == ".md" for p in results)
        assert len(results) == 1

    def test_excludes_synthesis_md(self, tmp_path):
        proj = tmp_path / "project" / "findings"
        proj.mkdir(parents=True)
        (proj / "synthesis.md").write_text("# Synthesis\n", encoding="utf-8")
        (proj / "q1.md").write_text("# Finding\n", encoding="utf-8")
        results = discover_findings(tmp_path)
        assert not any("synthesis.md" in str(p) for p in results)

    def test_multiple_projects_scanned(self, tmp_path):
        for project in ("alpha", "beta"):
            proj_dir = tmp_path / project / "findings"
            proj_dir.mkdir(parents=True)
            (proj_dir / "q1.md").write_text("# Finding\n", encoding="utf-8")
        results = discover_findings(tmp_path)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# write_jsonl
# ---------------------------------------------------------------------------


class TestWriteJsonl:
    def test_creates_file_with_records(self, tmp_path):
        records = [
            {
                "question_id": "Q1.1",
                "agent": "qa",
                "score": 80,
                "input": {},
                "output": {},
            },
            {
                "question_id": "Q1.2",
                "agent": "qa",
                "score": 70,
                "input": {},
                "output": {},
            },
        ]
        out = tmp_path / "out.jsonl"
        write_jsonl(records, out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_each_line_is_valid_json(self, tmp_path):
        records = [
            {
                "question_id": "Q1.1",
                "agent": "qa",
                "score": 80,
                "input": {},
                "output": {},
            },
        ]
        out = tmp_path / "out.jsonl"
        write_jsonl(records, out)
        for line in out.read_text(encoding="utf-8").strip().splitlines():
            parsed = json.loads(line)
            assert isinstance(parsed, dict)

    def test_creates_parent_dirs(self, tmp_path):
        records = [
            {
                "question_id": "Q1.1",
                "agent": "qa",
                "score": 80,
                "input": {},
                "output": {},
            }
        ]
        out = tmp_path / "deep" / "nested" / "out.jsonl"
        write_jsonl(records, out)
        assert out.exists()

    def test_empty_records_creates_empty_file(self, tmp_path):
        out = tmp_path / "out.jsonl"
        write_jsonl([], out)
        assert out.exists()
        assert out.read_text(encoding="utf-8").strip() == ""

    def test_jsonl_record_has_required_keys(self, tmp_path):
        records = [
            {
                "question_id": "Q1.1",
                "agent": "qa",
                "score": 80,
                "input": {"x": 1},
                "output": {"y": 2},
            },
        ]
        out = tmp_path / "out.jsonl"
        write_jsonl(records, out)
        parsed = json.loads(out.read_text(encoding="utf-8").strip())
        for key in ("question_id", "agent", "score", "input", "output"):
            assert key in parsed


# ---------------------------------------------------------------------------
# run (integration)
# ---------------------------------------------------------------------------


class TestRun:
    def _make_project(self, tmp_path: Path, n_good: int = 3, n_bad: int = 1) -> Path:
        findings_dir = tmp_path / "myproject" / "findings"
        findings_dir.mkdir(parents=True)
        for i in range(n_good):
            (findings_dir / f"q{i + 1}.md").write_text(
                FULL_FINDING.replace("Q1.1", f"Q{i + 1}.1"),
                encoding="utf-8",
            )
        for i in range(n_bad):
            (findings_dir / f"bad{i + 1}.md").write_text(
                MISSING_VERDICT_FINDING.replace("Q4.1", f"Qbad{i + 1}.1"),
                encoding="utf-8",
            )
        return tmp_path

    def test_writes_scored_findings_jsonl(self, tmp_path):
        base = self._make_project(tmp_path)
        out_path = tmp_path / "masonry" / "training_data" / "scored_findings.jsonl"
        run(base_dir=base, output_path=out_path)
        assert out_path.exists()

    def test_output_contains_only_training_ready_findings(self, tmp_path):
        base = self._make_project(tmp_path, n_good=3, n_bad=2)
        out_path = tmp_path / "masonry" / "training_data" / "scored_findings.jsonl"
        run(base_dir=base, output_path=out_path)
        lines = out_path.read_text(encoding="utf-8").strip().splitlines()
        # Only >= 60 score findings written
        for line in lines:
            record = json.loads(line)
            assert record["score"] >= 60

    def test_returns_summary_dict(self, tmp_path):
        base = self._make_project(tmp_path)
        out_path = tmp_path / "out.jsonl"
        summary = run(base_dir=base, output_path=out_path)
        assert "scanned" in summary
        assert "training_ready" in summary
        assert "output_path" in summary

    def test_summary_counts_are_accurate(self, tmp_path):
        base = self._make_project(tmp_path, n_good=3, n_bad=1)
        out_path = tmp_path / "out.jsonl"
        summary = run(base_dir=base, output_path=out_path)
        assert summary["scanned"] == 4
        assert summary["training_ready"] == 3

    def test_empty_base_dir_produces_empty_output(self, tmp_path):
        out_path = tmp_path / "out.jsonl"
        summary = run(base_dir=tmp_path, output_path=out_path)
        assert summary["scanned"] == 0
        assert summary["training_ready"] == 0

    def test_agents_with_10_plus_examples_in_summary(self, tmp_path):
        findings_dir = tmp_path / "project" / "findings"
        findings_dir.mkdir(parents=True)
        for i in range(12):
            (findings_dir / f"q{i + 1}.md").write_text(
                FULL_FINDING.replace("Q1.1", f"Q{i + 1}.1"),
                encoding="utf-8",
            )
        out_path = tmp_path / "out.jsonl"
        summary = run(base_dir=tmp_path, output_path=out_path)
        assert "agents_with_10_plus" in summary
        # quantitative-analyst should appear with 12 examples
        assert "quantitative-analyst" in summary["agents_with_10_plus"]
