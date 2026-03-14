"""
bl/goal.py — Goal-directed campaign question generator (C-03).

Reads goal.md from the project directory, calls qwen2.5:7b via local inference
to generate a focused, falsifiable question set targeting the stated goal,
and appends the questions to questions.md.

goal.md format:
    # Research Goal
    **Goal**: <natural language description of what to investigate>
    **Target**: <URL or system being tested, e.g. http://192.168.50.19:8200>
    **Focus**: <optional comma-separated domains: D1, D2, D3, D4, D5, D6>
    **Max questions**: <optional integer, default 6>
    **Context**: <optional additional context>

Usage:
    from bl.goal import generate_goal_questions
    generate_goal_questions(goal_md_path, questions_md_path, dry_run=False)
"""

import re
import sys
from pathlib import Path

import httpx

from bl.config import cfg

_TIMEOUT = 120.0
_DEFAULT_MAX_QUESTIONS = 6
_MAX_CONTEXT_CHARS = 3000

_QUESTION_BLOCK_HEADER = re.compile(r"## (QG\d+\.\d+)", re.MULTILINE)


# ---------------------------------------------------------------------------
# goal.md parser
# ---------------------------------------------------------------------------


def _parse_goal(goal_text: str) -> dict:
    """Parse goal.md text into a dict of structured fields."""
    result = {
        "goal": "",
        "target": "",
        "focus": [],
        "max_questions": _DEFAULT_MAX_QUESTIONS,
        "context": "",
    }

    for line in goal_text.splitlines():
        line = line.strip()
        # Strip bold markers for matching
        clean = line.replace("**", "")

        if clean.startswith("Goal:"):
            result["goal"] = clean[len("Goal:") :].strip()
        elif clean.startswith("Target:"):
            result["target"] = clean[len("Target:") :].strip()
        elif clean.startswith("Focus:"):
            focus_raw = clean[len("Focus:") :].strip()
            result["focus"] = [f.strip() for f in focus_raw.split(",") if f.strip()]
        elif clean.startswith("Max questions:"):
            try:
                result["max_questions"] = int(clean[len("Max questions:") :].strip())
            except ValueError:
                pass
        elif clean.startswith("Context:"):
            result["context"] = clean[len("Context:") :].strip()

    if not result["goal"]:
        raise ValueError(
            "goal.md is missing required **Goal**: field. "
            "Add a line like: **Goal**: Describe what to investigate."
        )

    return result


# ---------------------------------------------------------------------------
# Simulation context reader
# ---------------------------------------------------------------------------


def _read_sim_params(project_dir: Path) -> str:
    """Read constants.py and the SCENARIO PARAMETERS section of simulate.py."""
    parts = []

    constants_py = project_dir / "constants.py"
    if constants_py.exists():
        parts.append("=== constants.py ===")
        parts.append(constants_py.read_text(encoding="utf-8"))

    simulate_py = project_dir / "simulate.py"
    # Fall back to the autosearch root simulate.py
    if not simulate_py.exists():
        simulate_py = cfg.autosearch_root / "simulate.py"

    if simulate_py.exists():
        sim_text = simulate_py.read_text(encoding="utf-8")
        # Find the SCENARIO PARAMETERS section
        scenario_match = re.search(
            r"(#\s*SCENARIO PARAMETERS|#\s*-{5,}.*scenario|#\s*-{5,})",
            sim_text,
            re.IGNORECASE,
        )
        if scenario_match:
            start = scenario_match.start()
            snippet = sim_text[start : start + 80 * 60]  # up to 80 lines
            parts.append("=== simulate.py SCENARIO PARAMETERS ===")
            parts.append(snippet)
        else:
            # No clear section marker — take first 60 lines as context
            lines = sim_text.splitlines()[:60]
            parts.append("=== simulate.py (first 60 lines) ===")
            parts.append("\n".join(lines))

    combined = "\n\n".join(parts)
    return combined[:_MAX_CONTEXT_CHARS]


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_prompt(goal: dict, sim_context: str) -> str:
    focus_str = ", ".join(goal["focus"]) if goal["focus"] else "all domains (D1–D6)"
    n = goal["max_questions"]

    return f"""You are a research campaign director. Your task is to generate {n} focused, falsifiable research questions targeting the stated goal below.

RESEARCH GOAL:
  {goal["goal"]}

TARGET SYSTEM:
  {goal["target"] or "See simulate.py for configuration"}

DOMAIN FOCUS:
  {focus_str}

ADDITIONAL CONTEXT:
  {goal["context"] or "None provided."}

SIMULATION CONTEXT (parameter space):
{sim_context}

Generate exactly {n} questions in the format below. Each question must:
- Be directly motivated by the stated goal
- Be independently runnable
- Have a falsifiable hypothesis
- Target a specific measurable condition
- Be non-redundant

REQUIRED FORMAT — output ONLY these blocks separated by ---. No preamble, no explanation, no markdown outside the blocks:

---
## QG1.1 [D1] Short descriptive title
**Mode**: agent
**Status**: PENDING
**Hypothesis**: One sentence predicting what we will find.
**Test**: Exact instruction or command to execute the test.
**Verdict threshold**:
- FAILURE: specific measurable condition that indicates failure
- WARNING: specific measurable condition that warrants attention
- HEALTHY: baseline condition indicating no issue
**Goal**: Which aspect of the stated goal this question addresses.
---

## QG1.2 [D4] Another question title
**Mode**: agent
**Status**: PENDING
**Hypothesis**: ...
**Test**: ...
**Verdict threshold**:
- FAILURE: ...
- WARNING: ...
- HEALTHY: ...
**Goal**: ...
---

(continue for all {n} questions)

Output ONLY the question blocks separated by ---. No preamble, no explanation, no markdown outside the blocks."""


# ---------------------------------------------------------------------------
# Ollama call
# ---------------------------------------------------------------------------


def _call_ollama(prompt: str) -> str | None:
    """Call qwen2.5:7b via local Ollama and return response text."""
    print("[goal] Calling qwen2.5:7b...", file=sys.stderr)
    try:
        resp = httpx.post(
            f"{cfg.local_ollama_url}/api/generate",
            json={
                "model": cfg.local_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 2048},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[goal] Ollama call failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------


def _get_next_wave_index(questions_text: str) -> int:
    """Find the next sequential wave index for QG questions."""
    matches = re.findall(r"## QG(\d+)\.\d+", questions_text)
    if not matches:
        return 1
    return max(int(m) for m in matches) + 1


def _parse_goal_questions(raw: str, wave_label: str = "Goal Campaign") -> list[str]:
    """Split LLM output on --- and return valid question blocks."""
    blocks = re.split(r"\n---\n|^---\n|\n---$", raw, flags=re.MULTILINE)
    valid = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if "**Status**: PENDING" not in block:
            if "## QG" in block:
                print(
                    f"[goal] Warning: block missing **Status**: PENDING — skipping:\n  {block[:80]}",
                    file=sys.stderr,
                )
            continue
        if "## QG" not in block:
            continue
        valid.append(block)

    return valid


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_goal_questions(
    goal_md: Path,
    questions_md: Path,
    dry_run: bool = False,
) -> list[str]:
    """
    Read goal.md, generate questions via qwen2.5:7b, append to questions.md.
    Returns list of question IDs generated.
    Prints progress to stderr.
    """
    if not goal_md.exists():
        print(f"[goal] goal.md not found at {goal_md}", file=sys.stderr)
        return []

    goal_text = goal_md.read_text(encoding="utf-8")
    try:
        goal = _parse_goal(goal_text)
    except ValueError as e:
        print(f"[goal] Parse error: {e}", file=sys.stderr)
        return []

    print(f"[goal] Goal: {goal['goal'][:80]}", file=sys.stderr)
    print(f"[goal] Max questions: {goal['max_questions']}", file=sys.stderr)

    project_dir = goal_md.parent
    sim_context = _read_sim_params(project_dir)
    prompt = _build_prompt(goal, sim_context)

    raw = _call_ollama(prompt)
    if raw is None:
        print("[goal] No output from local model — aborting.", file=sys.stderr)
        return []

    blocks = _parse_goal_questions(raw)

    if not blocks:
        print(
            "[goal] Could not parse any valid question blocks from LLM output.",
            file=sys.stderr,
        )
        print(f"[goal] Raw output (first 500 chars):\n{raw[:500]}", file=sys.stderr)
        return []

    # Re-number blocks using next available QG wave index
    existing_text = (
        questions_md.read_text(encoding="utf-8") if questions_md.exists() else ""
    )
    wave_idx = _get_next_wave_index(existing_text)

    renumbered = []
    for i, block in enumerate(blocks, start=1):
        # Replace QGx.y header with correct wave index
        block = re.sub(r"## QG\d+\.(\d+)", f"## QG{wave_idx}.{i}", block)
        renumbered.append(block)

    if dry_run:
        print(f"\n[goal] DRY RUN — would append {len(renumbered)} question(s):\n")
        for b in renumbered:
            print(b)
            print()
        return [f"QG{wave_idx}.{i}" for i in range(1, len(renumbered) + 1)]

    # Append to questions.md
    goal_summary = goal["goal"][:60]
    header = (
        f"\n\n---\n\n"
        f"## Goal Campaign — {goal_summary}\n\n"
        f"*Generated by BrickLayer goal-directed mode from goal.md.*\n\n"
        f"---\n"
    )
    with open(questions_md, "a", encoding="utf-8") as f:
        f.write(header)
        for block in renumbered:
            f.write(f"\n{block}\n\n---\n")

    generated_ids = [f"QG{wave_idx}.{i}" for i in range(1, len(renumbered) + 1)]
    print(
        f"[goal] Generated {len(generated_ids)} question(s): {', '.join(generated_ids)}",
        file=sys.stderr,
    )
    return generated_ids
