"""
bl/questions.py — Question bank I/O.

Parses questions.md and reads/writes question status via results.tsv.
"""

import re

from bl.config import cfg


def parse_questions() -> list[dict]:
    """Parse questions.md and return list of question dicts."""
    text = cfg.questions_md.read_text(encoding="utf-8")

    block_pattern = re.compile(
        r"^## (Q[\d.]+\w*) \[(\w+)\] (.+?)$",
        re.MULTILINE,
    )
    field_pattern = re.compile(
        r"^\*\*(Mode|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source)\*\*:\s*(.+?)(?=\n\*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    matches = list(block_pattern.finditer(text))
    questions = []

    for i, m in enumerate(matches):
        qid = m.group(1)
        mode_raw = m.group(2).lower()
        title = m.group(3).strip()

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        fields = {}
        for fm in field_pattern.finditer(body):
            fields[fm.group(1).lower().replace(" ", "_")] = fm.group(2).strip()

        status = get_question_status(qid)

        questions.append(
            {
                "id": qid,
                "mode": mode_raw,
                "title": title,
                "status": status,
                "target": fields.get("target", ""),
                "hypothesis": fields.get("hypothesis", ""),
                "test": fields.get("test", ""),
                "verdict_threshold": fields.get("verdict_threshold", ""),
                "agent_name": fields.get("agent", "").strip(),
                "finding": fields.get("finding", "").strip(),
                "source": fields.get("source", "").strip(),
            }
        )

    return questions


def get_question_status(qid: str) -> str:
    """Read current verdict from results.tsv. Returns 'PENDING' if not found."""
    if not cfg.results_tsv.exists():
        return "PENDING"
    for line in cfg.results_tsv.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        parts = line.split("\t")
        if parts and parts[0] == qid:
            return parts[1].strip() if len(parts) > 1 else "PENDING"
    return "PENDING"


def get_next_pending(questions: list[dict]) -> dict | None:
    """Return the first PENDING question, or None."""
    for q in questions:
        if q["status"] == "PENDING":
            return q
    return None


def get_question_by_id(questions: list[dict], qid: str) -> dict | None:
    """Return the question with the given ID, or None."""
    for q in questions:
        if q["id"] == qid:
            return q
    return None
