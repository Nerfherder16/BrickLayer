"""masonry/scripts/generate_synth_records.py

Generate live-eval-calibrated training records for synthesizer-bl2.
Runs each candidate question through the live eval harness (tools enabled),
collects tool-enabled agent outputs as gold labels, and saves records
to a staging JSONL file for review before adding to scored_all.jsonl.

Usage:
    python masonry/scripts/generate_synth_records.py
    python masonry/scripts/generate_synth_records.py --output masonry/training_data/synth_records_staging.jsonl
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

# 10 candidate questions targeting synthesizer-bl2 quality in the current BrickLayer 2.0 codebase.
# All are verifiable by tool-enabled agents reading actual files.
CANDIDATE_QUESTIONS = [
    {
        "id": "E12.3-synth-1",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` contain a 'Wave 11' section "
            "documenting the live eval harness implementation (eval_agent_live.py) and the "
            "synthesizer-bl2 data quality fixes? Read synthesis.md and verify the Wave 11 "
            "section exists with accurate verdicts for E11.1 and E11.2."
        ),
    },
    {
        "id": "E12.3-synth-2",
        "text": (
            "The synthesizer-bl2 agent (`synthesizer-bl2.md`) is responsible for writing "
            "synthesis.md after each wave. Does `bricklayer-v2/findings/synthesis.md` "
            "contain accurate cumulative agent eval scores as of Wave 11? Read synthesis.md "
            "and compare the 'Cumulative Agent Eval Scores' table against any available "
            "eval score data in the findings directory."
        ),
    },
    {
        "id": "E12.3-synth-3",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` correctly document the Wave 9 "
            "verdict distribution (how many IMPROVEMENT, HEALTHY, WARNING, INCONCLUSIVE, "
            "REGRESSION verdicts)? Read synthesis.md and count the Wave 9 findings in "
            "bricklayer-v2/findings/evolve/ to verify the counts match."
        ),
    },
    {
        "id": "E12.3-synth-4",
        "text": (
            "The synthesizer-bl2 agent should update ARCHITECTURE.md, CHANGELOG.md, and "
            "ROADMAP.md after each wave. Read `bricklayer-v2/ROADMAP.md` — does it contain "
            "a section listing the active E13.x wave questions from `bricklayer-v2/questions.md`? "
            "The Wave 13 questions were added in the most recent hypothesis-generator-bl2 run."
        ),
    },
    {
        "id": "E12.3-synth-5",
        "text": (
            "The `synthesizer-bl2.md` agent instructions say it should 'commit all docs' "
            "after updating synthesis.md and supporting files. Read the agent instructions "
            "at `.claude/agents/synthesizer-bl2.md` — does the commit step include "
            "ARCHITECTURE.md and ROADMAP.md in addition to synthesis.md and CHANGELOG.md? "
            "Or does the commit step only cover synthesis.md?"
        ),
    },
    {
        "id": "E12.3-synth-6",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` contain a 'Path Forward' or "
            "'Next Steps' section at the end that lists actionable recommendations? "
            "Read synthesis.md and assess whether the current path forward section "
            "is specific and actionable (names specific agents, scores, and thresholds) "
            "or generic/vague."
        ),
    },
    {
        "id": "E12.3-synth-7",
        "text": (
            "The BrickLayer 2.0 Wave 10 included eval work on synthesizer-bl2 (E10.1-E10.3). "
            "Does `bricklayer-v2/findings/synthesis.md` accurately reflect the Wave 10 "
            "synthesizer-bl2 findings? Read synthesis.md and compare against the Wave 10 "
            "finding files E10.1.md, E10.2.md, E10.3.md in bricklayer-v2/findings/evolve/."
        ),
    },
    {
        "id": "E12.3-synth-8",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` document the masonry-guard.js "
            "E8.4 fix (scoping error signal detection to newString only)? Read synthesis.md "
            "and verify this fix is documented with the correct technical detail. "
            "Then read the actual masonry-guard.js hook to confirm the fix is present."
        ),
    },
    {
        "id": "E12.3-synth-9",
        "text": (
            "The synthesizer-bl2 agent instructions define a 'Synthesis Report' format "
            "with specific required sections. Read `.claude/agents/synthesizer-bl2.md` "
            "and then read `bricklayer-v2/findings/synthesis.md` — does the current "
            "synthesis.md follow the format defined in the agent instructions? "
            "Are all required sections present?"
        ),
    },
    {
        "id": "E12.3-synth-10",
        "text": (
            "Does `bricklayer-v2/findings/synthesis.md` correctly identify the top "
            "3 'failure modes' or 'recurring issues' observed across all waves? "
            "Read synthesis.md and assess whether the failure mode analysis is "
            "backed by specific finding references (e.g., 'E8.4 found X, E9.2 confirmed Y') "
            "or is a general summary without evidence anchors."
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
            encoding="utf-8",
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
    parser.add_argument("--output", default="masonry/training_data/synth_records_staging.jsonl")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=len(CANDIDATE_QUESTIONS))
    args = parser.parse_args()

    output_path = _SCRIPT_ROOT / args.output
    agent_instructions = _read_agent_instructions("synthesizer-bl2")
    questions = CANDIDATE_QUESTIONS[args.start:args.end]

    print(f"[live-gen] synthesizer-bl2 | {len(questions)} questions | tools ENABLED")
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
            "agent": "synthesizer-bl2",
            "score": 99,  # placeholder — will be set by merge_live_records.py
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

        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nDone: {len(results)}/{len(questions)} completed")
    print(f"Output: {output_path}")

    verdicts: dict[str, int] = {}
    for r in results:
        v = r["output"]["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    print(f"Verdicts: {verdicts}")


if __name__ == "__main__":
    main()
