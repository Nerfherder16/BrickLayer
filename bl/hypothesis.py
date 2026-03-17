"""
bl/hypothesis.py — Hypothesis generator: local LLM reads campaign findings
and generates the next wave of PENDING questions.

This is the feedback loop. The model reasons about what failure patterns
have been found and what hasn't been tested yet, then generates specific
testable hypotheses in questions.md format.
"""

import re
import sys
from pathlib import Path

import httpx

from bl.config import cfg


_TIMEOUT = 120.0  # hypothesis generation needs more time than classification

_QUESTION_BLOCK_HEADER = re.compile(
    r"^## ([\w][\w.-]*)\s+\[(\w+)\]\s+(.+)$",
    re.MULTILINE,  # F9.1: match BL 2.0 IDs (D8.1, F5.1) + BL 1.x (Q2.4)
)


def _get_wave_number(questions_text: str) -> int:
    """Detect highest wave number currently in questions.md."""
    matches = _QUESTION_BLOCK_HEADER.findall(questions_text)
    if not matches:
        return 1
    waves = []
    for qid, _, _ in matches:
        try:
            wave = int(qid.split(".")[0][1:])
            waves.append(wave)
        except (ValueError, IndexError):
            pass
    return max(waves) if waves else 1


def _get_existing_ids(questions_text: str) -> set[str]:
    """Return all question IDs already in questions.md."""
    return {m[0] for m in _QUESTION_BLOCK_HEADER.findall(questions_text)}


def _build_findings_summary(results_tsv: Path) -> str:
    """Build a concise findings summary from results.tsv for the LLM prompt."""
    if not results_tsv.exists():
        return "No results available."

    lines = results_tsv.read_text(encoding="utf-8").splitlines()
    if len(lines) <= 1:
        return "No results yet."

    summary_lines = []
    warnings = []
    failures = []
    inconclusives = []

    for line in lines[1:]:  # skip header
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        qid = parts[0].strip()
        verdict = parts[1].strip()
        # summary is the last non-empty column before timestamp
        summary = parts[-2].strip() if len(parts) >= 4 else parts[2].strip()

        entry = f"  {qid}: {verdict} — {summary[:120]}"
        summary_lines.append(entry)
        if verdict == "WARNING":
            warnings.append(entry)
        elif verdict == "FAILURE":
            failures.append(entry)
        elif verdict == "INCONCLUSIVE":
            inconclusives.append(entry)

    out = ["=== All findings ==="]
    out.extend(summary_lines)

    if failures:
        out.append("\n=== FAILURES (highest priority) ===")
        out.extend(failures)
    if warnings:
        out.append("\n=== WARNINGS (investigate further) ===")
        out.extend(warnings)
    if inconclusives:
        out.append("\n=== INCONCLUSIVE (may need re-run or agent analysis) ===")
        out.extend(inconclusives)

    return "\n".join(out)


def _ollama_hypothesize(
    findings_summary: str, next_wave: int, existing_ids: set[str]
) -> str | None:
    """Call qwen2.5:7b to generate hypothesis questions."""

    prompt = f"""You are a research campaign director analyzing findings from an automated testing campaign against a production memory system (Recall: FastAPI + Qdrant + Neo4j + Redis + PostgreSQL + Ollama).

Your job: read the findings below and generate {4 if next_wave >= 8 else 5} new PENDING research questions for Wave {next_wave}.

Rules:
1. Focus on failure patterns — WARNING and INCONCLUSIVE findings deserve follow-up
2. Generate questions that test what hasn't been tested yet
3. Each question must be specific and independently runnable
4. Use the EXACT format shown below — no deviation
5. Question IDs must start at Q{next_wave}.1 and increment
6. Each block must start with a line containing exactly "---" on its own

EXACT FORMAT (copy this structure precisely):
---

## Q{next_wave}.1 [CATEGORY] Short descriptive title
**Mode**: agent
**Status**: PENDING
**Hypothesis**: One sentence predicting what we will find.
**Test**: Exact pytest command or agent instruction to execute.
**Verdict threshold**:
- FAILURE: specific measurable condition
- WARNING: specific measurable condition
- HEALTHY: specific measurable condition

**Derived from**: Q3.5, Q3.3 (comma-separated parent question IDs)

---

## Q{next_wave}.2 [CATEGORY] Another question
... (continue same format)

CAMPAIGN FINDINGS:
{findings_summary}

Generate Wave {next_wave} questions now. Output ONLY the question blocks in the exact format above. No preamble, no explanation, no commentary after."""

    try:
        resp = httpx.post(
            f"{cfg.local_ollama_url}/api/generate",
            json={
                "model": cfg.local_model,
                "prompt": prompt,
                "system": "You generate structured research question blocks in exact markdown format. Follow the format precisely.",
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2048},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[hypothesis] Ollama call failed: {e}", file=sys.stderr)
        return None


def _parse_question_blocks(raw: str, next_wave: int) -> list[str]:
    """Extract well-formed question blocks from LLM output."""
    # Split on --- separators
    blocks = re.split(r"\n---\n|\n---$|^---\n", raw, flags=re.MULTILINE)
    valid = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Must contain a question header for our wave
        if not re.search(rf"## Q{next_wave}\.\d+", block):
            continue
        # Must have Status: PENDING
        if "**Status**: PENDING" not in block:
            # Add it if missing
            block = block.replace("**Mode**:", "**Status**: PENDING\n**Mode**:", 1)
            if "**Status**: PENDING" not in block:
                continue
        valid.append(block)

    return valid


def generate_hypotheses(
    questions_md: Path,
    results_tsv: Path,
    wave: int | None = None,
    dry_run: bool = False,
) -> list[str]:
    """
    Generate next-wave hypotheses using the local LLM. Appends to questions.md.

    Returns list of generated question IDs.
    """
    if not questions_md.exists():
        print("[hypothesis] questions.md not found", file=sys.stderr)
        return []

    questions_text = questions_md.read_text(encoding="utf-8")
    existing_ids = _get_existing_ids(questions_text)
    next_wave = wave or (_get_wave_number(questions_text) + 1)

    print(f"[hypothesis] Existing questions: {len(existing_ids)}", file=sys.stderr)
    print(
        f"[hypothesis] Generating Wave {next_wave} questions via {cfg.local_model}...",
        file=sys.stderr,
    )

    findings_summary = _build_findings_summary(results_tsv)
    raw = _ollama_hypothesize(findings_summary, next_wave, existing_ids)

    if not raw:
        print("[hypothesis] No output from local model", file=sys.stderr)
        return []

    blocks = _parse_question_blocks(raw, next_wave)

    if not blocks:
        print(
            "[hypothesis] Could not parse any valid question blocks from LLM output",
            file=sys.stderr,
        )
        print(f"[hypothesis] Raw output was:\n{raw[:500]}", file=sys.stderr)
        return []

    if dry_run:
        print(f"\n[hypothesis] DRY RUN — would append {len(blocks)} question(s):\n")
        for b in blocks:
            print(b)
            print()
        return []

    # Append to questions.md
    with open(questions_md, "a", encoding="utf-8") as f:
        f.write(
            f"\n\n---\n\n## Wave {next_wave} — Hypothesis Generator (qwen2.5:7b)\n\n"
        )
        f.write(
            "*Generated by BrickLayer local inference from campaign findings patterns.*\n"
        )
        for block in blocks:
            f.write(f"\n---\n\n{block}\n")

    generated_ids = []
    for block in blocks:
        m = re.search(r"## (Q\d+\.\d+[\w.]*)", block)
        if m:
            generated_ids.append(m.group(1))

    print(
        f"[hypothesis] Generated {len(blocks)} question(s): {', '.join(generated_ids)}",
        file=sys.stderr,
    )
    return generated_ids
