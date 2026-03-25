"""masonry/scripts/eval_agent_live.py

Live eval harness — runs research-analyst with tools ENABLED.
Implements Path B from E6.3: eval the agent as it would run in production
(tool-augmented research), not tool-free knowledge-only reasoning.

Usage:
    python masonry/scripts/eval_agent_live.py --eval-size 5
    python masonry/scripts/eval_agent_live.py --eval-size 10 --seed 42

Differences from eval_agent.py (tool-free):
  - No --setting-sources "" (hooks + tools enabled)
  - No --no-session-persistence (allows file access)
  - Adds --dangerously-skip-permissions (non-interactive tool approval)
  - No _RESEARCH_JSON_INSTRUCTION appended — agent prompted as normal research question
  - Timeout: 120s per record (agent uses tools, takes longer)
  - Records scored identically via build_metric() from masonry/src/metrics.py

Output:
    Live score per record, final avg, comparison to tool-free baseline
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_CLAUDE_CMD = ["claude.cmd" if platform.system() == "Windows" else "claude"]

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from masonry.src.metrics import build_metric  # noqa: E402

_DATA_FILE = _SCRIPT_ROOT / "masonry/training_data/scored_all.jsonl"
_DATA_FILE_FINDINGS = _SCRIPT_ROOT / "masonry/training_data/scored_findings.jsonl"
_AGENTS_DIR = _SCRIPT_ROOT / ".claude/agents"
_DEFAULT_MODEL = "claude-sonnet-4-6"

# Live eval prompt: the agent is given the question and asked to research it
# using its production tools (Read, Glob, Grep, WebSearch, etc.)
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


def _load_agent_records(
    agent_name: str, eval_size: int, seed: int, id_prefix: str | None = None,
    include_incompatible: bool = False,
) -> list[dict]:
    """Load records for a given agent from scored_all.jsonl. Optional id_prefix filter.

    Records with eval_compatible=False are skipped by default (they timeout or have
    malformed input). Pass include_incompatible=True to include them anyway.

    If no records are found in scored_all.jsonl for the agent, falls back to
    scored_findings.jsonl (which uses input.question_text instead of input.question).
    The fallback normalizes question_text -> question for downstream compatibility.
    """
    import random

    def _read_from_file(data_file: Path, normalize_question_key: bool = False) -> tuple[list[dict], int]:
        """Read matching records from a JSONL file. Returns (records, skipped_count)."""
        found: list[dict] = []
        skipped = 0
        if not data_file.exists():
            return found, skipped
        with open(data_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("agent") == agent_name:
                        qid = r.get("question_id") or r.get("input", {}).get("question_id", "")
                        if id_prefix is None or str(qid).startswith(id_prefix):
                            if not include_incompatible and r.get("eval_compatible") is False:
                                skipped += 1
                                continue
                            if normalize_question_key:
                                # Normalize scored_findings.jsonl schema: question_text -> question
                                inp = r.get("input", {})
                                if "question_text" in inp and "question" not in inp:
                                    inp = dict(inp)
                                    inp["question"] = inp["question_text"]
                                    r = dict(r, input=inp)
                            found.append(r)
        return found, skipped

    records, skipped = _read_from_file(_DATA_FILE)

    if not records:
        # Primary data file has no records for this agent — try scored_findings.jsonl
        records, skipped_fb = _read_from_file(_DATA_FILE_FINDINGS, normalize_question_key=True)
        skipped += skipped_fb
        if records:
            print(f"[live-eval] Loaded {len(records)} records from scored_findings.jsonl (fallback) for {agent_name}")

    if skipped:
        print(f"[live-eval] Skipped {skipped} eval-incompatible records (pass --include-incompatible to include)")
    rng = random.Random(seed)
    rng.shuffle(records)
    return records[:eval_size]


def _read_agent_instructions(agent_name: str) -> str:
    """Read agent instructions from .claude/agents/{agent_name}.md"""
    md_path = _AGENTS_DIR / f"{agent_name}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Agent file not found: {md_path}")
    return md_path.read_text(encoding="utf-8")


def _score_example(record: dict, raw_output: str) -> tuple[float, Any]:
    """Score a live eval response against the expected output."""
    metric_fn = build_metric()

    # Parse JSON from response
    raw = raw_output.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:raw.rfind("```")]
        raw = raw.strip()

    try:
        pred_dict = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Prose response — give partial evidence quality score, 0 verdict match
        pred = SimpleNamespace(
            verdict="",
            evidence=raw[:1000],
            confidence="0.75",
            summary=raw[:200],
        )
        ex = SimpleNamespace(
            verdict=record.get("output", {}).get("verdict", ""),
            evidence=record.get("output", {}).get("evidence", ""),
            confidence="0.75",
            summary=record.get("output", {}).get("summary", ""),
        )
        # 2-stage: score evidence quality only (max 0.4, below 0.50 threshold)
        import re
        ev = pred.evidence
        has_numbers = bool(re.search(r"\d+\.?\d*", ev))
        has_thresh = any(k in ev.lower() for k in ["baseline", "threshold", "%", "score"])
        evidence_score = 0.4 if (len(ev) > 300 and (has_numbers or has_thresh)) else 0.2
        return evidence_score, pred

    pred = SimpleNamespace(
        verdict=pred_dict.get("verdict", ""),
        evidence=pred_dict.get("evidence", ""),
        confidence=str(pred_dict.get("confidence", "0.75")),
        summary=pred_dict.get("summary", ""),
    )
    ex = SimpleNamespace(
        verdict=record.get("output", {}).get("verdict", ""),
        evidence=record.get("output", {}).get("evidence", ""),
        confidence="0.75",
        summary=record.get("output", {}).get("summary", ""),
    )
    score = metric_fn(ex, pred)
    return score, pred


def run_live_eval(
    eval_size: int = 5,
    seed: int = 42,
    id_prefix: str | None = None,
    agent_name: str = "research-analyst",
    include_incompatible: bool = False,
) -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    records = _load_agent_records(
        agent_name, eval_size, seed, id_prefix=id_prefix,
        include_incompatible=include_incompatible,
    )
    agent_instructions = _read_agent_instructions(agent_name)

    print(f"[live-eval] {agent_name} | {len(records)} records | tools ENABLED")
    print(f"[live-eval] Model: {_DEFAULT_MODEL}")
    print(f"[live-eval] Working directory: {_SCRIPT_ROOT}")
    print()

    passed = 0
    failed = 0
    total_score = 0.0

    for i, record in enumerate(records, 1):
        qid = record.get("question_id", "?")
        expected = record.get("output", {}).get("verdict", "?")
        q_text = (
            record.get("input", {}).get("question_text")
            or record.get("input", {}).get("question", "")
        )
        user_msg = _LIVE_PREAMBLE + q_text

        # Write system prompt to temp file
        import tempfile
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
                    # NOTE: no --setting-sources "" and no --no-session-persistence
                    # This enables tool access in production mode
                ],
                input=user_msg,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(_SCRIPT_ROOT),
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            print(f"[{i}/{len(records)}] {qid} TIMEOUT (>120s)")
            failed += 1
            continue
        finally:
            Path(sp_name).unlink(missing_ok=True)

        raw_output = proc.stdout
        try:
            envelope = json.loads(raw_output)
            if isinstance(envelope, dict) and "result" in envelope:
                raw_output = envelope["result"]
        except (json.JSONDecodeError, ValueError):
            pass

        score, pred = _score_example(record, raw_output)
        total_score += score
        passes = score >= 0.5
        if passes:
            passed += 1
        else:
            failed += 1

        pred_verdict = getattr(pred, "verdict", "?")
        print(
            f"[{i}/{len(records)}] {qid} | expected={expected} | "
            f"predicted={pred_verdict} | score={score:.2f}"
        )

    avg = total_score / len(records) if records else 0.0
    pct = passed / len(records) if records else 0.0
    print(f"\nlive-eval score={avg:.2f} ({passed}/{len(records)} passed at >=0.50)")
    print(f"Passed rate: {pct:.0%}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Live eval harness for BL 2.0 agents")
    parser.add_argument("--agent", type=str, default="research-analyst", help="Agent name to evaluate")
    parser.add_argument("--eval-size", type=int, default=5, help="Number of records to eval")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for record selection")
    parser.add_argument("--id-prefix", type=str, default=None, help="Filter records by question_id prefix")
    parser.add_argument(
        "--include-incompatible",
        action="store_true",
        default=False,
        help="Include records marked eval_compatible=False (timeout/malformed; excluded by default)",
    )
    args = parser.parse_args()
    run_live_eval(
        eval_size=args.eval_size,
        seed=args.seed,
        id_prefix=args.id_prefix,
        agent_name=args.agent,
        include_incompatible=args.include_incompatible,
    )


if __name__ == "__main__":
    main()
