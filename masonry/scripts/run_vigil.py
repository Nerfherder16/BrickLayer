"""masonry/scripts/run_vigil.py

VIGIL — agent health-monitor for BrickLayer campaigns.

Reads findings markdown files and/or results.tsv, computes per-agent quality
metrics, classifies agents as roses / buds / thorns, generates improvement
proposals, and writes a proposals.json report.

Usage:
    python masonry/scripts/run_vigil.py <project_dir> [--output-dir DIR]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Thresholds
_CONFIDENCE_PASS_THRESHOLD = 0.70   # findings with confidence >= this are "passing"
_MIN_FINDINGS_FOR_METRICS = 5       # agents with fewer findings are excluded
_ROSE_PASS_RATE = 0.80              # pass_rate >= this → rose
_THORN_PASS_RATE = 0.50             # pass_rate < this → thorn (otherwise bud)
_OVERCONFIDENT_PASS_RATE = 0.95     # rubric-based pass_rate >= this → thorn (overconfident)


# ---------------------------------------------------------------------------
# parse_results_tsv
# ---------------------------------------------------------------------------


def parse_results_tsv(tsv_file: Path) -> list[dict]:
    """Parse a results.tsv file into a list of row dicts.

    Returns an empty list if the file is missing or contains only a header.
    """
    if not tsv_file.exists():
        return []

    lines = tsv_file.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return []

    header = [col.strip() for col in lines[0].split("\t")]
    rows: list[dict] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        row = {header[i]: values[i].strip() for i in range(min(len(header), len(values)))}
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# parse_findings_dir
# ---------------------------------------------------------------------------


def parse_findings_dir(findings_dir: Path) -> list[dict]:
    """Parse all .md files in `findings_dir` and return a list of finding dicts.

    Each dict has at minimum:
        - agent: str  (default "unknown")
        - confidence: float  (default 0.5)
        - length: int  (character count of the file)
        - text: str  (raw file text)
    """
    if not findings_dir.exists():
        return []

    findings: list[dict] = []
    for md_file in sorted(findings_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8", errors="replace")

        # Extract agent
        agent_match = re.search(r"\*\*agent\*\*:\s*(.+)", text)
        agent = agent_match.group(1).strip() if agent_match else "unknown"

        # Extract confidence
        conf_match = re.search(r"\*\*confidence\*\*:\s*([0-9]*\.?[0-9]+)", text)
        confidence = float(conf_match.group(1)) if conf_match else 0.5

        findings.append({
            "agent": agent,
            "confidence": confidence,
            "length": len(text),
            "text": text,
        })

    return findings


# ---------------------------------------------------------------------------
# compute_agent_metrics
# ---------------------------------------------------------------------------


def compute_agent_metrics(findings: list[dict]) -> dict[str, dict]:
    """Compute per-agent quality metrics from a list of finding dicts.

    Agents with fewer than 5 findings are excluded from results.

    Returns a dict keyed by agent name with fields:
        pass_rate: float
        avg_length: float
        count: int
    """
    from collections import defaultdict

    buckets: dict[str, list[dict]] = defaultdict(list)
    for f in findings:
        buckets[f["agent"]].append(f)

    metrics: dict[str, dict] = {}
    for agent, agent_findings in buckets.items():
        if len(agent_findings) < _MIN_FINDINGS_FOR_METRICS:
            continue
        passing = sum(
            1 for f in agent_findings
            if f.get("confidence", 0.0) >= _CONFIDENCE_PASS_THRESHOLD
        )
        pass_rate = passing / len(agent_findings)
        avg_length = sum(f.get("length", 0) for f in agent_findings) / len(agent_findings)
        metrics[agent] = {
            "pass_rate": pass_rate,
            "avg_length": avg_length,
            "count": len(agent_findings),
        }

    return metrics


# ---------------------------------------------------------------------------
# classify_rbt
# ---------------------------------------------------------------------------


def classify_rbt(
    metrics: dict[str, dict],
) -> tuple[list[str], list[str], list[str]]:
    """Classify agents into roses, buds, and thorns.

    Roses:  pass_rate >= 0.80 (and not rubric-overconfident)
    Thorns: pass_rate < 0.50, OR (rubric_based=True AND pass_rate >= 0.95)
    Buds:   everything else

    Returns:
        (roses, buds, thorns) — three separate lists of agent names.
    """
    roses: list[str] = []
    buds: list[str] = []
    thorns: list[str] = []

    for agent, m in metrics.items():
        pass_rate = m.get("pass_rate", 0.0)
        rubric_based = m.get("rubric_based", False)

        if rubric_based and pass_rate >= _OVERCONFIDENT_PASS_RATE:
            thorns.append(agent)
        elif pass_rate < _THORN_PASS_RATE:
            thorns.append(agent)
        elif pass_rate >= _ROSE_PASS_RATE:
            roses.append(agent)
        else:
            buds.append(agent)

    return roses, buds, thorns


# ---------------------------------------------------------------------------
# generate_proposals
# ---------------------------------------------------------------------------


def generate_proposals(
    thorns: list[str],
    metrics: dict[str, dict],
) -> list[dict]:
    """Generate improvement proposals for each thorn agent.

    Each proposal dict has:
        agent_name, issue, evidence, proposed_change, risk_level,
        requires_human_approval, status
    """
    if not thorns:
        return []

    proposals: list[dict] = []
    for agent in thorns:
        m = metrics.get(agent, {})
        pass_rate = m.get("pass_rate", 0.0)
        count = m.get("count", 0)
        avg_length = m.get("avg_length", 0.0)

        if pass_rate < 0.30:
            risk_level = "high"
        elif pass_rate < 0.45:
            risk_level = "medium"
        else:
            risk_level = "low"

        proposals.append({
            "agent_name": agent,
            "issue": f"Low confidence pass rate: {pass_rate:.2%} across {count} findings",
            "evidence": (
                f"pass_rate={pass_rate:.3f}, count={count}, avg_length={avg_length:.0f} chars"
            ),
            "proposed_change": (
                "Review agent prompt for clarity; tighten confidence calibration; "
                "add domain-specific examples to improve output quality."
            ),
            "risk_level": risk_level,
            "requires_human_approval": True,
            "status": "pending",
        })

    return proposals


# ---------------------------------------------------------------------------
# write_proposals_json
# ---------------------------------------------------------------------------


def write_proposals_json(
    output_path: Path,
    campaign: str,
    roses: list[str],
    buds: list[str],
    thorns: list[str],
    proposals: list[dict],
) -> None:
    """Write the VIGIL proposals report to `output_path` as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "campaign": campaign,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "roses": roses,
        "buds": buds,
        "thorns": thorns,
        "proposals": proposals,
    }
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# run_vigil  (integration entry point)
# ---------------------------------------------------------------------------


def run_vigil(
    project_dir: Path | str,
    output_dir: Path | str | None = None,
    campaign: str | None = None,
) -> dict:
    """Run the full VIGIL health-monitor pipeline.

    Returns a result dict with keys:
        status:   "ok" | "insufficient_data"
        verdict:  "HEALTHY" | "WARNING" | "CRITICAL"  (absent when insufficient_data)
        summary:  human-readable summary string
        roses, buds, thorns: lists of agent names
        proposals: list of proposal dicts
    """
    project_dir = Path(project_dir)
    if output_dir is None:
        output_dir = project_dir / "vigil"
    output_dir = Path(output_dir)

    if campaign is None:
        campaign = project_dir.name

    findings_dir = project_dir / "findings"
    findings = parse_findings_dir(findings_dir)

    if not findings:
        # Also try results.tsv as fallback — but no agent data there
        tsv_rows = parse_results_tsv(project_dir / "results.tsv")
        if not tsv_rows:
            return {
                "status": "insufficient_data",
                "summary": "No findings or results data found.",
                "roses": [],
                "buds": [],
                "thorns": [],
                "proposals": [],
            }

    metrics = compute_agent_metrics(findings)

    if not metrics:
        # Not enough data per agent
        return {
            "status": "insufficient_data",
            "summary": "Insufficient per-agent findings (< 5 each).",
            "roses": [],
            "buds": [],
            "thorns": [],
            "proposals": [],
        }

    roses, buds, thorns = classify_rbt(metrics)
    proposals = generate_proposals(thorns, metrics)

    # Determine overall verdict
    n_thorns = len(thorns)
    if n_thorns == 0:
        verdict = "HEALTHY"
    elif n_thorns >= 3:
        verdict = "CRITICAL"
    else:
        verdict = "WARNING"

    summary = (
        f"roses={len(roses)}, buds={len(buds)}, thorns={n_thorns}. "
        f"Verdict: {verdict}."
    )

    proposals_path = output_dir / "proposals.json"
    write_proposals_json(
        output_path=proposals_path,
        campaign=campaign,
        roses=roses,
        buds=buds,
        thorns=thorns,
        proposals=proposals,
    )

    return {
        "status": "ok",
        "verdict": verdict,
        "summary": summary,
        "roses": roses,
        "buds": buds,
        "thorns": thorns,
        "proposals": proposals,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="VIGIL — agent health monitor.")
    parser.add_argument("project_dir", type=Path, help="Campaign project directory")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--campaign", default=None)
    args = parser.parse_args()

    result = run_vigil(
        project_dir=args.project_dir,
        output_dir=args.output_dir,
        campaign=args.campaign,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
