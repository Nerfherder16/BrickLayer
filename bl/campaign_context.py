"""
bl/campaign_context.py — Generate campaign-context.md for agent warm-start.

Writes a compact context file that specialist agents read before processing
questions. Eliminates the need for each agent to re-read the findings dir.

Usage:
    python -m bl.campaign_context --project-root /path/to/project [--wave N]
    # or import and call generate() directly
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Severity ordering (highest first)
# ---------------------------------------------------------------------------

_SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "info": 3,
    "low": 4,
}

_VERDICT_SEVERITY: dict[str, str] = {
    "FAILURE": "high",
    "NON_COMPLIANT": "high",
    "REGRESSION": "high",
    "ALERT": "high",
    "FIX_FAILED": "high",
    "IMMINENT": "critical",
    "PROBABLE": "high",
    "WARNING": "medium",
    "DEGRADED": "medium",
    "DEGRADED_TRENDING": "medium",
    "PARTIAL": "medium",
    "POSSIBLE": "medium",
    "UNCALIBRATED": "medium",
    "BLOCKED": "medium",
}


def _severity_rank(verdict: str, severity_str: str) -> int:
    """Return sort key — lower is higher priority."""
    # Try explicit severity field first
    if severity_str:
        key = severity_str.lower()
        if key in _SEVERITY_RANK:
            return _SEVERITY_RANK[key]
    # Fall back to verdict mapping
    mapped = _VERDICT_SEVERITY.get(verdict, "low")
    return _SEVERITY_RANK.get(mapped, 4)


def _parse_finding(path: Path) -> dict | None:
    """Parse a finding .md file into a dict with id, verdict, severity, summary."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    qid = path.stem

    verdict_m = re.search(r"\*\*Verdict\*\*:\s*(\w+)", text)
    severity_m = re.search(r"\*\*Severity\*\*:\s*(\w+)", text)
    summary_m = re.search(r"## Summary\s*\n(.*)", text)

    verdict = verdict_m.group(1) if verdict_m else "UNKNOWN"
    severity = severity_m.group(1) if severity_m else ""
    summary = (
        summary_m.group(1).strip()[:120]
        if summary_m
        else text[:80].replace("\n", " ").strip()
    )

    return {
        "id": qid,
        "verdict": verdict,
        "severity": severity,
        "summary": summary,
        "rank": _severity_rank(verdict, severity),
    }


def _top_findings(findings_dir: Path, n: int = 5) -> list[dict]:
    """Return the N highest-severity findings, excluding synthesis.md."""
    if not findings_dir.exists():
        return []

    parsed = []
    for md in findings_dir.glob("*.md"):
        if md.stem == "synthesis":
            continue
        f = _parse_finding(md)
        if f:
            parsed.append(f)

    parsed.sort(key=lambda f: f["rank"])
    return parsed[:n]


def _project_summary(project_root: Path) -> str:
    """Return the first non-empty paragraph of project-brief.md."""
    brief = project_root / "project-brief.md"
    if not brief.exists():
        return "No project brief found."
    text = brief.read_text(encoding="utf-8", errors="replace")
    # Skip leading headings and blank lines; grab first paragraph
    lines = text.splitlines()
    para_lines: list[str] = []
    in_para = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if in_para:
                break
            continue
        if stripped:
            in_para = True
            para_lines.append(stripped)
        elif in_para:
            break
    return " ".join(para_lines)[:400] if para_lines else "No project brief found."


def _open_hypotheses(project_root: Path, min_weight: float = 1.5) -> list[str]:
    """Return high-weight PENDING question IDs from .bl-weights.json, or [] if absent."""
    weights_path = project_root / ".bl-weights.json"
    if not weights_path.exists():
        return []
    try:
        data = json.loads(weights_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    high: list[tuple[float, str]] = []
    for qid, info in data.items():
        if isinstance(info, dict):
            w = float(info.get("weight", 1.0))
            status = info.get("status", "PENDING")
        else:
            w = float(info)
            status = "PENDING"
        if status == "PENDING" and w >= min_weight:
            high.append((w, qid))

    high.sort(reverse=True)
    return [qid for _, qid in high[:10]]


def _detect_wave(project_root: Path) -> int:
    """Estimate current wave from results.tsv row count (roughly 10 per wave)."""
    tsv = project_root / "results.tsv"
    if not tsv.exists():
        return 1
    try:
        lines = tsv.read_text(encoding="utf-8").splitlines()
        count = max(0, len(lines) - 1)  # subtract header
        return max(1, (count // 10) + 1)
    except OSError:
        return 1


def generate(project_root: Path, wave: int | None = None) -> Path:
    """
    Build campaign-context.md and write it to project_root.
    Returns the path written.
    """
    project_root = Path(project_root).resolve()
    wave = wave or _detect_wave(project_root)
    project_name = project_root.name

    summary = _project_summary(project_root)
    findings = _top_findings(project_root / "findings")
    hypotheses = _open_hypotheses(project_root)

    # Build findings section
    if findings:
        findings_lines = [
            f"- **{f['id']}** [{f['verdict']}]: {f['summary']}" for f in findings
        ]
        findings_section = "\n".join(findings_lines)
    else:
        findings_section = "_No findings yet._"

    # Build hypotheses section
    if hypotheses:
        hyp_section = ", ".join(hypotheses)
    else:
        hyp_section = (
            "_None above weight threshold (run more questions to generate weights)._"
        )

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content = f"""# Campaign Context — {project_name} (Wave {wave})

_Generated: {timestamp} — Read this before processing any question._

## Project

{summary}

## Top Findings

{findings_section}

## Open Hypotheses

High-weight PENDING questions (priority targets):
{hyp_section}
"""

    out_path = project_root / "campaign-context.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate campaign-context.md")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to the BrickLayer project directory (default: cwd)",
    )
    parser.add_argument(
        "--wave",
        type=int,
        default=None,
        help="Wave number override (auto-detected from results.tsv if omitted)",
    )
    args = parser.parse_args()
    out = generate(Path(args.project_root), wave=args.wave)
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
