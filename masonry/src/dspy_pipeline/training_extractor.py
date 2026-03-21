"""Training data extractor for DSPy optimization.

Parses existing BL2.0 findings into DSPy-compatible training examples.
Supports quality-based weighting via agent_db scores.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


# ── Regex patterns for finding field extraction ───────────────────────────

_QUESTION_ID_RE = re.compile(r"^#\s+Finding:\s+(\S+)", re.MULTILINE)
_VERDICT_RE = re.compile(r"^\*\*Verdict\*\*:\s*(\S+)", re.MULTILINE)
_SEVERITY_RE = re.compile(r"^\*\*Severity\*\*:\s*(\S+)", re.MULTILINE)
_SECTION_RE = re.compile(r"^##\s+(\w[\w\s]*)", re.MULTILINE)


def _extract_section(text: str, section_name: str) -> str | None:
    """Extract content of a markdown section by name.

    Returns None if the section is not present.
    """
    # Find the section header
    pattern = re.compile(
        r"^##\s+" + re.escape(section_name) + r"\s*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None
    content = m.group(1).strip()
    return content if content else None


def extract_finding(finding_path: Path) -> dict[str, Any] | None:
    """Parse a single finding .md file into a training example dict.

    Returns None if the file cannot be read or lacks a **Verdict** line.
    """
    try:
        text = finding_path.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError):
        return None

    # Extract verdict (required)
    verdict_m = _VERDICT_RE.search(text)
    if not verdict_m:
        return None

    verdict = verdict_m.group(1).strip()

    # Extract question_id
    qid_m = _QUESTION_ID_RE.search(text)
    question_id = qid_m.group(1).strip() if qid_m else finding_path.stem

    # Extract severity
    sev_m = _SEVERITY_RE.search(text)
    severity = sev_m.group(1).strip() if sev_m else ""

    # Extract sections
    evidence = _extract_section(text, "Evidence") or ""
    mitigation = _extract_section(text, "Mitigation")

    # Skip "No mitigation required" style text
    if mitigation and mitigation.lower().startswith("no mitigation"):
        mitigation = None

    return {
        "question_id": question_id,
        "verdict": verdict,
        "severity": severity,
        "evidence": evidence,
        "mitigation": mitigation,
        "source_file": str(finding_path),
    }


def extract_training_data(projects_dir: Path) -> list[dict[str, Any]]:
    """Scan all findings directories under projects_dir and extract examples.

    Scans `*/findings/*.md` and `*/findings/wave*/*.md` patterns.
    """
    if not projects_dir.exists():
        return []

    results: list[dict[str, Any]] = []

    # Walk all subdirectories looking for `findings/` directories
    for findings_dir in projects_dir.rglob("findings"):
        if not findings_dir.is_dir():
            continue

        # Scan direct children
        for md_file in findings_dir.glob("*.md"):
            finding = extract_finding(md_file)
            if finding is not None:
                results.append(finding)

        # Scan wave subdirectories
        for wave_dir in findings_dir.iterdir():
            if wave_dir.is_dir() and wave_dir.name.startswith("wave"):
                for md_file in wave_dir.glob("*.md"):
                    finding = extract_finding(md_file)
                    if finding is not None:
                        results.append(finding)

    return results


def score_example(finding: dict[str, Any], agent_db: dict[str, Any]) -> float:
    """Score a training example based on the producing agent's quality.

    Returns:
        1.0 — gold: agent score > 0.8
        0.7 — silver: agent score 0.5 to 0.8
        0.0 — excluded: agent score < 0.5, or agent not found
    """
    agent_name = finding.get("agent")
    if not agent_name:
        return 0.0

    agent_entry = agent_db.get(agent_name, {})
    score = agent_entry.get("score", 0.0)

    if score >= 0.8:
        return 1.0
    if score >= 0.5:
        return 0.7
    return 0.0


def build_dataset(
    projects_dir: Path,
    agent_db_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Build a grouped training dataset from project findings.

    Groups examples by agent name. Excludes examples from low-scoring agents.

    Returns:
        Dict mapping agent_name -> list of example dicts.
        Example dicts have keys matching DSPy Signature input/output fields.
    """
    # Load agent_db
    agent_db: dict[str, Any] = {}
    try:
        raw = agent_db_path.read_text(encoding="utf-8")
        agent_db = json.loads(raw)
    except (OSError, FileNotFoundError, json.JSONDecodeError):
        return {}

    findings = extract_training_data(projects_dir)
    dataset: dict[str, list[dict[str, Any]]] = {}

    for finding in findings:
        weight = score_example(finding, agent_db)
        if weight == 0.0:
            continue

        agent_name = finding.get("agent", "unknown")
        if agent_name not in dataset:
            dataset[agent_name] = []

        # Shape the example to match ResearchAgentSig fields
        example = {
            "question_text": finding.get("question_id", ""),
            "project_context": "",
            "constraints": "",
            "verdict": finding.get("verdict", ""),
            "severity": finding.get("severity", ""),
            "evidence": finding.get("evidence", ""),
            "mitigation": finding.get("mitigation", "") or "",
            "confidence": "0.75",  # default calibration
            "_weight": weight,
        }
        dataset[agent_name].append(example)

    return dataset
