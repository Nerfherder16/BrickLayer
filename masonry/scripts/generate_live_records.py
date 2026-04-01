"""masonry/scripts/generate_live_records.py

Generate live-eval-calibrated training records for research-analyst.
Runs each candidate question through eval_agent_live.py with tools enabled,
collects the tool-enabled agent outputs as gold labels, and saves records
to a staging JSONL file for review before adding to scored_all.jsonl.

Usage:
    python masonry/scripts/generate_live_records.py --output live_records.jsonl
    python masonry/scripts/generate_live_records.py --output live_records.jsonl --start 0 --end 10
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_CLAUDE_CMD = ["claude.cmd" if platform.system() == "Windows" else "claude"]

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

_AGENTS_DIR = _SCRIPT_ROOT / ".claude/agents"
_DEFAULT_MODEL = "claude-sonnet-4-6"
_TIMEOUT = 180

_LIVE_PREAMBLE = (
    "You are running in eval mode. Research the following question using your available tools. "
    "Produce a finding in the standard FindingPayload JSON format:\n"
    '{"verdict": "HEALTHY|WARNING|FAILURE|INCONCLUSIVE|PROMISING", '
    '"summary": "1-2 sentence summary", '
    '"evidence": "detailed evidence with specific numbers and file references", '
    '"confidence": "0.0-1.0"}\n\n'
    "Respond ONLY with the JSON object. Use your tools to verify claims before producing the verdict.\n\n"
    "Question: "
)

# 20 candidate questions targeting current BrickLayer 2.0 codebase
# All are verifiable by tool-enabled agents reading actual files
CANDIDATE_QUESTIONS = [
    # WARNING — known design issues verifiable in code
    {
        "id": "E12.1-live-1",
        "text": (
            "The `eval_agent.py` script runs agent inference with `--no-session-persistence` "
            "and `--setting-sources ''`. Does this configuration correctly prevent the agent "
            "from reading any files on disk, or are there code paths where file access could "
            "still occur during eval? Read `masonry/scripts/eval_agent.py` to verify."
        ),
    },
    {
        "id": "E12.1-live-2",
        "text": (
            "Does `masonry/src/metrics.py` `build_metric()` correctly handle the case where "
            "both predicted and expected verdicts are empty strings? Is there a division-by-zero "
            "or KeyError risk in the current implementation? Read the file to verify."
        ),
    },
    {
        "id": "E12.1-live-3",
        "text": (
            "The `optimize_with_claude.py` script writes optimized instructions back to agent "
            ".md files. Does the `writeback_optimized_instructions()` function in "
            "`masonry/src/writeback.py` have a guard to prevent overwriting non-DSPy content "
            "outside the delimited section? Read both files to verify."
        ),
    },
    {
        "id": "E12.1-live-4",
        "text": (
            "In `masonry/scripts/eval_agent.py`, the `_score_example()` function applies a "
            "2-stage scoring: prose responses get 0.40 max, JSON responses get full scoring. "
            "Is the 0.50 pass threshold correctly calibrated such that prose responses always "
            "fail (score < 0.50) and correct-verdict JSON responses always pass (score >= 0.50)? "
            "Read `eval_agent.py` and `masonry/src/metrics.py` to verify."
        ),
    },
    {
        "id": "E12.1-live-5",
        "text": (
            "The `eval_agent_live.py` script uses `--dangerously-skip-permissions` to enable "
            "non-interactive tool approval. What is the security risk of running this flag in "
            "a shared environment, and does the script have any scope limitation to prevent "
            "the agent from modifying production files during eval? Read the script to verify."
        ),
    },
    # HEALTHY — design decisions that are sound as implemented
    {
        "id": "E12.1-live-6",
        "text": (
            "Does `masonry/src/metrics.py` `build_metric()` correctly implement the verdict "
            "prerequisite gate — capping score at 0.20 when verdict_match == 0.0? Verify "
            "that this prevents the calibration inversion where wrong verdict + good evidence "
            "previously produced a false pass score of 0.60."
        ),
    },
    {
        "id": "E12.1-live-7",
        "text": (
            "Does the `masonry-guard.js` hook correctly scope error signal detection to "
            "`newString` content only (not the full JSON response including `oldString`)? "
            "Read the hook implementation to verify this fix from E8.4 is correctly applied."
        ),
    },
    {
        "id": "E12.1-live-8",
        "text": (
            "Does `masonry/scripts/improve_agent.py` correctly revert optimized instructions "
            "when a loop cycle produces a regression (lower score than baseline)? Read the "
            "revert logic in the script to verify the guard is implemented."
        ),
    },
    {
        "id": "E12.1-live-9",
        "text": (
            "In `masonry/src/writeback.py`, does `writeback_optimized_instructions()` correctly "
            "update ALL copies of an agent's .md file (global ~/.claude/agents/, project "
            ".claude/agents/, and .claude/agents/ in each project folder) when writing back "
            "optimized instructions? Read the function to count how many paths are updated."
        ),
    },
    {
        "id": "E12.1-live-10",
        "text": (
            "The `eval_agent.py` script's `_score_example()` function uses `build_metric()` "
            "from `masonry/src/metrics.py`. Does the function correctly extract the agent's "
            "predicted verdict from both dict-style outputs (JSON) and SimpleNamespace "
            "objects? Verify by reading the function's type handling code."
        ),
    },
    # WARNING — architectural gaps the tool-enabled agent can identify
    {
        "id": "E12.1-live-11",
        "text": (
            "The `scored_all.jsonl` training data file contains records for multiple agents. "
            "Is there a deduplication check that prevents the same `question_id` from "
            "appearing twice across different agent entries? Read any merge or validation "
            "scripts in `masonry/scripts/` to determine if this guard exists."
        ),
    },
    {
        "id": "E12.1-live-12",
        "text": (
            "The BrickLayer 2.0 evolve mode uses `masonry/scripts/eval_agent.py` to score "
            "agents. Does the eval harness validate that the agent under test is using the "
            "CURRENT version of its `.md` instruction file (vs a cached or stale version)? "
            "Read `eval_agent.py` to check if there's a freshness or version check."
        ),
    },
    {
        "id": "E12.1-live-13",
        "text": (
            "In `masonry/scripts/optimize_with_claude.py`, the optimization prompt includes "
            "both high-scoring and low-scoring examples from training data. Is there a risk "
            "that low-scoring examples contain adversarial or misleading content that could "
            "corrupt the optimized instructions? Read the example selection and prompt "
            "construction code to assess this risk."
        ),
    },
    {
        "id": "E12.1-live-14",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` accurately reflect the current "
            "state of the agent eval scores as of Wave 11? Read synthesis.md and compare "
            "the 'Updated Cumulative Agent Eval Scores' table against the Wave 11 findings "
            "in `bricklayer-v2/findings/evolve/E11.1.md` and `E11.2.md`."
        ),
    },
    {
        "id": "E12.1-live-15",
        "text": (
            "The `eval_agent_live.py` script writes a temporary file containing agent "
            "instructions for each eval record. Is the temp file correctly cleaned up "
            "after each subprocess call, including in error/timeout cases? Read the "
            "`try/finally` block in the script to verify."
        ),
    },
    # PROMISING — improvements that look high-value but unverified
    {
        "id": "E12.1-live-16",
        "text": (
            "The research-analyst eval currently averages 0.44–0.61 with tool-free eval "
            "and 0.50 with live eval (E11.1 pilot, 8 records). Would adding a "
            "`--max-tokens` limit to the live eval subprocess call reduce timeout risk "
            "while preserving verdict quality? Read `eval_agent_live.py` to assess "
            "whether max-tokens is a viable lever."
        ),
    },
    {
        "id": "E12.1-live-17",
        "text": (
            "The `improve_agent.py` optimization loop uses `--num-examples 15` per quality "
            "tier by default. Is there evidence in the optimization history files under "
            "`masonry/agent_snapshots/` that more examples (e.g., 25) would produce higher "
            "scores? Read any available snapshot or history files for research-analyst."
        ),
    },
    # INCONCLUSIVE — genuinely ambiguous questions even with tools
    {
        "id": "E12.1-live-18",
        "text": (
            "The masonry-agent-onboard.js hook auto-onboards new agent .md files to the "
            "agent registry. Is the onboarding process idempotent — does running it twice "
            "on the same agent produce a duplicate registry entry, or does it detect and "
            "skip existing agents? Read `masonry/scripts/onboard_agent.py` to determine "
            "if deduplication logic exists."
        ),
    },
    {
        "id": "E12.1-live-19",
        "text": (
            "Does the BrickLayer 2.0 `program.md` evolve mode stop condition — 'all "
            "high-ROI candidates explored, OR marginal gain < 3% across all remaining "
            "candidates' — have a quantitative definition of 'marginal gain' that an "
            "agent can objectively evaluate? Read `bricklayer-v2/modes/evolve.md` and "
            "assess whether the stop condition is operationally precise."
        ),
    },
    {
        "id": "E12.1-live-20",
        "text": (
            "The `masonry/training_data/scored_all.jsonl` file currently has 500 records. "
            "What is the distribution of records by agent? Are there any agents in the "
            "`.claude/agents/` directory that have zero training records, making them "
            "unable to be evaluated? Read scored_all.jsonl and list the agents directory."
        ),
    },
]


def _read_agent_instructions(agent_name: str) -> str:
    md_path = _AGENTS_DIR / f"{agent_name}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Agent file not found: {md_path}")
    return md_path.read_text(encoding="utf-8")


def run_question(question_text: str, agent_instructions: str) -> dict | None:
    """Run one question through the live eval harness. Returns parsed output or None."""
    user_msg = _LIVE_PREAMBLE + question_text

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as sp_file:
        sp_file.write(agent_instructions)
        sp_name = sp_file.name

    try:
        proc = subprocess.run(
            _CLAUDE_CMD + [
                "--print",
                "--model", _DEFAULT_MODEL,
                "--system-prompt-file", sp_name,
                "--output-format", "json",
                "--dangerously-skip-permissions",
            ],
            input=user_msg,
            capture_output=True,
            text=True,
            cwd=str(_SCRIPT_ROOT),
            timeout=_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None
    finally:
        Path(sp_name).unlink(missing_ok=True)

    raw = proc.stdout.strip()
    try:
        envelope = json.loads(raw)
        if isinstance(envelope, dict) and "result" in envelope:
            raw = envelope["result"]
    except (json.JSONDecodeError, ValueError):
        pass

    # Strip markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:raw.rfind("```")]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {"verdict": "PROSE", "summary": raw[:200], "evidence": raw[:500], "confidence": "0.5"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="masonry/training_data/live_records_staging.jsonl")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=len(CANDIDATE_QUESTIONS))
    args = parser.parse_args()

    output_path = _SCRIPT_ROOT / args.output
    agent_instructions = _read_agent_instructions("research-analyst")
    questions = CANDIDATE_QUESTIONS[args.start:args.end]

    print(f"[live-gen] research-analyst | {len(questions)} questions | tools ENABLED")
    print(f"[live-gen] Output: {output_path}")
    print(f"[live-gen] Timeout: {_TIMEOUT}s/question")
    print()

    results = []
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']} ... ", end="", flush=True)
        output = run_question(q["text"], agent_instructions)

        if output is None:
            print("TIMEOUT")
            continue

        verdict = output.get("verdict", "PROSE")
        print(f"{verdict} (confidence={output.get('confidence', '?')})")

        record = {
            "question_id": q["id"],
            "agent": "research-analyst",
            "score": 99,  # placeholder — will be set after review
            "input": {"question_text": q["text"]},
            "output": {
                "verdict": verdict,
                "severity": output.get("severity", "Medium"),
                "confidence": str(output.get("confidence", "0.75")),
                "summary": output.get("summary", ""),
                "evidence": output.get("evidence", ""),
            },
            "_live_generated": True,
            "_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)

        # Write incrementally so partial results are saved on interrupt
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nDone: {len(results)}/{len(questions)} completed")
    print(f"Output: {output_path}")

    # Summary
    verdicts: dict[str, int] = {}
    for r in results:
        v = r["output"]["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    print(f"Verdicts: {verdicts}")


if __name__ == "__main__":
    main()
