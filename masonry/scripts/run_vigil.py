"""masonry/scripts/run_vigil.py

Standalone VIGIL health check — reads results.tsv + findings, produces proposals.json.

Usage:
    python masonry/scripts/run_vigil.py [--project PROJECT_DIR] [--output OUTPUT_DIR]

If --project is omitted, the current working directory is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Try to import scoring rubrics for scored_all integration
# ---------------------------------------------------------------------------

try:
    from masonry.src.scoring.rubrics import max_score as _rubric_max_score
    _HAS_RUBRICS = True
except ImportError:
    _HAS_RUBRICS = False

    def _rubric_max_score(agent_name: str) -> int:  # type: ignore[misc]
        return 100

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.70
ROSE_PASS_RATE = 0.80
THORN_PASS_RATE = 0.50
OVERCONFIDENT_PASS_RATE = 0.95  # Suspiciously perfect — flag as thorn
MIN_FINDINGS_FOR_METRICS = 5


# ---------------------------------------------------------------------------
# parse_results_tsv
# ---------------------------------------------------------------------------


def load_scored_all(base_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Load scored_all.jsonl and return {agent_name: [records]}.

    Handles two CWD layouts:
      - Normal (base_dir = BL repo root): base_dir/masonry/training_data/scored_all.jsonl
      - Self-research (base_dir = masonry/ dir): base_dir/training_data/scored_all.jsonl
    """
    # Self-research mode: CWD is the masonry/ dir itself
    self_research_path = base_dir / "training_data" / "scored_all.jsonl"
    normal_path = base_dir / "masonry" / "training_data" / "scored_all.jsonl"
    if self_research_path.exists():
        jsonl_path = self_research_path
    else:
        jsonl_path = normal_path
    if not jsonl_path.exists():
        return {}
    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            agent = rec.get("agent", "unknown")
            if agent and agent != "unknown":
                records[agent].append(rec)
        except json.JSONDecodeError:
            continue
    return dict(records)


def parse_results_tsv(tsv_path: Path) -> list[dict[str, Any]]:
    """Parse a results.tsv file and return a list of row dicts.

    Returns an empty list if the file does not exist or contains only a header.
    """
    if not tsv_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    lines = tsv_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return []

    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        row = dict(zip(header, values))
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# parse_findings_dir
# ---------------------------------------------------------------------------

_AGENT_PATTERN = re.compile(r"\*\*agent\*\*\s*:\s*(.+)", re.IGNORECASE)
_CONFIDENCE_PATTERN = re.compile(r"\*\*confidence\*\*\s*:\s*([0-9.]+)", re.IGNORECASE)


def parse_findings_dir(findings_dir: Path) -> list[dict[str, Any]]:
    """Parse all .md files in a findings directory.

    Returns a list of dicts with keys: agent, confidence, length, path.
    Defaults to agent='unknown' and confidence=0.5 if not found in the file.
    """
    if not findings_dir.exists():
        return []

    findings: list[dict[str, Any]] = []
    for md_file in sorted(findings_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")

        agent_match = _AGENT_PATTERN.search(text)
        agent = agent_match.group(1).strip() if agent_match else "unknown"

        conf_match = _CONFIDENCE_PATTERN.search(text)
        confidence = float(conf_match.group(1)) if conf_match else 0.5

        findings.append(
            {
                "agent": agent,
                "confidence": confidence,
                "length": len(text),
                "verdict": "UNKNOWN",
                "path": str(md_file),
            }
        )

    return findings


# ---------------------------------------------------------------------------
# compute_agent_metrics
# ---------------------------------------------------------------------------


def compute_agent_metrics(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Compute per-agent metrics from a list of finding dicts.

    Agents with fewer than MIN_FINDINGS_FOR_METRICS findings are excluded.

    Returns a dict keyed by agent name with:
        pass_rate  — fraction of findings with confidence >= CONFIDENCE_THRESHOLD
        avg_length — average character length of findings
        count      — number of findings
    """
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in findings:
        buckets[f["agent"]].append(f)

    metrics: dict[str, dict[str, Any]] = {}
    for agent, agent_findings in buckets.items():
        if len(agent_findings) < MIN_FINDINGS_FOR_METRICS:
            continue
        passing = sum(1 for f in agent_findings if f["confidence"] >= CONFIDENCE_THRESHOLD)
        avg_length = sum(f["length"] for f in agent_findings) / len(agent_findings)
        metrics[agent] = {
            "pass_rate": passing / len(agent_findings),
            "avg_length": avg_length,
            "count": len(agent_findings),
        }

    return metrics


# ---------------------------------------------------------------------------
# classify_rbt
# ---------------------------------------------------------------------------


def classify_rbt(
    metrics: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    """Classify agents into Roses, Buds, and Thorns.

    Thresholds:
        Rose   — pass_rate in [ROSE_PASS_RATE, OVERCONFIDENT_PASS_RATE)
        Thorn  — pass_rate < THORN_PASS_RATE  OR  pass_rate >= OVERCONFIDENT_PASS_RATE
        Bud    — everything else (pass_rate in [THORN_PASS_RATE, ROSE_PASS_RATE))

    The OVERCONFIDENT threshold flags agents that are suspiciously perfect — a
    pass_rate >= 0.95 suggests the agent is not self-critical enough.
    """
    roses: list[str] = []
    buds: list[str] = []
    thorns: list[str] = []

    for agent, m in metrics.items():
        pr = m["pass_rate"]
        if pr >= OVERCONFIDENT_PASS_RATE:
            # Suspiciously over-confident
            thorns.append(agent)
        elif pr >= ROSE_PASS_RATE:
            roses.append(agent)
        elif pr < THORN_PASS_RATE:
            thorns.append(agent)
        else:
            buds.append(agent)

    return roses, buds, thorns


# ---------------------------------------------------------------------------
# generate_proposals
# ---------------------------------------------------------------------------


def generate_proposals(
    thorns: list[str],
    metrics: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate guarded improvement proposals for each Thorn agent."""
    proposals: list[dict[str, Any]] = []

    for agent in thorns:
        m = metrics.get(agent, {})
        pass_rate = m.get("pass_rate", 0.0)
        count = m.get("count", 0)
        avg_length = m.get("avg_length", 0.0)

        if pass_rate >= OVERCONFIDENT_PASS_RATE:
            issue = (
                f"confidence consistently at or above {OVERCONFIDENT_PASS_RATE} "
                "— possible over-confidence"
            )
            proposed_change = (
                "Add explicit uncertainty language to the agent's output instructions. "
                "Require the agent to list at least one counter-argument or limitation "
                "in every finding."
            )
            risk = "low"
        else:
            issue = (
                f"quality gate pass rate is {pass_rate:.0%} over {count} findings "
                f"(threshold: {CONFIDENCE_THRESHOLD})"
            )
            proposed_change = (
                "Review the agent's system prompt for vague or overly broad instructions. "
                "Add explicit criteria for what constitutes a high-confidence finding and "
                "require citing specific data points from the simulation."
            )
            risk = "medium" if pass_rate >= 0.3 else "high"

        proposals.append(
            {
                "agent_name": agent,
                "issue": issue,
                "evidence": (
                    f"pass_rate={pass_rate:.2f}, avg_length={avg_length:.0f}chars, "
                    f"findings_analyzed={count}"
                ),
                "proposed_change": proposed_change,
                "risk_level": risk,
                "requires_human_approval": True,
                "status": "pending",
            }
        )

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
    proposals: list[dict[str, Any]],
) -> None:
    """Write the VIGIL output to proposals.json, creating parent dirs as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "campaign": campaign,
        "roses": roses,
        "buds": buds,
        "thorns": thorns,
        "proposals": proposals,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# run_vigil — top-level orchestrator
# ---------------------------------------------------------------------------


def run_vigil(
    project_dir: Path,
    output_dir: Path,
    campaign: str | None = None,
) -> dict[str, Any]:
    """Run the VIGIL health check for a single project directory.

    Returns a result dict with keys:
        status   — 'ok' or 'insufficient_data'
        verdict  — 'HEALTHY' | 'WARNING' | 'CRITICAL'
        summary  — human-readable summary string
        roses / buds / thorns — lists of agent names
        proposals — list of proposal dicts
    """
    findings_dir = project_dir / "findings"
    findings = parse_findings_dir(findings_dir)

    if not findings:
        return {
            "status": "insufficient_data",
            "verdict": "UNKNOWN",
            "summary": "No findings available — insufficient data for health analysis.",
            "roses": [],
            "buds": [],
            "thorns": [],
            "proposals": [],
        }

    metrics = compute_agent_metrics(findings)

    if not metrics:
        return {
            "status": "insufficient_data",
            "verdict": "UNKNOWN",
            "summary": (
                "No agents have enough findings for metric computation "
                f"(need >= {MIN_FINDINGS_FOR_METRICS} per agent)."
            ),
            "roses": [],
            "buds": [],
            "thorns": [],
            "proposals": [],
        }

    roses, buds, thorns = classify_rbt(metrics)

    # Augment with scored_all data for agents not present in results.tsv
    scored_all_data = load_scored_all(project_dir)
    tsv_agents = set(metrics.keys())

    for agent, agent_records in scored_all_data.items():
        if agent in tsv_agents or not agent_records:
            continue
        scores = [rec.get("score", 0) for rec in agent_records]
        if not scores:
            continue
        avg_score = sum(scores) / len(scores)
        max_pts = _rubric_max_score(agent)
        pct = avg_score / max_pts if max_pts > 0 else 0.0

        if pct >= ROSE_PASS_RATE:
            roses.append(agent)
        elif pct >= THORN_PASS_RATE:
            buds.append(agent)
        else:
            thorns.append(agent)

    proposals = generate_proposals(thorns, metrics)

    n_thorns = len(thorns)
    if n_thorns == 0:
        verdict = "HEALTHY"
    elif n_thorns <= 2:
        verdict = "WARNING"
    else:
        verdict = "CRITICAL"

    summary = (
        f"Fleet health: {len(roses)} roses, {len(buds)} buds, {n_thorns} thorns. "
        f"{len(proposals)} proposal(s) generated."
    )

    project_name = campaign or project_dir.name
    output_dir.mkdir(parents=True, exist_ok=True)
    write_proposals_json(
        output_path=output_dir / "proposals.json",
        campaign=project_name,
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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VIGIL — fleet health monitor for Masonry agent campaigns."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Path to the project directory (default: cwd).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for proposals.json (default: <project>/masonry/vigil).",
    )
    parser.add_argument(
        "--campaign",
        type=str,
        default=None,
        help="Campaign label written into proposals.json (default: project dir name).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    project_dir: Path = args.project.resolve()
    output_dir: Path = (
        args.output.resolve()
        if args.output
        else project_dir / "masonry" / "vigil"
    )

    result = run_vigil(
        project_dir=project_dir,
        output_dir=output_dir,
        campaign=args.campaign,
    )

    print(f"Verdict : {result['verdict']}")
    print(f"Summary : {result['summary']}")
    if result.get("roses"):
        print(f"Roses   : {', '.join(result['roses'])}")
    if result.get("buds"):
        print(f"Buds    : {', '.join(result['buds'])}")
    if result.get("thorns"):
        print(f"Thorns  : {', '.join(result['thorns'])}")
    if result.get("proposals"):
        print(f"\n{len(result['proposals'])} proposal(s) written to {output_dir / 'proposals.json'}")

    return 0 if result["verdict"] in ("HEALTHY", "UNKNOWN") else 1


if __name__ == "__main__":
    sys.exit(main())
