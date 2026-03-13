"""
bl/findings.py — Finding writer, failure classifier, and results.tsv updater.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from bl.config import cfg

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
    """
    verdict = result.get("verdict", "")
    if verdict in ("HEALTHY", "WARNING"):
        return None

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
