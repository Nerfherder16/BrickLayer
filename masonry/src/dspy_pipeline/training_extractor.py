"""masonry/src/dspy_pipeline/training_extractor.py

Extract and score training examples from BrickLayer findings for DSPy optimization.

Exposes:
  - extract_finding(path) -> dict | None
  - extract_training_data(project_dir) -> list[dict]
  - score_example(finding, agent_db) -> float
  - build_dataset(project_dir, agent_db_path) -> dict[str, list[dict]]
"""

from __future__ import annotations

import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Finding extraction
# ---------------------------------------------------------------------------


def extract_finding(path: Path) -> dict | None:
    """Parse a single finding markdown file into a structured dict.

    Returns ``None`` if the file does not exist or has no **Verdict** line.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None

    # Extract question_id from heading (e.g. "# Finding: Q1.1")
    question_id = None
    heading_match = re.search(r"#\s+Finding:\s*(Q[\d.]+)", text, re.IGNORECASE)
    if heading_match:
        question_id = heading_match.group(1)

    # Extract verdict
    verdict_match = re.search(r"\*\*Verdict\*\*:\s*(\S+)", text)
    if not verdict_match:
        return None
    verdict = verdict_match.group(1).rstrip(".,;")

    # Extract severity
    severity = None
    severity_match = re.search(r"\*\*Severity\*\*:\s*(\S+)", text)
    if severity_match:
        severity = severity_match.group(1).rstrip(".,;")

    # Extract evidence section
    evidence = ""
    evidence_match = re.search(
        r"##\s+Evidence\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if evidence_match:
        evidence = evidence_match.group(1).strip()

    # Extract mitigation section
    mitigation = None
    mitigation_match = re.search(
        r"##\s+Mitigation\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if mitigation_match:
        candidate = mitigation_match.group(1).strip()
        # Treat "No mitigation required" variants as absent
        if candidate and not re.match(r"(?i)no mitigation", candidate):
            mitigation = candidate

    # Extract agent from metadata
    agent = None
    agent_match = re.search(r"-\s+agent:\s*(.+)", text)
    if agent_match:
        agent = agent_match.group(1).strip()

    return {
        "question_id": question_id,
        "verdict": verdict,
        "severity": severity,
        "evidence": evidence,
        "mitigation": mitigation,
        "agent": agent,
    }


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------


def extract_training_data(project_dir: Path) -> list[dict]:
    """Recursively scan *project_dir* for finding markdown files.

    Returns all findings that have a valid verdict, skipping those without.
    """
    project_dir = Path(project_dir)
    if not project_dir.exists():
        return []

    results: list[dict] = []
    for md_file in project_dir.rglob("*.md"):
        finding = extract_finding(md_file)
        if finding is not None:
            results.append(finding)

    return results


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_example(finding: dict, agent_db: dict) -> float:
    """Return a quality weight for a training example based on agent performance.

    Score tiers:
      - agent score >= 0.8 → weight 1.0 (gold)
      - agent score >= 0.5 → weight 0.7 (silver)
      - agent score <  0.5 → weight 0.0 (excluded)
      - agent missing from db or finding has no agent field → weight 0.0
    """
    agent_name = finding.get("agent")
    if not agent_name:
        return 0.0

    db_entry = agent_db.get(agent_name)
    if not db_entry:
        return 0.0

    agent_score = db_entry.get("score", 0.0)
    if agent_score >= 0.8:
        return 1.0
    if agent_score >= 0.5:
        return 0.7
    return 0.0


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------


def build_dataset(project_dir: Path, agent_db_path: Path) -> dict[str, list[dict]]:
    """Build a per-agent training dataset from findings in *project_dir*.

    Only includes findings whose agent has a score >= 0.5 in *agent_db*.
    Findings with no agent match are excluded.

    Returns a dict mapping agent_name -> list of training example dicts.
    """
    project_dir = Path(project_dir)
    agent_db_path = Path(agent_db_path)

    if not agent_db_path.exists():
        return {}

    try:
        agent_db: dict = json.loads(agent_db_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    all_findings = extract_training_data(project_dir)

    dataset: dict[str, list[dict]] = {}
    for finding in all_findings:
        weight = score_example(finding, agent_db)
        if weight == 0.0:
            continue
        agent_name = finding.get("agent") or "unknown"
        dataset.setdefault(agent_name, []).append(finding)

    return dataset
