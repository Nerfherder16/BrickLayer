"""masonry/scripts/optimize_with_claude.py

Optimize a Masonry agent's instructions using `claude -p` (Claude Code CLI).
No API key required — uses Claude Max subscription via the local claude binary.

Usage:
    python masonry/scripts/optimize_with_claude.py <agent_name> [options]

    Options:
      --base-dir DIR     BrickLayer root (default: cwd)
      --num-examples N   Max examples to include per tier (default: 15)
      --dry-run          Print prompt and exit without calling claude

Prints progress lines to stdout (Kiln-compatible optimization-progress events).
Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

# Re-use write-back and registry helpers from the existing script
from masonry.src.writeback import (
    update_registry_dspy_status,
    writeback_optimized_instructions,
)

_DSPY_SECTION_HEADER = "## DSPy Optimized Instructions"
_DSPY_SECTION_END = "<!-- /DSPy Optimized Instructions -->"


# ── Training data helpers ────────────────────────────────────────────────────

def _load_records(scored_all_path: Path, agent_name: str) -> list[dict]:
    """Load all scored records for agent_name from scored_all.jsonl."""
    if not scored_all_path.exists():
        return []
    records = []
    for line in scored_all_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("agent") == agent_name:
            records.append(rec)
    return records


def _tier_examples(records: list[dict], n: int) -> tuple[list[dict], list[dict]]:
    """Split records into high-quality (score>=75) and low-quality (score<50) tiers."""
    sorted_records = sorted(records, key=lambda r: r.get("score", 0), reverse=True)
    high = [r for r in sorted_records if r.get("score", 0) >= 75][:n]
    low = [r for r in sorted_records if r.get("score", 0) < 50][:n]
    return high, low


def _format_example(rec: dict) -> str:
    """Format a single record as readable text for the prompt."""
    inp = rec.get("input") or {}
    out = rec.get("output") or {}
    score = rec.get("score", "?")
    q = inp.get("question_text") or inp.get("question_id") or "?"
    verdict = out.get("verdict") or "?"
    evidence = (out.get("evidence") or "")[:800]  # 800 chars captures full numbered structure
    summary = (out.get("summary") or "")[:200]
    return (
        f"Score: {score}/100\n"
        f"Question: {q}\n"
        f"Verdict: {verdict}\n"
        f"Summary: {summary}\n"
        f"Evidence: {evidence}\n"
    )


# ── Agent .md reader ─────────────────────────────────────────────────────────

def _find_agent_md(agent_name: str, base_dir: Path) -> Path | None:
    """Find the primary agent .md file (project-level preferred, then global)."""
    candidates = [
        base_dir / ".claude" / "agents" / f"{agent_name}.md",
        Path.home() / ".claude" / "agents" / f"{agent_name}.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _read_current_instructions(md_path: Path) -> str:
    """Read the agent instructions, stripping any existing DSPy section."""
    content = md_path.read_text(encoding="utf-8")
    # Strip existing DSPy section so we don't compound noise
    pattern = re.compile(
        rf"{re.escape(_DSPY_SECTION_HEADER)}.*?{re.escape(_DSPY_SECTION_END)}\n?",
        re.DOTALL,
    )
    return pattern.sub("", content).strip()


# ── Prompt builder ───────────────────────────────────────────────────────────

def _build_prompt(
    agent_name: str,
    current_instructions: str,
    high_examples: list[dict],
    low_examples: list[dict],
) -> str:
    high_block = "\n---\n".join(_format_example(r) for r in high_examples) if high_examples else "(none)"
    low_block = "\n---\n".join(_format_example(r) for r in low_examples) if low_examples else "(none)"

    return f"""You are a prompt engineer optimizing the instructions for a BrickLayer research agent called **{agent_name}**.

## Scoring Rubric (what the eval measures)

The agent is scored on three axes, 0–1 each:
- **Verdict match (40%)**: exact string match against the expected verdict (HEALTHY, WARNING, FAILURE, INCONCLUSIVE, etc.)
- **Evidence quality (40%)**: evidence text > 300 chars AND contains numbers or threshold language (%, ms, pts, baseline, threshold, seconds) = full marks; otherwise half marks. **Prerequisite gate**: wrong verdict caps total at 0.20 regardless of evidence quality.
- **Confidence calibration (20%)**: 1 - |predicted_confidence - 0.75|. Closer to 0.75 = higher score.

## Current Agent Instructions

{current_instructions}

## High-Quality Outputs (score >= 75/100)

{high_block}

## Low-Quality Outputs (score < 50/100)

{low_block}

## Your Task

Write quality-guidance instructions to be injected into the agent's `## DSPy Optimized Instructions` section.
These instructions **supplement** the procedural steps already in the agent file — they do NOT replace them.

Focus your improvements on:

1. **Verdict calibration**: What patterns distinguish correct verdicts? When is WARNING vs FAILURE vs HEALTHY correct? Ground rules in the scoring rubric above.
2. **Evidence structure**: The eval requires >300 chars with quantitative data. What format consistently produces high-scoring evidence? (Numbered bold-header items with specific numbers score highest.)
3. **Summary quality**: Summaries must be ≤200 chars, include a quantitative fact, and state the verdict + key insight.
4. **Confidence targeting**: Optimal confidence is ~0.75. When to deviate.
5. **Root cause chains**: High-scoring outputs explain root cause → mechanism → impact. Low-scoring outputs state symptoms only.

DO NOT:
- Rewrite the procedural steps (Steps 1–7 in the synthesizer, or equivalent in other agents)
- Remove or restructure output format templates
- Add meta-commentary about the optimization process
- Include instructions about infrastructure tasks (git, CHANGELOG, etc.) in quality guidance

DO:
- Write concrete quality standards, evidence format rules, and verdict calibration guides
- Include pattern examples derived from the training data above
- Keep instructions imperative and direct (not suggestions)

Respond with ONLY a JSON object, no markdown fences, no commentary:

{{
  "improved_instructions": "<quality-guidance text to inject — not a full rewrite>",
  "key_changes": ["change 1", "change 2", "change 3"]
}}"""


# ── Main ─────────────────────────────────────────────────────────────────────

def run(
    agent_name: str,
    base_dir: Path,
    num_examples: int = 15,
    dry_run: bool = False,
) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"[init] Starting claude-p optimization for: {agent_name}")
    print(f"[init] Base directory: {base_dir}")

    # ── Load training data ────────────────────────────────────────────────────
    td_dir = base_dir / "masonry" / "training_data"
    scored_all_path = td_dir / "scored_all.jsonl"
    print(f"[data] Loading records for {agent_name} ...")

    records = _load_records(scored_all_path, agent_name)
    if not records:
        print(f"[error] No records found for {agent_name} in scored_all.jsonl")
        print(f"[error] Run 'Score All' in Kiln first to generate training data.")
        return 1

    print(f"[data] Found {len(records)} records.")
    high, low = _tier_examples(records, num_examples)
    print(f"[data] High-quality examples: {len(high)}, Low-quality: {len(low)}")

    # ── Read agent instructions ───────────────────────────────────────────────
    md_path = _find_agent_md(agent_name, base_dir)
    if not md_path:
        print(f"[error] Could not find {agent_name}.md in agents directories.")
        return 1

    print(f"[agent] Reading instructions from: {md_path}")
    current_instructions = _read_current_instructions(md_path)

    # ── Build prompt ──────────────────────────────────────────────────────────
    prompt = _build_prompt(agent_name, current_instructions, high, low)
    print(f"[prompt] Prompt size: {len(prompt)} chars")

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN — prompt that would be sent to claude -p:")
        print("=" * 60)
        safe = prompt[:3000].encode("ascii", errors="replace").decode("ascii")
        print(safe + ("\n... (truncated)" if len(prompt) > 3000 else ""))
        return 0

    # ── Call claude -p ────────────────────────────────────────────────────────
    import shutil
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("[error] claude binary not found — is Claude Code installed and in PATH?")
        return 1

    print(f"[claude] Calling claude -p (subscription mode) via {claude_bin} ...")

    try:
        result = subprocess.run(
            [claude_bin, "-p", "--no-session-persistence", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print("[error] claude -p timed out after 600 seconds.")
        return 1

    if result.returncode != 0:
        print(f"[error] claude -p exited with code {result.returncode}")
        if result.stderr:
            print(f"[error] stderr: {result.stderr[:500]}")
        return 1

    raw_output = result.stdout.strip()
    print(f"[claude] Got response ({len(raw_output)} chars)")

    # ── Parse JSON response ───────────────────────────────────────────────────
    # Strip markdown code fences if Claude added them anyway
    json_text = re.sub(r"^```(?:json)?\s*", "", raw_output, flags=re.MULTILINE)
    json_text = re.sub(r"\s*```$", "", json_text, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as e:
        # Try extracting a JSON object with a regex fallback
        m = re.search(r'\{.*"improved_instructions".*\}', json_text, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except json.JSONDecodeError:
                parsed = None
        else:
            parsed = None

        if parsed is None:
            print(f"[error] Could not parse JSON from claude response: {e}")
            print(f"[error] Raw output (first 500 chars): {raw_output[:500]}")
            return 1

    instructions = parsed.get("improved_instructions", "").strip()
    key_changes = parsed.get("key_changes", [])

    if not instructions:
        print("[error] Response JSON had empty 'improved_instructions'.")
        return 1

    print(f"[parse] Extracted instructions ({len(instructions)} chars)")
    if key_changes:
        print("[parse] Key changes:")
        for change in key_changes[:5]:
            print(f"  - {change}")

    # ── Write-back ────────────────────────────────────────────────────────────
    # Scope guard: only write back to the file that was read for optimization.
    # This prevents contaminating copies that may be different variants of the
    # same agent (e.g., commit-classifier karen vs project-org karen).
    optimized_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        updated_files = writeback_optimized_instructions(
            base_dir=base_dir,
            agent_name=agent_name,
            instructions=instructions,
            optimized_at=optimized_at,
            target_paths=[md_path],  # scope guard: source file only
        )
        if updated_files:
            for f in updated_files:
                print(f"[writeback] Injected instructions into: {f}")
        else:
            print(f"[writeback] No agent .md files found — skipping writeback.")
    except Exception as exc:
        print(f"[warn] Writeback failed: {exc}")

    # ── Save output JSON (same path as DSPy for Kiln compatibility) ───────────
    output_dir = base_dir / "masonry" / "optimized_prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{agent_name}.json"
    output_data = {
        "agent": agent_name,
        "method": "claude-p",
        "optimized_at": optimized_at,
        "training_records": len(records),
        "high_quality_examples": len(high),
        "low_quality_examples": len(low),
        "key_changes": key_changes,
        "predict": {
            "signature": {
                "instructions": instructions,
            }
        },
    }
    output_file.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    print(f"[output] Saved to: {output_file}")

    # ── Update registry ───────────────────────────────────────────────────────
    registry_path = base_dir / "masonry" / "agent_registry.yml"
    if registry_path.exists():
        try:
            update_registry_dspy_status(registry_path, agent_name, optimized_at)
            print(f"[registry] Updated agent_registry.yml — dspy_status: optimized")
        except Exception as exc:
            print(f"[warn] Could not update registry: {exc}")

    print(f"[done] Optimization complete for {agent_name}.")
    return 0


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimize a Masonry agent using claude -p (no API key required)."
    )
    parser.add_argument("agent_name", help="Name of the agent to optimize")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="BrickLayer root directory (default: cwd)",
    )
    parser.add_argument(
        "--num-examples",
        type=int,
        default=15,
        help="Max examples per quality tier to include (default: 15)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt and exit without calling claude",
    )
    args = parser.parse_args()
    sys.exit(run(
        agent_name=args.agent_name,
        base_dir=args.base_dir.resolve(),
        num_examples=args.num_examples,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    _main()
