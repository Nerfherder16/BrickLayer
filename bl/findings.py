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

_NON_FAILURE_VERDICTS = frozenset(
    {
        "HEALTHY",
        "WARNING",
        "DIAGNOSIS_COMPLETE",
        "PENDING_EXTERNAL",
        "PROMISING",
        "WEAK",
        "CALIBRATED",
        "FIXED",
        "COMPLIANT",
        "PARTIAL",
        "NOT_APPLICABLE",
        "IMPROVEMENT",
        "OK",
        "POSSIBLE",
        "UNLIKELY",
        "DEGRADED_TRENDING",
        "SUBJECTIVE",
        "NOT_MEASURABLE",
        "UNCALIBRATED",
        # Monitor-mode verdicts (F2.2 fix — previously missing, caused false failure classification)
        "DEGRADED",
        "ALERT",
        "UNKNOWN",
        # Frontier verdict (F2.2 fix — BLOCKED is not a failure, it's a prerequisite gap)
        "BLOCKED",
    }
)

_CONFIDENCE_FLOAT = {"high": 0.9, "medium": 0.6, "low": 0.3, "uncertain": 0.1}


def classify_failure_type(result: dict, mode: str) -> str | None:
    """
    Classify why a question failed. Returns one of:
      syntax | logic | hallucination | tool_failure | timeout | unknown
    Returns None when verdict is HEALTHY or WARNING — no failure to classify.

    Tries local model (Ollama) first; falls back to keyword heuristic if
    local inference is unavailable or returns an unexpected value.
    """
    verdict = result.get("verdict", "")
    if verdict in _NON_FAILURE_VERDICTS:
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
    # Original
    "HEALTHY": 1.0,
    "FAILURE": 1.0,
    "WARNING": 0.7,
    "INCONCLUSIVE": 0.0,
    # Frontier
    "PROMISING": 0.8,
    "WEAK": 0.6,
    "BLOCKED": 0.5,
    # Benchmark
    "CALIBRATED": 1.0,
    "UNCALIBRATED": 0.7,
    "NOT_MEASURABLE": 0.3,
    # Fix
    "FIXED": 1.0,
    "FIX_FAILED": 1.0,
    # Diagnose
    "DIAGNOSIS_COMPLETE": 1.0,
    # Audit
    "COMPLIANT": 1.0,
    "NON_COMPLIANT": 1.0,
    "PARTIAL": 0.7,
    "NOT_APPLICABLE": 0.5,
    # Evolve
    "IMPROVEMENT": 1.0,
    "REGRESSION": 1.0,
    # Predict
    "IMMINENT": 1.0,
    "PROBABLE": 0.8,
    "POSSIBLE": 0.6,
    "UNLIKELY": 0.4,
    # Monitor
    "OK": 1.0,
    "DEGRADED": 0.8,
    "DEGRADED_TRENDING": 0.7,
    "ALERT": 1.0,
    "UNKNOWN": 0.1,
    # Any
    "PENDING_EXTERNAL": 0.5,
    "SUBJECTIVE": 0.2,
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
        # Original
        "FAILURE": "High",
        "WARNING": "Medium",
        "HEALTHY": "Info",
        "INCONCLUSIVE": "Low",
        # Frontier
        "PROMISING": "Info",
        "WEAK": "Low",
        "BLOCKED": "Medium",
        # Benchmark
        "CALIBRATED": "Info",
        "UNCALIBRATED": "Medium",
        "NOT_MEASURABLE": "Low",
        # Fix
        "FIXED": "Info",
        "FIX_FAILED": "High",
        # Audit
        "COMPLIANT": "Info",
        "NON_COMPLIANT": "High",
        "PARTIAL": "Medium",
        "NOT_APPLICABLE": "Low",
        # Evolve
        "IMPROVEMENT": "Info",
        "REGRESSION": "High",
        # Predict
        "IMMINENT": "Critical",
        "PROBABLE": "High",
        "POSSIBLE": "Medium",
        "UNLIKELY": "Low",
        # Monitor
        "OK": "Info",
        "DEGRADED": "Medium",
        "DEGRADED_TRENDING": "Medium",
        "ALERT": "High",
        "UNKNOWN": "Low",
        # Any mode
        "DIAGNOSIS_COMPLETE": "Info",
        "PENDING_EXTERNAL": "Low",
        "SUBJECTIVE": "Low",
    }

    # C-30: enforce code_audit constraints
    question_type = question.get("question_type", "behavioral")
    if question_type == "code_audit":
        # Cap confidence at medium
        current_conf = result.get("confidence", "")
        if current_conf == "high":
            result = dict(result)
            result["confidence"] = "medium"
        # Downgrade HEALTHY → WARNING for code_audit
        if result.get("verdict") == "HEALTHY":
            result = dict(result)
            result["verdict"] = "WARNING"
            orig_summary = result.get("summary", "")
            result["summary"] = (
                orig_summary
                + " (C-30: CODE-AUDIT questions cannot produce HEALTHY verdicts"
                " — requires live HTTP/test evidence)"
            )

    verdict = result["verdict"]
    severity = severity_map.get(verdict, "Low")

    failure_type = result.get("failure_type")
    failure_type_line = f"\n**Failure Type**: {failure_type}" if failure_type else ""
    type_label = "CODE-AUDIT" if question_type == "code_audit" else "BEHAVIORAL"

    conf_str = result.get("confidence", "uncertain")
    confidence_float = _CONFIDENCE_FLOAT.get(conf_str, 0.1)
    needs_human = confidence_float < 0.35

    content = f"""# Finding: {qid} — {question["title"]}

**Question**: {question["hypothesis"]}
**Verdict**: {verdict}
**Severity**: {severity}{failure_type_line}
**Mode**: {question.get("operational_mode", question["mode"])}
**Type**: {type_label}
**Target**: {question["target"]}
**Confidence**: {confidence_float}
**Needs Human**: {needs_human}

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
    qid: str,
    verdict: str,
    summary: str,
    failure_type: str | None = None,
    eval_score: float | None = None,
) -> None:
    """Upsert a result row in results.tsv."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not cfg.results_tsv.exists():
        cfg.results_tsv.write_text(
            "question_id\tverdict\tfailure_type\teval_score\tsummary\ttimestamp\n",
            encoding="utf-8",
        )

    lines = cfg.results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    ft = failure_type or ""
    score_str = f"{eval_score:.3f}" if eval_score is not None else ""
    safe_summary = summary.replace("\t", " ")[:120]
    new_row = f"{qid}\t{verdict}\t{ft}\t{score_str}\t{safe_summary}\t{timestamp}"

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
    _mark_question_done(qid, verdict)


# ---------------------------------------------------------------------------
# C-31: atomic questions.md status update
# ---------------------------------------------------------------------------


def _mark_question_done(qid: str, verdict: str) -> None:
    """Update **Status**: PENDING → DONE/INCONCLUSIVE in questions.md for this qid."""
    if not cfg.questions_md.exists():
        return
    _PRESERVE_AS_IS = frozenset(
        {
            "INCONCLUSIVE",
            "DIAGNOSIS_COMPLETE",
            "PENDING_EXTERNAL",
            "FIXED",
            "FIX_FAILED",
            "BLOCKED",
            # F8.2: preserve failure/violation verdicts for human visibility in questions.md
            "FAILURE",
            "NON_COMPLIANT",
            "WARNING",
            "REGRESSION",
            "ALERT",
            "HEAL_EXHAUSTED",  # F-mid.1: exhausted heal loop — preserve for human visibility
        }
    )
    new_status = verdict if verdict in _PRESERVE_AS_IS else "DONE"
    text = cfg.questions_md.read_text(encoding="utf-8", errors="replace")
    block_start = text.find(f"## {qid} [")
    if block_start == -1:
        block_start = text.find(f"## {qid}\n")
    if block_start == -1:
        return
    next_block = text.find(
        "\n## ", block_start + 1
    )  # F4.3: match any ## header (not just Q-prefix)
    block_end = next_block if next_block != -1 else len(text)
    block = text[block_start:block_end]
    if "**Status**: PENDING" not in block:
        return
    new_block = block.replace("**Status**: PENDING", f"**Status**: {new_status}", 1)
    cfg.questions_md.write_text(
        text[:block_start] + new_block + text[block_end:], encoding="utf-8"
    )
