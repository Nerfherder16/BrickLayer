"""Layer 2: LLM Judge — score agent outputs via `claude -p`.

Uses the 10-dimension rubric (4 pts each = 40 max).
Falls back gracefully when the `claude` CLI is not available.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

JUDGE_DIMENSIONS: list[str] = [
    "task_completion",        # Did it do what was asked?
    "output_format",          # Follows expected format?
    "evidence_quality",       # Evidence cited/shown?
    "confidence_calibration", # Confidence matches evidence strength?
    "no_hallucination",       # No fabricated claims?
    "actionability",          # Output is actionable?
    "conciseness",             # No unnecessary verbosity?
    "error_handling",         # Edge cases addressed?
    "consistency",            # No internal contradictions?
    "instruction_following",  # Followed all constraints?
]

_MAX_PTS_PER_DIM = 4


def build_judge_prompt(task: str, output: str, dimensions: list[str]) -> str:
    """Build a judge prompt for scoring output on given dimensions."""
    dims_list = "\n".join(f"- {d}" for d in dimensions)
    return (
        "You are an impartial judge scoring an AI agent's output.\n\n"
        f"## Task\n{task}\n\n"
        f"## Agent Output\n{output}\n\n"
        f"## Scoring Dimensions (0–{_MAX_PTS_PER_DIM} each)\n{dims_list}\n\n"
        "Return a JSON object with exactly these keys (one per dimension) "
        "and integer scores 0–4. Example:\n"
        '{"task_completion": 4, "output_format": 3, ...}'
    )


def run_judge(
    agent_name: str,
    task: str,
    output: str,
    base_dir: Any = None,
) -> dict[str, Any] | None:
    """Run the LLM judge and return dimension scores + total.

    Returns None if `claude` CLI is unavailable or produces invalid output.
    """
    prompt = build_judge_prompt(task, output, JUDGE_DIMENSIONS)
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        raw = proc.stdout.strip()
        if not raw:
            return None

        # claude --output-format json wraps result; try to extract the scores dict
        parsed: Any = json.loads(raw)
        # If wrapped (e.g. {"type":"result","result":"..."}) unwrap
        if isinstance(parsed, dict) and "result" in parsed:
            inner = parsed["result"]
            if isinstance(inner, str):
                parsed = json.loads(inner)
            elif isinstance(inner, dict):
                parsed = inner

        scores: dict[str, int] = {}
        for dim in JUDGE_DIMENSIONS:
            val = parsed.get(dim)
            scores[dim] = int(val) if val is not None else 0

        total = sum(scores.values())
        return {"scores": scores, "total": total, "agent": agent_name}

    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        return None
