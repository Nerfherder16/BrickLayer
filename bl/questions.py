"""
bl/questions.py — Question bank I/O.

Parses questions.md and reads/writes question status via results.tsv.
"""

import re
from pathlib import Path

from bl.config import cfg

# C-30: tags that require live evidence vs. static analysis only
_BEHAVIORAL_TAGS = frozenset(
    ("performance", "correctness", "agent", "http", "benchmark")
)
_CODE_AUDIT_TAGS = frozenset(("quality", "static", "code-audit"))


def parse_questions() -> list[dict]:
    """Parse questions.md and return list of question dicts."""
    text = cfg.questions_md.read_text(encoding="utf-8")

    block_pattern = re.compile(
        r"^## ([\w][\w.-]*) \[(\w+)\] (.+?)$",  # F4.3: accept BL 2.0 IDs (D1, F2.1, A4...) not just Q-prefix
        re.MULTILINE,
    )
    field_pattern = re.compile(
        r"^\*\*(Mode|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source|Operational Mode|Resume After)\*\*:\s*(.+?)(?=\n\*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    matches = list(block_pattern.finditer(text))
    questions = []

    for i, m in enumerate(matches):
        qid = m.group(1)
        tag_raw = m.group(2)
        mode_raw = tag_raw.lower()
        title = m.group(3).strip()

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        fields = {}
        for fm in field_pattern.finditer(body):
            fields[fm.group(1).lower().replace(" ", "_")] = fm.group(2).strip()

        # C-30: derive question_type from header tag or explicit **Type** field
        explicit_type = fields.get("type", "").lower()
        tag_lower = tag_raw.lower()
        if explicit_type in ("behavioral", "code_audit"):
            question_type = explicit_type
        elif tag_lower in _CODE_AUDIT_TAGS:
            question_type = "code_audit"
        elif tag_lower in _BEHAVIORAL_TAGS:
            question_type = "behavioral"
        else:
            question_type = "behavioral"  # default

        status = get_question_status(qid)

        questions.append(
            {
                "id": qid,
                "mode": fields.get(
                    "mode", mode_raw
                ),  # F5.1: body **Mode** field takes priority over bracket tag
                "title": title,
                "status": status,
                "question_type": question_type,
                "target": fields.get("target", ""),
                "hypothesis": fields.get("hypothesis", ""),
                "test": fields.get("test", ""),
                "verdict_threshold": fields.get("verdict_threshold", ""),
                "agent_name": fields.get("agent", "").strip(),
                "finding": fields.get("finding", "").strip(),
                "source": fields.get("source", "").strip(),
                "operational_mode": fields.get("operational_mode", "diagnose"),
                "resume_after": fields.get("resume_after", "").strip(),
            }
        )

    return questions


def load_questions(path: str) -> list[dict]:
    """Parse questions.md from an arbitrary path, using results.tsv in the same directory."""
    questions_path = Path(path)
    results_path = questions_path.parent / "results.tsv"
    text = questions_path.read_text(encoding="utf-8")

    block_pattern = re.compile(
        r"^## ([\w][\w.-]*) \[(\w+)\] (.+?)$",
        re.MULTILINE,
    )
    field_pattern = re.compile(
        r"^\*\*(Mode|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source|Operational Mode|Resume After)\*\*:\s*(.+?)(?=\n\*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def _status(qid: str) -> str:
        if not results_path.exists():
            return "PENDING"
        for line in results_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            parts = line.split("\t")
            if parts and parts[0] == qid:
                return parts[1].strip() if len(parts) > 1 else "PENDING"
        return "PENDING"

    matches = list(block_pattern.finditer(text))
    questions = []

    for i, m in enumerate(matches):
        qid = m.group(1)
        tag_raw = m.group(2)
        mode_raw = tag_raw.lower()
        title = m.group(3).strip()

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        fields = {}
        for fm in field_pattern.finditer(body):
            fields[fm.group(1).lower().replace(" ", "_")] = fm.group(2).strip()

        tag_lower = tag_raw.lower()
        explicit_type = fields.get("type", "").lower()
        if explicit_type in ("behavioral", "code_audit"):
            question_type = explicit_type
        elif tag_lower in _CODE_AUDIT_TAGS:
            question_type = "code_audit"
        elif tag_lower in _BEHAVIORAL_TAGS:
            question_type = "behavioral"
        else:
            question_type = "behavioral"

        questions.append(
            {
                "id": qid,
                "mode": fields.get("mode", mode_raw),
                "title": title,
                "status": _status(qid),
                "question_type": question_type,
                "target": fields.get("target", ""),
                "hypothesis": fields.get("hypothesis", ""),
                "test": fields.get("test", ""),
                "verdict_threshold": fields.get("verdict_threshold", ""),
                "agent_name": fields.get("agent", "").strip(),
                "finding": fields.get("finding", "").strip(),
                "source": fields.get("source", "").strip(),
                "operational_mode": fields.get("operational_mode", "diagnose"),
                "resume_after": fields.get("resume_after", "").strip(),
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


_PARKED_STATUSES = frozenset(
    (
        "DIAGNOSIS_COMPLETE",
        "PENDING_EXTERNAL",
        "DEPLOYMENT_BLOCKED",  # Q6.3: diagnosed but awaiting deployment; re-check suppressed
        "DONE",
        "INCONCLUSIVE",
        "FIXED",
        "FIX_FAILED",
        "COMPLIANT",
        "NON_COMPLIANT",
        "CALIBRATED",
        "BLOCKED",
        "HEAL_EXHAUSTED",  # F-mid.1: exhausted heal loop — human intervention required
    )
)

# Question IDs referenced in resume_after fields (e.g. "Q6.3" or "after Q6.3 is DONE")
# are matched by this pattern.
import re as _re

_QREF_PATTERN = _re.compile(r"\b([A-Za-z]\d+(?:\.\d+)?)\b")


def get_next_pending(questions: list[dict]) -> dict | None:
    """Return the first PENDING question, skipping parked/terminal statuses.

    resume_after supports two formats:
      - ISO-8601 datetime string: skip until that time has passed
      - Question-ID reference (e.g. "Q6.3" or "after Q6.3 is DONE"):
        skip until the referenced question reaches a resolved status
    """
    from datetime import datetime, timezone

    # Statuses that count as "resolved" for resume_after question-ID references.
    _RESOLVED = frozenset(
        (
            "DONE",
            "HEALTHY",
            "WARNING",
            "FAILURE",
            "INCONCLUSIVE",
            "FIXED",
            "FIX_FAILED",
            "COMPLIANT",
            "NON_COMPLIANT",
            "CALIBRATED",
            "HEAL_EXHAUSTED",
        )
    )

    now = datetime.now(timezone.utc)
    for q in questions:
        if q["status"] in _PARKED_STATUSES:
            continue
        if q["status"] != "PENDING":
            continue
        resume_after = q.get("resume_after", "")
        if resume_after:
            # Try ISO-8601 datetime first
            try:
                gate = datetime.fromisoformat(resume_after.replace("Z", "+00:00"))
                if now < gate:
                    continue
            except ValueError:
                # Try question-ID reference: "Q6.3", "after Q6.3 is DONE", "DONE:Q6.3"
                ref_match = _QREF_PATTERN.search(resume_after)
                if ref_match:
                    ref_qid = ref_match.group(1).upper()
                    ref_q = get_question_by_id(questions, ref_qid)
                    if ref_q and ref_q["status"] not in _RESOLVED:
                        continue  # referenced question not yet resolved
        return q
    return None


def get_question_by_id(questions: list[dict], qid: str) -> dict | None:
    """Return the question with the given ID, or None."""
    for q in questions:
        if q["id"] == qid:
            return q
    return None


def sync_status_from_results() -> int:
    """
    Reconcile questions.md Status fields against results.tsv.
    Returns count of questions updated.
    """
    if not cfg.results_tsv.exists() or not cfg.questions_md.exists():
        return 0

    # Build map of qid → new status from results.tsv
    done_ids: dict[str, str] = {}
    for line in cfg.results_tsv.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] not in ("question_id", ""):
            verdict = parts[1].strip()
            _TERMINAL_VERDICTS = frozenset(
                {
                    "HEALTHY",
                    "WARNING",
                    "FAILURE",
                    "INCONCLUSIVE",
                    "DIAGNOSIS_COMPLETE",
                    "PENDING_EXTERNAL",
                    "FIXED",
                    "FIX_FAILED",
                    "PROMISING",
                    "WEAK",
                    "BLOCKED",
                    "CALIBRATED",
                    "UNCALIBRATED",
                    "NOT_MEASURABLE",
                    "COMPLIANT",
                    "NON_COMPLIANT",
                    "PARTIAL",
                    "NOT_APPLICABLE",
                    "IMPROVEMENT",
                    "REGRESSION",
                    "IMMINENT",
                    "PROBABLE",
                    "POSSIBLE",
                    "UNLIKELY",
                    "OK",
                    "DEGRADED",
                    "ALERT",
                    "UNKNOWN",
                    "SUBJECTIVE",
                    "DEGRADED_TRENDING",
                    "DEPLOYMENT_BLOCKED",  # Q6.3: preserve — human must confirm deployment before unblocking
                    "HEAL_EXHAUSTED",  # F-mid.1: exhausted heal loop — preserve status
                }
            )
            if verdict in _TERMINAL_VERDICTS:
                done_ids[parts[0]] = (
                    verdict
                    if verdict
                    in (
                        "INCONCLUSIVE",
                        "DIAGNOSIS_COMPLETE",
                        "PENDING_EXTERNAL",
                        "DEPLOYMENT_BLOCKED",  # Q6.3: preserve — awaiting deployment
                        "FIXED",
                        "FIX_FAILED",
                        "BLOCKED",
                        # F11.2: preserve failure/violation verdicts for human visibility (matches F8.2 in findings.py)
                        "FAILURE",
                        "NON_COMPLIANT",
                        "WARNING",
                        "REGRESSION",
                        "ALERT",
                        "HEAL_EXHAUSTED",  # F-mid.1: preserve exhausted-heal status
                    )
                    else "DONE"
                )

    # Update questions.md
    text = cfg.questions_md.read_text(encoding="utf-8")
    updated = 0
    for qid, new_status in done_ids.items():
        block_start = text.find(f"## {qid} [")
        if block_start == -1:
            block_start = text.find(f"## {qid}\n")
        if block_start == -1:
            continue
        next_block = text.find("\n## ", block_start + 1)
        block_end = next_block if next_block != -1 else len(text)
        block = text[block_start:block_end]
        if "**Status**: PENDING" in block:
            new_block = block.replace(
                "**Status**: PENDING", f"**Status**: {new_status}", 1
            )
            text = text[:block_start] + new_block + text[block_end:]
            updated += 1

    if updated:
        cfg.questions_md.write_text(text, encoding="utf-8")
    return updated
