"""bl/recall_hook.py — Extract Recall payload from BL 2.0 finding text."""

import json
import re

FAILURE_SET = {"FAILURE", "INCONCLUSIVE", "INCONCLUSIVE-FORMAT-ERROR"}


def extract_recall_payload(
    finding_text: str,
    agent_name: str,
    question_id: str,
    project: str,
) -> dict | None:
    """Parse finding text, extract verdict and summary, build Recall payload.

    Priority order:
    1. Find last fenced ```json block, parse it, use 'verdict' and 'summary'
       (fall back to 'simulation_result' if 'summary' absent)
    2. If no JSON or malformed JSON: regex for '**Verdict**: {WORD}' line,
       grab first 200 chars after '## Evidence' section for summary
    3. Return None if neither path yields a verdict

    Returns dict:
      content: "{agent_name} {question_id}: verdict={verdict}. {summary}"
      domain: "{project}-bricklayer"
      tags: ["bricklayer", "agent:{agent_name}", "type:finding", "verdict:{verdict}"]
      importance: 0.9 if verdict in FAILURE_SET else 0.7
      durability: "durable"
    """
    verdict, summary = _extract_from_json(finding_text)

    if verdict is None:
        verdict, summary = _extract_from_verdict_line(finding_text)

    if verdict is None:
        return None

    return _build_payload(
        verdict=verdict,
        summary=summary or "",
        agent_name=agent_name,
        question_id=question_id,
        project=project,
    )


def _extract_from_json(finding_text: str) -> tuple[str | None, str | None]:
    """Find the last fenced ```json block and parse verdict + summary from it."""
    blocks = re.findall(r"```json\s*(.*?)```", finding_text, re.DOTALL)
    if not blocks:
        return None, None

    last_block = blocks[-1].strip()
    try:
        data = json.loads(last_block)
    except (json.JSONDecodeError, ValueError):
        return None, None

    verdict = data.get("verdict")
    if not verdict:
        return None, None

    summary = data.get("summary") or data.get("simulation_result") or ""
    return str(verdict), str(summary)


def _extract_from_verdict_line(finding_text: str) -> tuple[str | None, str | None]:
    """Regex fallback: extract verdict from **Verdict**: line and summary from ## Evidence."""
    verdict_match = re.search(r"\*\*Verdict\*\*:\s*([\w-]+)", finding_text)
    if not verdict_match:
        return None, None

    verdict = verdict_match.group(1)

    summary = ""
    evidence_match = re.search(r"##\s+Evidence\s*\n+(.*)", finding_text, re.DOTALL)
    if evidence_match:
        summary = evidence_match.group(1)[:200]

    return verdict, summary


def _build_payload(
    verdict: str,
    summary: str,
    agent_name: str,
    question_id: str,
    project: str,
) -> dict:
    """Assemble the Recall payload dict."""
    importance = 0.9 if verdict in FAILURE_SET else 0.7
    content = f"{agent_name} {question_id}: verdict={verdict}. {summary}"
    return {
        "content": content,
        "domain": f"{project}-bricklayer",
        "tags": [
            "bricklayer",
            f"agent:{agent_name}",
            "type:finding",
            f"verdict:{verdict}",
        ],
        "importance": importance,
        "durability": "durable",
    }
