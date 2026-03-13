"""
bl/findings.py — Finding writer, failure classifier, and results.tsv updater.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from bl.config import cfg
from bl.local_inference import (
    classify_confidence_local,
    classify_failure_type_local,
    score_result_local,
)

# ---------------------------------------------------------------------------
# Failure taxonomy
# ---------------------------------------------------------------------------

_FAILURE_TYPES = frozenset(
    ("syntax", "logic", "hallucination", "tool_failure", "timeout", "unknown")
)


def classify_failure_type(result: dict, mode: str) -> str | None:
    """
    Classify why a question failed. Returns one of:
      syntax | logic | hallucination | tool_failure | timeout | unknown
    Returns None when verdict is HEALTHY or WARNING — no failure to classify.

    Tries local model (Ollama) first; falls back to keyword heuristic if
    local inference is unavailable or returns an unexpected value.
    """
    verdict = result.get("verdict", "")
    if verdict in ("HEALTHY", "WARNING"):
        return None

    # Try local model first
    local = classify_failure_type_local(result, mode)
    if local:
        return local

    # Heuristic fallback
    details = (result.get("details", "") or "").lower()
    summary = (result.get("summary", "") or "").lower()
    combined = details + " " + summary

    if any(
        s in combined
        for s in (
            "timeout",
            "timed out",
            "readtimeout",
            "connecttimeout",
            "time limit exceeded",
        )
    ):
        return "timeout"

    if any(
        s in combined
        for s in (
            "connection refused",
            "connection error",
            "importerror",
            "modulenotfounderror",
            "no module named",
            "oserror",
            "permissionerror",
            "filenotfounderror",
            "subprocess failed",
            "process exited",
            "returncode",
            "could not connect",
            "httpstatuserror",
            "network error",
        )
    ):
        return "tool_failure"

    if any(
        s in combined
        for s in (
            "syntaxerror",
            "indentationerror",
            "parse error",
            "syntax error",
            "invalid syntax",
        )
    ):
        return "syntax"

    if mode in ("correctness", "performance"):
        return "logic"

    if mode in ("agent", "quality", "static"):
        if any(
            s in combined
            for s in (
                "no evidence",
                "cannot verify",
                "no concrete",
                "assumed",
                "unclear",
                "speculative",
                "no data",
                "not found in",
                "could not find evidence",
            )
        ):
            return "hallucination"

    return "unknown"


# ---------------------------------------------------------------------------
# Confidence signaling
# ---------------------------------------------------------------------------

CONFIDENCE_ROUTING: dict[str, str] = {
    "high": "accept",
    "medium": "validate",
    "low": "escalate",
    "uncertain": "re-run",
}


def classify_confidence(result: dict, mode: str) -> str:
    """
    Estimate how much trust to place in this verdict.
    Returns: high | medium | low | uncertain

    Tries local model (Ollama) first; falls back to structured heuristic if
    local inference is unavailable or returns an unexpected value.
    """
    verdict = result.get("verdict", "")

    # INCONCLUSIVE always uncertain — we don't know what happened
    if verdict == "INCONCLUSIVE":
        return "uncertain"

    # Try local model first
    local = classify_confidence_local(result)
    if local:
        return local

    # Heuristic fallback
    data = result.get("data", {}) or {}
    details = (result.get("details", "") or "").lower()

    # --- Performance mode ---
    if mode == "performance":
        stages = data.get("stages", [])
        if not stages:
            return "uncertain"
        early_stop = data.get("early_stop_at")
        if early_stop:
            return "low"
        return "high" if len(stages) >= 3 else "medium"

    # --- Correctness mode ---
    if mode == "correctness":
        passed = data.get("passed", 0) or 0
        failed = data.get("failed", 0) or 0
        total = passed + failed
        if total == 0:
            return "uncertain"
        if total >= 10:
            return "high"
        if total >= 3:
            return "medium"
        return "low"

    # --- Agent / quality / static mode ---
    if mode in ("agent", "quality", "static"):
        concrete_signals = (
            "line ",
            "line:",
            ".py:",
            ".rs:",
            ".ts:",
            ".kt:",
            "function ",
            "def ",
            "file:",
            "/src/",
            "test_",
            "error:",
            "warning:",
            "assert",
            "found ",
        )
        evidence_count = sum(1 for s in concrete_signals if s in details)
        if evidence_count >= 4:
            return "high"
        if evidence_count >= 2:
            return "medium"
        if evidence_count >= 1:
            return "low"
        if data and data != {}:
            return "medium"
        return "uncertain"

    # --- Generic fallback by verdict ---
    if verdict == "FAILURE":
        return "high" if details.strip() else "low"
    if verdict == "WARNING":
        return "medium"
    if verdict == "HEALTHY":
        return "high" if details.strip() else "medium"

    return "uncertain"


# ---------------------------------------------------------------------------
# Eval / scoring harness
# ---------------------------------------------------------------------------

_VERDICT_CLARITY: dict[str, float] = {
    "HEALTHY": 1.0,
    "FAILURE": 1.0,
    "WARNING": 0.7,
    "INCONCLUSIVE": 0.0,
}

_CONFIDENCE_EVIDENCE: dict[str, float] = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.3,
    "uncertain": 0.0,
}

_FAILURE_EXECUTION: dict[str, float] = {
    None: 1.0,
    "logic": 0.9,
    "syntax": 0.8,
    "hallucination": 0.4,
    "unknown": 0.5,
    "timeout": 0.3,
    "tool_failure": 0.0,
}


def score_result(result: dict) -> float:
    """
    Score a verdict envelope on a 0.0-1.0 scale.

    Tries local model (Ollama) first; falls back to weighted formula:
      evidence_quality * 0.4 + verdict_clarity * 0.4 + execution_success * 0.2
    """
    # Try local model first
    local = score_result_local(result)
    if local is not None:
        return local

    # Formula fallback
    verdict = result.get("verdict", "INCONCLUSIVE")
    confidence = result.get("confidence", "uncertain")
    failure_type = result.get("failure_type")

    evidence_quality = _CONFIDENCE_EVIDENCE.get(confidence, 0.0)
    verdict_clarity = _VERDICT_CLARITY.get(verdict, 0.0)
    execution_success = _FAILURE_EXECUTION.get(failure_type, 0.5)

    score = (
        (evidence_quality * 0.4) + (verdict_clarity * 0.4) + (execution_success * 0.2)
    )
    return round(score, 3)


# ---------------------------------------------------------------------------
# Finding writer
# ---------------------------------------------------------------------------


def write_finding(question: dict, result: dict) -> Path:
    """Write findings/{qid}.md in BrickLayer finding format. Returns the path."""
    qid = question["id"]
    finding_path = cfg.findings_dir / f"{qid}.md"

    severity_map = {
        "FAILURE": "High",
        "WARNING": "Medium",
        "HEALTHY": "Info",
        "INCONCLUSIVE": "Low",
    }
    verdict = result["verdict"]
    severity = severity_map.get(verdict, "Low")

    failure_type = result.get("failure_type")
    failure_type_line = f"\n**Failure Type**: {failure_type}" if failure_type else ""

    content = f"""# Finding: {qid} — {question["title"]}

**Question**: {question["hypothesis"]}
**Verdict**: {verdict}
**Severity**: {severity}{failure_type_line}
**Mode**: {question["mode"]}
**Target**: {question["target"]}

## Summary

{result["summary"]}

## Evidence

{result["details"][:3000]}

## Raw Data

```json
{json.dumps(result["data"], indent=2)[:2000]}
```

## Verdict Threshold

{question["verdict_threshold"]}

## Mitigation Recommendation

[To be filled by agent analysis]

## Open Follow-up Questions

[Add follow-up questions here if verdict is FAILURE or WARNING]
"""

    finding_path.write_text(content, encoding="utf-8")
    return finding_path


# ---------------------------------------------------------------------------
# Results TSV
# ---------------------------------------------------------------------------


def update_results_tsv(
    qid: str, verdict: str, summary: str, failure_type: str | None = None
) -> None:
    """Upsert a result row in results.tsv."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not cfg.results_tsv.exists():
        cfg.results_tsv.write_text(
            "question_id\tverdict\tfailure_type\tsummary\ttimestamp\n", encoding="utf-8"
        )

    lines = cfg.results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    ft = failure_type or ""
    safe_summary = summary.replace("\t", " ")[:120]
    new_row = f"{qid}\t{verdict}\t{ft}\t{safe_summary}\t{timestamp}"

    updated = False
    new_lines = []
    for line in lines:
        parts = line.split("\t")
        if parts and parts[0] == qid:
            new_lines.append(new_row)
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(new_row)

    cfg.results_tsv.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
