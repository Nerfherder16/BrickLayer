"""
bl/findings.py — Finding writer and results.tsv updater.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from bl.config import cfg


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

    content = f"""# Finding: {qid} — {question["title"]}

**Question**: {question["hypothesis"]}
**Verdict**: {verdict}
**Severity**: {severity}
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


def update_results_tsv(qid: str, verdict: str, summary: str) -> None:
    """Upsert a result row in results.tsv."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not cfg.results_tsv.exists():
        cfg.results_tsv.write_text(
            "question_id\tverdict\tsummary\ttimestamp\n", encoding="utf-8"
        )

    lines = cfg.results_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    safe_summary = summary.replace("\t", " ")[:120]
    new_row = f"{qid}\t{verdict}\t{safe_summary}\t{timestamp}"

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
