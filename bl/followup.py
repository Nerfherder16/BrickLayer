"""
bl/followup.py — Adaptive follow-up question generator (C-04).

After a FAILURE or WARNING verdict, generates targeted drill-down sub-questions
using qwen2.5:7b and injects them into questions.md for immediate campaign pickup.

Sub-question IDs: parent Q2.4 -> Q2.4.1, Q2.4.2, Q2.4.3
Depth limit: only 1 level deep (Q2.4.1 never generates Q2.4.1.1)
"""

import os
import re
import sys
from pathlib import Path

import httpx

from bl.config import cfg

_TIMEOUT = 90.0


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------


def _is_leaf_id(qid: str) -> bool:
    """Return True if qid is already a sub-question (3+ numeric parts after Q/QG prefix).

    Examples:
        Q2.4   -> False  (can drill down)
        Q2.4.1 -> True   (already a sub-question)
        QG1.2  -> False  (goal-generated, can drill)
        Q8.1   -> False  (can drill)
    """
    # Strip leading Q or QG prefix
    stripped = qid
    if stripped.startswith("QG"):
        stripped = stripped[2:]
    elif stripped.startswith("Q"):
        stripped = stripped[1:]
    else:
        # Unknown format — treat as leaf to be safe
        return True

    parts = stripped.split(".")
    return len(parts) >= 3


def _get_existing_sub_ids(questions_md: Path, parent_id: str) -> list[str]:
    """Scan questions.md for lines matching ## {parent_id}.N — return existing sub-IDs."""
    if not questions_md.exists():
        return []
    text = questions_md.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s+" + re.escape(parent_id) + r"\.\d+", re.MULTILINE)
    matches = pattern.findall(text)
    # Extract IDs from "## Q2.4.1 [DOMAIN] ..." lines
    ids = []
    for m in matches:
        parts = m.split()
        if len(parts) >= 2:
            ids.append(parts[1])
    return ids


def _next_sub_index(questions_md: Path, parent_id: str) -> int:
    """Return next available sub-question index (1-based).

    If Q2.4.1 and Q2.4.2 exist, returns 3.
    """
    existing = _get_existing_sub_ids(questions_md, parent_id)
    if not existing:
        return 1
    # Parse the numeric suffix of each sub-ID
    indices = []
    for sid in existing:
        # sid like "Q2.4.1" — last segment after final dot
        try:
            idx = int(sid.rsplit(".", 1)[-1])
            indices.append(idx)
        except ValueError:
            pass
    return max(indices) + 1 if indices else 1


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _build_followup_prompt(question: dict, result: dict, max_questions: int) -> str:
    """Build the prompt for qwen2.5:7b to generate drill-down sub-questions."""
    parent_id = question["id"]
    verdict = result.get("verdict", "UNKNOWN")
    summary = result.get("summary", "")
    details = result.get("details", "")[:500]
    failure_type = result.get("failure_type", "")
    mode = question.get("mode", "agent")
    hypothesis = question.get("hypothesis", "")
    test = question.get("test", "")

    failure_type_line = f"\nFailure type: {failure_type}" if failure_type else ""

    return f"""You are a research campaign director drilling down into a failed test result.

The question below returned {verdict}. Generate exactly {max_questions} targeted drill-down sub-questions that investigate the specific failure more precisely.

ORIGINAL QUESTION:
ID: {parent_id}
Title: {question.get("title", "")}
Hypothesis: {hypothesis}
Test: {test}

RESULT:
Verdict: {verdict}
Summary: {summary}{failure_type_line}
Details: {details}

Generate {max_questions} sub-questions. Each must start with --- on its own line, then a ## header.

EXACT FORMAT (use this precisely):
---
## {parent_id}.N [DOMAIN] Short drill-down title
**Mode**: {mode}
**Status**: PENDING
**Hypothesis**: Specific follow-on hypothesis targeting the observed failure.
**Test**: Concrete test command or agent instruction targeting the specific failure.
**Verdict threshold**:
- FAILURE: specific measurable condition
- WARNING: specific measurable condition
- HEALTHY: specific measurable condition
**Derived from**: {parent_id} ({verdict})
---

Output ONLY the question blocks. No preamble. Each block starts with --- and a ## header."""


def _call_ollama(prompt: str) -> str | None:
    """POST to Ollama and return response text, or None on failure."""
    try:
        resp = httpx.post(
            f"{cfg.local_ollama_url}/api/generate",
            json={
                "model": cfg.local_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1500},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[followup] Ollama call failed: {e}", file=sys.stderr)
        return None


def _parse_followup_blocks(raw: str, parent_id: str, start_index: int) -> list[str]:
    """Parse LLM output into valid question block strings, renumbered from start_index."""
    # Split on --- separators
    segments = re.split(r"\n---\n|^---\n|\n---$|^---$", raw, flags=re.MULTILINE)

    valid = []
    current_index = start_index
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # Must contain required markers
        if "**Status**: PENDING" not in seg:
            print(
                "[followup] Skipping block — missing **Status**: PENDING",
                file=sys.stderr,
            )
            continue
        if "**Derived from**:" not in seg:
            print(
                "[followup] Skipping block — missing **Derived from**:",
                file=sys.stderr,
            )
            continue
        if not seg.startswith("##"):
            print(
                "[followup] Skipping block — does not start with ##",
                file=sys.stderr,
            )
            continue

        # Renumber the ## header ID to the correct sequential ID
        correct_id = f"{parent_id}.{current_index}"
        # Replace whatever ID the LLM put in the header with the correct one
        # Header pattern: ## Q2.4.N [DOMAIN] title  or  ## Q2.4.N title
        seg = re.sub(
            r"^##\s+\S+",
            f"## {correct_id}",
            seg,
            count=1,
            flags=re.MULTILINE,
        )
        valid.append(seg)
        current_index += 1

    return valid


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_followup(
    question: dict,
    result: dict,
    questions_md: Path,
    dry_run: bool = False,
    max_questions: int = 3,
) -> list[str]:
    """Generate drill-down sub-questions after a FAILURE or WARNING verdict.

    Returns list of generated sub-question IDs (e.g. ["Q2.4.1", "Q2.4.2"]).
    Injects them into questions_md unless dry_run=True.
    """
    # Check if disabled via env or cfg attribute
    if os.environ.get("BRICKLAYER_NO_FOLLOWUP"):
        return []
    if not getattr(cfg, "followup_enabled", True):
        return []

    verdict = result.get("verdict", "")
    if verdict not in ("FAILURE", "WARNING"):
        return []

    qid = question["id"]

    if _is_leaf_id(qid):
        print(
            f"[followup] {qid} is already a sub-question — skipping drill-down",
            file=sys.stderr,
        )
        return []

    if not questions_md.exists():
        print(
            f"[followup] questions.md not found at {questions_md} — skipping",
            file=sys.stderr,
        )
        return []

    start_index = _next_sub_index(questions_md, qid)
    prompt = _build_followup_prompt(question, result, max_questions)

    print(
        f"[followup] Generating drill-down for {qid} ({verdict})...",
        file=sys.stderr,
    )
    raw = _call_ollama(prompt)
    if raw is None:
        print(
            f"[followup] Ollama returned nothing — skipping follow-up for {qid}",
            file=sys.stderr,
        )
        return []

    blocks = _parse_followup_blocks(raw, qid, start_index)
    if not blocks:
        print(
            f"[followup] No valid blocks parsed for {qid}",
            file=sys.stderr,
        )
        return []

    # Build the list of IDs from start_index
    ids = [f"{qid}.{start_index + i}" for i in range(len(blocks))]

    if dry_run:
        for block in blocks:
            print("---")
            print(block)
            print("---")
        return ids

    # Append to questions.md
    separator = f"\n\n---\n\n*Follow-up drill-down for {qid} — {verdict} verdict*\n\n"
    with open(questions_md, "a", encoding="utf-8") as f:
        f.write(separator)
        for block in blocks:
            f.write(block)
            f.write("\n\n---\n\n")

    print(
        f"[followup] Injected {len(ids)} sub-question(s): {', '.join(ids)}",
        file=sys.stderr,
    )
    return ids
