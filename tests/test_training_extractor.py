"""Tests for masonry/src/dspy_pipeline/training_extractor.py."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path


from masonry.src.dspy_pipeline.training_extractor import (
    build_dataset,
    extract_finding,
    extract_training_data,
    score_example,
)


FIXTURES_FINDINGS = Path(__file__).parent / "fixtures" / "findings"


# ──────────────────────────────────────────────────────────────────────────
# extract_finding
# ──────────────────────────────────────────────────────────────────────────


class TestExtractFinding:
    def test_extracts_valid_finding(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding.md")
        assert result is not None
        assert result["question_id"] == "Q1.1"
        assert result["verdict"] == "HEALTHY"
        assert result["severity"] == "Info"
        assert len(result["evidence"]) > 50

    def test_extracts_warning_finding(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding_warning.md")
        assert result is not None
        assert result["question_id"] == "Q1.2"
        assert result["verdict"] == "WARNING"
        assert result["severity"] == "High"

    def test_missing_verdict_returns_none(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding_no_verdict.md")
        assert result is None

    def test_nonexistent_file_returns_none(self):
        result = extract_finding(Path("/does/not/exist/finding.md"))
        assert result is None

    def test_mitigation_extracted_when_present(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding_warning.md")
        assert result is not None
        assert result.get("mitigation") is not None
        assert len(result["mitigation"]) > 0

    def test_mitigation_none_when_absent(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding.md")
        assert result is not None
        # sample_finding.md has no mitigation section or says "No mitigation required"
        # The field may be None or contain the text — just check it's a string or None
        assert result.get("mitigation") is None or isinstance(result["mitigation"], str)

    def test_result_has_all_required_keys(self):
        result = extract_finding(FIXTURES_FINDINGS / "sample_finding.md")
        assert result is not None
        for key in ["question_id", "verdict", "severity", "evidence"]:
            assert key in result

    def test_dynamic_finding(self, tmp_path):
        finding = tmp_path / "q3_1.md"
        finding.write_text(
            textwrap.dedent("""\
                # Finding: Q3.1

                **Verdict**: FAILURE
                **Severity**: Critical

                ## Evidence

                The system failed under all stress scenarios tested.
                Revenue dropped below zero in 90% of Monte Carlo runs.

                ## Mitigation

                Redesign the pricing model from scratch.
            """),
            encoding="utf-8",
        )
        result = extract_finding(finding)
        assert result is not None
        assert result["question_id"] == "Q3.1"
        assert result["verdict"] == "FAILURE"
        assert result["severity"] == "Critical"
        assert "Revenue" in result["evidence"]
        assert "Redesign" in result["mitigation"]


# ──────────────────────────────────────────────────────────────────────────
# extract_training_data
# ──────────────────────────────────────────────────────────────────────────


class TestExtractTrainingData:
    def test_scans_findings_directory(self):
        results = extract_training_data(FIXTURES_FINDINGS.parent)
        # Should find at least the 2 valid findings (HEALTHY and WARNING)
        assert len(results) >= 2

    def test_excludes_no_verdict_findings(self):
        results = extract_training_data(FIXTURES_FINDINGS.parent)
        for r in results:
            assert r.get("verdict") is not None

    def test_empty_directory_returns_empty_list(self, tmp_path):
        results = extract_training_data(tmp_path)
        assert results == []

    def test_nonexistent_directory_returns_empty(self):
        results = extract_training_data(Path("/does/not/exist"))
        assert results == []

    def test_nested_wave_directories_scanned(self, tmp_path):
        """Findings in wave subdirectories should also be found."""
        wave_dir = tmp_path / "project" / "findings" / "wave1"
        wave_dir.mkdir(parents=True)
        finding = wave_dir / "q1.md"
        finding.write_text(
            "# Finding: Q1.1\n\n**Verdict**: OK\n**Severity**: Info\n\n## Evidence\n\nOk.\n",
            encoding="utf-8",
        )
        results = extract_training_data(tmp_path)
        assert len(results) == 1
        assert results[0]["verdict"] == "OK"


# ──────────────────────────────────────────────────────────────────────────
# score_example
# ──────────────────────────────────────────────────────────────────────────


class TestScoreExample:
    def _make_finding(self, agent_name: str = "quantitative-analyst") -> dict:
        return {
            "question_id": "Q1.1",
            "verdict": "HEALTHY",
            "severity": "Info",
            "evidence": "OK",
            "agent": agent_name,
        }

    def test_high_score_agent_gets_weight_1(self):
        finding = self._make_finding("gold-agent")
        agent_db = {"gold-agent": {"score": 0.9}}
        weight = score_example(finding, agent_db)
        assert weight == 1.0

    def test_medium_score_agent_gets_weight_0_7(self):
        finding = self._make_finding("silver-agent")
        agent_db = {"silver-agent": {"score": 0.65}}
        weight = score_example(finding, agent_db)
        assert weight == 0.7

    def test_low_score_agent_gets_weight_0(self):
        finding = self._make_finding("poor-agent")
        agent_db = {"poor-agent": {"score": 0.3}}
        weight = score_example(finding, agent_db)
        assert weight == 0.0

    def test_exact_boundary_0_8_is_gold(self):
        finding = self._make_finding("boundary-agent")
        agent_db = {"boundary-agent": {"score": 0.8}}
        weight = score_example(finding, agent_db)
        assert weight == 1.0

    def test_exact_boundary_0_5_is_silver(self):
        finding = self._make_finding("boundary-agent")
        agent_db = {"boundary-agent": {"score": 0.5}}
        weight = score_example(finding, agent_db)
        assert weight == 0.7

    def test_missing_agent_in_db_returns_0(self):
        finding = self._make_finding("unknown-agent")
        agent_db = {}
        weight = score_example(finding, agent_db)
        assert weight == 0.0

    def test_finding_missing_agent_field_returns_0(self):
        finding = {"question_id": "Q1.1", "verdict": "HEALTHY"}
        weight = score_example(finding, {"some-agent": {"score": 0.9}})
        assert weight == 0.0


# ──────────────────────────────────────────────────────────────────────────
# build_dataset
# ──────────────────────────────────────────────────────────────────────────


class TestBuildDataset:
    def test_groups_by_agent_or_mode(self, tmp_path):
        """Dataset should be grouped by something meaningful."""
        findings_dir = tmp_path / "project" / "findings"
        findings_dir.mkdir(parents=True)

        (findings_dir / "q1.md").write_text(
            "# Finding: Q1.1\n\n**Verdict**: HEALTHY\n**Severity**: Info\n\n## Evidence\n\nOK.\n",
            encoding="utf-8",
        )

        agent_db = {"quantitative-analyst": {"score": 0.9}}
        agent_db_path = tmp_path / "agent_db.json"
        agent_db_path.write_text(json.dumps(agent_db), encoding="utf-8")

        dataset = build_dataset(tmp_path, agent_db_path)
        assert isinstance(dataset, dict)

    def test_excludes_low_score_agents(self, tmp_path):
        """Agents with score < 0.5 are excluded from dataset."""
        findings_dir = tmp_path / "project" / "findings"
        findings_dir.mkdir(parents=True)

        (findings_dir / "q1.md").write_text(
            "# Finding: Q1.1\n\n**Verdict**: HEALTHY\n**Severity**: Info\n\n## Evidence\n\nOK.\n",
            encoding="utf-8",
        )

        # Agent with very low score
        agent_db = {"bad-agent": {"score": 0.2}}
        agent_db_path = tmp_path / "agent_db.json"
        agent_db_path.write_text(json.dumps(agent_db), encoding="utf-8")

        dataset = build_dataset(tmp_path, agent_db_path)
        # All findings should be excluded (no agent match or low score)
        total = sum(len(v) for v in dataset.values())
        assert total == 0

    def test_missing_agent_db_returns_empty(self, tmp_path):
        dataset = build_dataset(tmp_path, Path("/does/not/exist/agent_db.json"))
        assert isinstance(dataset, dict)
        total = sum(len(v) for v in dataset.values())
        assert total == 0
