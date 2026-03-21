"""Score existing findings for DSPy training data quality.

Discovers all findings across project subdirectories, scores them on three
rule-based dimensions (confidence calibration, evidence quality, verdict clarity),
and writes training-ready records (score >= 60) to a JSONL file.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Valid verdict set (mirrors masonry.src.schemas.payloads.VALID_VERDICTS)
# ---------------------------------------------------------------------------

VALID_VERDICTS: frozenset[str] = frozenset({
    "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "DIAGNOSIS_COMPLETE",
    "FIXED", "FIX_FAILED", "COMPLIANT", "NON_COMPLIANT", "PARTIAL",
    "NOT_APPLICABLE", "CALIBRATED", "UNCALIBRATED", "NOT_MEASURABLE",
    "IMPROVEMENT", "REGRESSION", "IMMINENT", "PROBABLE", "POSSIBLE",
    "UNLIKELY", "OK", "DEGRADED", "DEGRADED_TRENDING", "ALERT", "UNKNOWN",
    "PROMISING", "BLOCKED", "WEAK", "SUBJECTIVE", "PENDING_EXTERNAL",
})

# Severity labels that indicate high-stakes findings
_CRITICAL_SEVERITIES = frozenset({"Critical", "High"})
_CRITICAL_VERDICTS = frozenset({
    "FAILURE", "INCONCLUSIVE", "NON_COMPLIANT", "UNCALIBRATED",
    "REGRESSION", "IMMINENT", "DEGRADED", "DEGRADED_TRENDING", "ALERT",
    "WEAK", "FIX_FAILED",
})

# Regex patterns for field extraction
_RE_VERDICT = re.compile(r"\*\*Verdict\*\*\s*:\s*([A-Z_]+)", re.IGNORECASE)
_RE_SEVERITY = re.compile(r"\*\*Severity\*\*\s*:\s*(Critical|High|Medium|Low|Info)", re.IGNORECASE)
_RE_CONFIDENCE = re.compile(r"\*\*Confidence\*\*\s*:\s*([0-9.]+)", re.IGNORECASE)
_RE_AGENT = re.compile(r"\*\*Agent\*\*\s*:\s*([^\n]+)", re.IGNORECASE)
_RE_QUESTION = re.compile(r"\*\*Question\*\*\s*:\s*([^\n]+)", re.IGNORECASE)
_RE_HEADER_ID = re.compile(r"^#\s+Finding\s*:\s*([^\s—–-][^\s]*)", re.IGNORECASE | re.MULTILINE)
_RE_NUMBERS = re.compile(r"\b\d+\.?\d*\b")

TRAINING_THRESHOLD = 60


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------

def extract_finding_fields(path: Path) -> dict[str, Any]:
    """Extract structured fields from a finding markdown file.

    Returns a dict with keys: question_id, agent, verdict, severity,
    confidence, question_text, summary, evidence.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""

    # question_id: from header, else stem filename
    qid_match = _RE_HEADER_ID.search(text)
    if qid_match:
        question_id = qid_match.group(1).strip()
    else:
        question_id = path.stem

    # agent
    agent_match = _RE_AGENT.search(text)
    agent = agent_match.group(1).strip() if agent_match else "unknown"

    # verdict — strip inline annotations like "(7.97x at...)"
    verdict_match = _RE_VERDICT.search(text)
    if verdict_match:
        raw_verdict = verdict_match.group(1).strip().upper()
        # Take only the first token (handles "WARNING (7.97x...)")
        verdict = raw_verdict.split()[0] if raw_verdict else ""
    else:
        verdict = ""

    # severity — strip inline text after em-dash
    severity_match = _RE_SEVERITY.search(text)
    if severity_match:
        raw_sev = severity_match.group(1).strip()
        severity = raw_sev.split()[0] if raw_sev else ""
    else:
        severity = ""

    # confidence
    conf_match = _RE_CONFIDENCE.search(text)
    if conf_match:
        try:
            confidence: float | None = float(conf_match.group(1))
        except ValueError:
            confidence = None
    else:
        confidence = None

    # question_text: from **Question**: field, else header subtitle
    q_match = _RE_QUESTION.search(text)
    if q_match:
        question_text = q_match.group(1).strip()
    else:
        # Try to extract subtitle from header: "# Finding: Q1.1 — <text>"
        sub_match = re.search(r"^#\s+Finding\s*:[^—–\n]*[—–]\s*(.+)$", text, re.MULTILINE)
        question_text = sub_match.group(1).strip() if sub_match else ""

    # evidence: content of ## Evidence section
    evidence = _extract_section(text, "Evidence")

    # summary: first non-empty line after the header block (simplified)
    summary = _build_summary(text, verdict, severity)

    return {
        "question_id": question_id,
        "agent": agent,
        "verdict": verdict,
        "severity": severity,
        "confidence": confidence,
        "question_text": question_text,
        "summary": summary,
        "evidence": evidence,
    }


def _extract_section(text: str, section_name: str) -> str:
    """Return the body of a markdown ## Section, or empty string."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*\n(.*?)(?=^##|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return ""


def _build_summary(text: str, verdict: str, severity: str) -> str:
    """Build a short summary from available text."""
    # Use the first substantive line after the metadata block
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("**")
            and not stripped.startswith("```")
            and len(stripped) > 10
        ):
            return stripped[:200]
    return f"{verdict} / {severity}" if verdict else "no summary"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_confidence_calibration(
    confidence: float | None,
    verdict: str,
    severity: str,
) -> int:
    """Score confidence calibration dimension (0-40 points)."""
    points = 0

    if confidence is None:
        return 0

    # +10: confidence field present
    points += 10

    # +15: confidence in non-extreme range 0.5-0.95
    if 0.5 <= confidence <= 0.95:
        points += 15

        # +15: confidence matches verdict severity
        # High-stakes (CRITICAL verdict / Critical|High severity) → expect high confidence (> 0.7)
        # Low-stakes (HEALTHY/OK/Info) → expect moderate-to-lower confidence (≤ 0.85)
        is_critical = verdict in _CRITICAL_VERDICTS or severity in _CRITICAL_SEVERITIES
        if is_critical and confidence >= 0.70:
            points += 15
        elif not is_critical and confidence <= 0.85:
            points += 15

    return points


def _score_evidence_quality(evidence: str) -> int:
    """Score evidence quality dimension (0-40 points)."""
    points = 0

    if not evidence:
        return 0

    # +10: has evidence section with content
    points += 10

    # +15: evidence is 50+ characters
    if len(evidence) >= 50:
        points += 15

        # +15: evidence includes specific numbers/values/thresholds
        numbers = _RE_NUMBERS.findall(evidence)
        if len(numbers) >= 2:  # at least two numeric values
            points += 15

    return points


def _score_verdict_clarity(verdict: str) -> int:
    """Score verdict clarity dimension (0-20 points)."""
    if not verdict:
        return 0

    # +10: verdict field present and non-empty
    points = 10

    # +10: verdict is from the known valid set
    if verdict.upper() in VALID_VERDICTS:
        points += 10

    return points


def score_finding(path: Path) -> dict[str, Any]:
    """Score a single finding file on three dimensions.

    Returns a dict with keys: score, score_breakdown, fields.
    """
    fields = extract_finding_fields(path)

    confidence_cal = _score_confidence_calibration(
        fields["confidence"], fields["verdict"], fields["severity"]
    )
    evidence_qual = _score_evidence_quality(fields["evidence"])
    verdict_clar = _score_verdict_clarity(fields["verdict"])

    total = confidence_cal + evidence_qual + verdict_clar

    return {
        "score": total,
        "score_breakdown": {
            "confidence_calibration": confidence_cal,
            "evidence_quality": evidence_qual,
            "verdict_clarity": verdict_clar,
        },
        "fields": fields,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_findings(base_dir: Path) -> list[Path]:
    """Discover all finding .md files under base_dir.

    Scans:
      - base_dir/*/findings/*.md  (project subdirectories)
      - base_dir/findings/*.md    (root-level findings)

    Excludes synthesis.md and non-.md files.
    """
    found: list[Path] = []

    def _collect(findings_dir: Path) -> None:
        if not findings_dir.is_dir():
            return
        for p in findings_dir.iterdir():
            if p.suffix == ".md" and p.name != "synthesis.md":
                found.append(p)

    # Root-level findings/
    _collect(base_dir / "findings")

    # Project subdirectory findings/
    for child in base_dir.iterdir():
        if child.is_dir() and child.name not in ("findings", "masonry", ".git"):
            _collect(child / "findings")

    return found


# ---------------------------------------------------------------------------
# JSONL output
# ---------------------------------------------------------------------------

def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write records to a JSONL file, creating parent dirs as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(
    base_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Score all findings and write training-ready records to output_path.

    Returns a summary dict with keys:
      scanned, training_ready, agents_with_10_plus, output_path
    """
    paths = discover_findings(base_dir)

    training_records: list[dict[str, Any]] = []
    agent_counts: dict[str, int] = defaultdict(int)

    for finding_path in paths:
        scored = score_finding(finding_path)
        fields = scored["fields"]

        if scored["score"] >= TRAINING_THRESHOLD:
            record = {
                "question_id": fields["question_id"],
                "agent": fields["agent"],
                "score": scored["score"],
                "input": {
                    "question_text": fields["question_text"],
                    "question_id": fields["question_id"],
                },
                "output": {
                    "verdict": fields["verdict"],
                    "severity": fields["severity"],
                    "confidence": fields["confidence"],
                    "summary": fields["summary"],
                    "evidence": fields["evidence"],
                },
            }
            training_records.append(record)
            agent_counts[fields["agent"]] += 1

    write_jsonl(training_records, output_path)

    agents_with_10_plus = {
        agent: count for agent, count in agent_counts.items() if count >= 10
    }

    return {
        "scanned": len(paths),
        "training_ready": len(training_records),
        "agents_with_10_plus": agents_with_10_plus,
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Score findings for DSPy training data.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: cwd)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("masonry/training_data/scored_findings.jsonl"),
        help="Output JSONL path",
    )
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, output_path=args.output)

    print(f"Scanned: {summary['scanned']} findings")
    print(f"Scored >= {TRAINING_THRESHOLD} (training-ready): {summary['training_ready']} findings")
    if summary["agents_with_10_plus"]:
        agents_str = ", ".join(
            f"{a} ({c})" for a, c in sorted(summary["agents_with_10_plus"].items())
        )
        print(f"Agents with >= 10 training examples: {agents_str}")
    print(f"Written to: {summary['output_path']}")


if __name__ == "__main__":
    _main()
