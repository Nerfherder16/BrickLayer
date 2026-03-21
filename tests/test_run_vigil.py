"""Tests for masonry/scripts/run_vigil.py — VIGIL health-monitor script."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TSV_HEADER = (
    "commit\tquestion_id\tverdict\ttreasury_runway_months\tkey_finding\tscenario_name\n"
)


def _make_tsv(rows: list[dict]) -> str:
    """Build a results.tsv string from a list of row dicts."""
    lines = [TSV_HEADER]
    for r in rows:
        commit = r.get("commit", "abc1234")
        q_id = r.get("question_id", "1.1")
        verdict = r.get("verdict", "HEALTHY")
        runway = str(r.get("treasury_runway_months", "60.0"))
        finding = r.get("key_finding", "All good")
        scenario = r.get("scenario_name", "Q1.1 — Baseline")
        lines.append(f"{commit}\t{q_id}\t{verdict}\t{runway}\t{finding}\t{scenario}\n")
    return "".join(lines)


def _make_finding_md(
    question_id: str,
    agent: str,
    confidence: float,
    length: int = 300,
) -> str:
    """Build a minimal finding markdown with an agent tag and confidence."""
    body = "x" * length
    return textwrap.dedent(f"""\
        # Finding {question_id}

        **agent**: {agent}
        **confidence**: {confidence}

        {body}
    """)


# ---------------------------------------------------------------------------
# parse_results_tsv
# ---------------------------------------------------------------------------


class TestParseResultsTsv:
    """Unit tests for the TSV parser."""

    def test_parses_verdicts(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_results_tsv

        tsv_file = tmp_path / "results.tsv"
        tsv_file.write_text(
            _make_tsv(
                [
                    {"verdict": "HEALTHY"},
                    {"verdict": "WARNING"},
                    {"verdict": "FAILURE"},
                ]
            ),
            encoding="utf-8",
        )

        rows = parse_results_tsv(tsv_file)
        verdicts = [r["verdict"] for r in rows]
        assert verdicts == ["HEALTHY", "WARNING", "FAILURE"]

    def test_returns_empty_list_when_file_missing(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_results_tsv

        rows = parse_results_tsv(tmp_path / "nonexistent.tsv")
        assert rows == []

    def test_returns_empty_list_for_header_only(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_results_tsv

        tsv_file = tmp_path / "results.tsv"
        tsv_file.write_text(TSV_HEADER, encoding="utf-8")

        rows = parse_results_tsv(tsv_file)
        assert rows == []


# ---------------------------------------------------------------------------
# parse_findings_dir
# ---------------------------------------------------------------------------


class TestParseFindingsDir:
    """Unit tests for the findings directory parser."""

    def test_extracts_agent_and_confidence(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_findings_dir

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "q1.md").write_text(
            _make_finding_md("1.1", "quantitative-analyst", 0.85),
            encoding="utf-8",
        )

        findings = parse_findings_dir(findings_dir)
        assert len(findings) == 1
        assert findings[0]["agent"] == "quantitative-analyst"
        assert abs(findings[0]["confidence"] - 0.85) < 0.001

    def test_returns_empty_list_when_dir_missing(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_findings_dir

        findings = parse_findings_dir(tmp_path / "no-findings")
        assert findings == []

    def test_handles_multiple_findings(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_findings_dir

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        for i in range(3):
            (findings_dir / f"q{i}.md").write_text(
                _make_finding_md(str(i), "competitive-analyst", 0.7),
                encoding="utf-8",
            )

        findings = parse_findings_dir(findings_dir)
        assert len(findings) == 3

    def test_defaults_confidence_when_missing(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_findings_dir

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "q_no_conf.md").write_text(
            "# Finding\n\n**agent**: some-agent\n\nNo confidence here.\n",
            encoding="utf-8",
        )

        findings = parse_findings_dir(findings_dir)
        assert len(findings) == 1
        # Should default to 0.5 when confidence line is missing
        assert findings[0]["confidence"] == 0.5

    def test_defaults_agent_when_missing(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import parse_findings_dir

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        (findings_dir / "q_no_agent.md").write_text(
            "# Finding\n\n**confidence**: 0.8\n\nNo agent here.\n",
            encoding="utf-8",
        )

        findings = parse_findings_dir(findings_dir)
        assert len(findings) == 1
        assert findings[0]["agent"] == "unknown"


# ---------------------------------------------------------------------------
# compute_agent_metrics
# ---------------------------------------------------------------------------


class TestComputeAgentMetrics:
    """Unit tests for per-agent metric computation."""

    def _make_findings(
        self,
        agent: str,
        confidences: list[float],
        lengths: list[int] | None = None,
    ) -> list[dict]:
        if lengths is None:
            lengths = [300] * len(confidences)
        return [
            {"agent": agent, "confidence": c, "length": l, "verdict": "HEALTHY"}
            for c, l in zip(confidences, lengths)
        ]

    def test_pass_rate_all_above_threshold(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings("qa", [0.8, 0.9, 0.75, 0.85, 0.95])
        metrics = compute_agent_metrics(findings)
        assert metrics["qa"]["pass_rate"] == 1.0

    def test_pass_rate_none_above_threshold(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings("qa", [0.5, 0.6, 0.4, 0.3, 0.65])
        metrics = compute_agent_metrics(findings)
        assert metrics["qa"]["pass_rate"] == 0.0

    def test_pass_rate_partial(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        # 2 of 5 above 0.7
        findings = self._make_findings("qa", [0.8, 0.5, 0.9, 0.6, 0.4])
        metrics = compute_agent_metrics(findings)
        assert abs(metrics["qa"]["pass_rate"] - 0.4) < 0.001

    def test_avg_length_computed(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings(
            "qa", [0.8, 0.9, 0.75, 0.85, 0.95], [100, 200, 300, 400, 500]
        )
        metrics = compute_agent_metrics(findings)
        assert metrics["qa"]["avg_length"] == 300.0

    def test_agents_with_fewer_than_five_findings_excluded(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings("sparse-agent", [0.8, 0.9, 0.75, 0.85])  # only 4
        metrics = compute_agent_metrics(findings)
        assert "sparse-agent" not in metrics

    def test_multiple_agents_tracked_separately(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings(
            "alpha", [0.8, 0.9, 0.75, 0.85, 0.95]
        ) + self._make_findings("beta", [0.5, 0.4, 0.3, 0.6, 0.2])
        metrics = compute_agent_metrics(findings)
        assert metrics["alpha"]["pass_rate"] == 1.0
        assert metrics["beta"]["pass_rate"] == 0.0

    def test_finding_count_tracked(self) -> None:
        from masonry.scripts.run_vigil import compute_agent_metrics

        findings = self._make_findings("qa", [0.8, 0.9, 0.75, 0.85, 0.95])
        metrics = compute_agent_metrics(findings)
        assert metrics["qa"]["count"] == 5


# ---------------------------------------------------------------------------
# classify_rbt
# ---------------------------------------------------------------------------


class TestClassifyRbt:
    """Unit tests for RBT classification logic."""

    def _make_metrics(
        self, pass_rate: float, avg_length: float = 300.0, count: int = 10
    ) -> dict:
        return {
            "pass_rate": pass_rate,
            "avg_length": avg_length,
            "count": count,
        }

    def test_rose_high_pass_rate(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        metrics = {"good-agent": self._make_metrics(pass_rate=0.9)}
        roses, buds, thorns = classify_rbt(metrics)
        assert "good-agent" in roses
        assert "good-agent" not in thorns

    def test_thorn_low_pass_rate(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        metrics = {"bad-agent": self._make_metrics(pass_rate=0.3)}
        roses, buds, thorns = classify_rbt(metrics)
        assert "bad-agent" in thorns
        assert "bad-agent" not in roses

    def test_bud_mid_pass_rate(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        # pass rate between thorn threshold (< 0.5) and rose threshold (>= 0.8)
        metrics = {"mid-agent": self._make_metrics(pass_rate=0.65)}
        roses, buds, thorns = classify_rbt(metrics)
        assert "mid-agent" in buds
        assert "mid-agent" not in roses
        assert "mid-agent" not in thorns

    def test_thorn_very_high_confidence_overconfident(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        # Confidence always >= 0.95 means over-confident — should be a thorn
        metrics = {"overconfident": self._make_metrics(pass_rate=0.98)}
        roses, buds, thorns = classify_rbt(metrics)
        # overconfident (pass_rate >= 0.95) is flagged as thorn, not rose
        assert "overconfident" in thorns

    def test_no_agents_returns_empty_lists(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        roses, buds, thorns = classify_rbt({})
        assert roses == []
        assert buds == []
        assert thorns == []

    def test_each_agent_appears_in_exactly_one_category(self) -> None:
        from masonry.scripts.run_vigil import classify_rbt

        metrics = {
            "rose-agent": self._make_metrics(0.85),
            "bud-agent": self._make_metrics(0.65),
            "thorn-agent": self._make_metrics(0.3),
        }
        roses, buds, thorns = classify_rbt(metrics)
        all_agents = roses + buds + thorns
        assert len(all_agents) == len(set(all_agents))
        assert "rose-agent" in roses
        assert "bud-agent" in buds
        assert "thorn-agent" in thorns


# ---------------------------------------------------------------------------
# generate_proposals
# ---------------------------------------------------------------------------


class TestGenerateProposals:
    """Unit tests for thorn-agent proposal generation."""

    def test_generates_proposal_for_each_thorn(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        metrics = {
            "weak-agent": {
                "pass_rate": 0.3,
                "avg_length": 300.0,
                "count": 10,
            }
        }
        thorns = ["weak-agent"]
        proposals = generate_proposals(thorns, metrics)
        assert len(proposals) == 1
        assert proposals[0]["agent_name"] == "weak-agent"

    def test_proposal_has_required_fields(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        metrics = {
            "weak-agent": {
                "pass_rate": 0.3,
                "avg_length": 300.0,
                "count": 10,
            }
        }
        proposals = generate_proposals(["weak-agent"], metrics)
        p = proposals[0]
        assert "agent_name" in p
        assert "issue" in p
        assert "evidence" in p
        assert "proposed_change" in p
        assert "risk_level" in p
        assert "requires_human_approval" in p
        assert "status" in p

    def test_requires_human_approval_always_true(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        metrics = {
            "weak-agent": {
                "pass_rate": 0.3,
                "avg_length": 300.0,
                "count": 10,
            }
        }
        proposals = generate_proposals(["weak-agent"], metrics)
        assert proposals[0]["requires_human_approval"] is True

    def test_status_is_pending(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        metrics = {
            "weak-agent": {
                "pass_rate": 0.3,
                "avg_length": 300.0,
                "count": 10,
            }
        }
        proposals = generate_proposals(["weak-agent"], metrics)
        assert proposals[0]["status"] == "pending"

    def test_no_thorns_returns_empty_list(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        proposals = generate_proposals([], {})
        assert proposals == []

    def test_risk_level_is_valid(self) -> None:
        from masonry.scripts.run_vigil import generate_proposals

        metrics = {
            "weak-agent": {
                "pass_rate": 0.3,
                "avg_length": 300.0,
                "count": 10,
            }
        }
        proposals = generate_proposals(["weak-agent"], metrics)
        assert proposals[0]["risk_level"] in ("low", "medium", "high")


# ---------------------------------------------------------------------------
# write_proposals_json
# ---------------------------------------------------------------------------


class TestWriteProposalsJson:
    """Unit tests for proposals.json output."""

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import write_proposals_json

        output_path = tmp_path / "proposals.json"
        write_proposals_json(
            output_path=output_path,
            campaign="test-project",
            roses=["good-agent"],
            buds=["mid-agent"],
            thorns=["bad-agent"],
            proposals=[
                {
                    "agent_name": "bad-agent",
                    "issue": "Low pass rate",
                    "evidence": "pass_rate=0.3",
                    "proposed_change": "Tighten confidence threshold",
                    "risk_level": "medium",
                    "requires_human_approval": True,
                    "status": "pending",
                }
            ],
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert data["campaign"] == "test-project"
        assert "generated_at" in data
        assert data["roses"] == ["good-agent"]
        assert data["buds"] == ["mid-agent"]
        assert data["thorns"] == ["bad-agent"]
        assert len(data["proposals"]) == 1

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import write_proposals_json

        output_path = tmp_path / "vigil" / "proposals.json"
        write_proposals_json(
            output_path=output_path,
            campaign="test",
            roses=[],
            buds=[],
            thorns=[],
            proposals=[],
        )

        assert output_path.exists()

    def test_generated_at_is_iso_format(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import write_proposals_json
        import re

        output_path = tmp_path / "proposals.json"
        write_proposals_json(
            output_path=output_path,
            campaign="test",
            roses=[],
            buds=[],
            thorns=[],
            proposals=[],
        )

        data = json.loads(output_path.read_text(encoding="utf-8"))
        # Basic ISO-8601 pattern check: YYYY-MM-DDTHH:MM:SS
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", data["generated_at"])


# ---------------------------------------------------------------------------
# run_vigil (integration / end-to-end)
# ---------------------------------------------------------------------------


class TestRunVigil:
    """Integration tests for the top-level run_vigil function."""

    def test_insufficient_data_when_no_findings(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        result = run_vigil(project_dir=tmp_path, output_dir=tmp_path / "vigil")
        assert result["status"] == "insufficient_data"

    def test_healthy_verdict_when_no_thorns(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        # 7 high-confidence + 1 below threshold => pass_rate = 7/8 = 0.875 (rose zone)
        for i in range(7):
            (findings_dir / f"q{i}.md").write_text(
                _make_finding_md(str(i), "good-agent", 0.85),
                encoding="utf-8",
            )
        (findings_dir / "q7.md").write_text(
            _make_finding_md("7", "good-agent", 0.55),
            encoding="utf-8",
        )

        result = run_vigil(project_dir=tmp_path, output_dir=tmp_path / "vigil")
        assert result["verdict"] == "HEALTHY"

    def test_warning_verdict_with_one_thorn(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        # good-agent: 8 high-confidence findings
        for i in range(8):
            (findings_dir / f"good_{i}.md").write_text(
                _make_finding_md(str(i), "good-agent", 0.85),
                encoding="utf-8",
            )
        # bad-agent: 5 low-confidence findings
        for i in range(5):
            (findings_dir / f"bad_{i}.md").write_text(
                _make_finding_md(f"b{i}", "bad-agent", 0.3),
                encoding="utf-8",
            )

        result = run_vigil(project_dir=tmp_path, output_dir=tmp_path / "vigil")
        assert result["verdict"] in ("WARNING", "CRITICAL")

    def test_critical_verdict_with_three_thorns(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        for agent_idx in range(3):
            for i in range(5):
                (findings_dir / f"bad_{agent_idx}_{i}.md").write_text(
                    _make_finding_md(f"b{agent_idx}{i}", f"bad-agent-{agent_idx}", 0.3),
                    encoding="utf-8",
                )

        result = run_vigil(project_dir=tmp_path, output_dir=tmp_path / "vigil")
        assert result["verdict"] == "CRITICAL"

    def test_writes_proposals_json(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        for i in range(5):
            (findings_dir / f"q{i}.md").write_text(
                _make_finding_md(str(i), "some-agent", 0.85),
                encoding="utf-8",
            )

        output_dir = tmp_path / "vigil"
        run_vigil(project_dir=tmp_path, output_dir=output_dir)

        assert (output_dir / "proposals.json").exists()

    def test_summary_contains_counts(self, tmp_path: Path) -> None:
        from masonry.scripts.run_vigil import run_vigil

        findings_dir = tmp_path / "findings"
        findings_dir.mkdir()
        for i in range(6):
            (findings_dir / f"q{i}.md").write_text(
                _make_finding_md(str(i), "some-agent", 0.85),
                encoding="utf-8",
            )

        result = run_vigil(project_dir=tmp_path, output_dir=tmp_path / "vigil")
        assert (
            "roses" in result["summary"].lower()
            or "buds" in result["summary"].lower()
            or "thorns" in result["summary"].lower()
        )
