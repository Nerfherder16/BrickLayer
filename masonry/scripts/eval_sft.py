"""masonry/scripts/eval_sft.py

Eval bricklayer-sft (Ollama) against held-out scored_all.jsonl examples.
Uses the same scoring metrics as eval_agent.py for an apples-to-apples comparison.

Usage:
    python masonry/scripts/eval_sft.py karen --eval-size 30
    python masonry/scripts/eval_sft.py research-analyst --eval-size 20
    python masonry/scripts/eval_sft.py karen --compare  # also run claude-haiku baseline

Output:
    Prints per-example scores + overall score.
    Writes masonry/agent_snapshots/{agent}/eval_sft_latest.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from masonry.src.metrics import build_metric  # noqa: E402
from masonry.scripts.export_sharegpt import (  # noqa: E402
    _format_human_turn,
    _find_agent_md,
)

_OLLAMA_HOST = "http://100.70.195.84:11434"
_SFT_MODEL = "bricklayer-sft"
_SCORED_PATH = _SCRIPT_ROOT / "masonry" / "training_data" / "scored_all.jsonl"
_SNAPSHOT_DIR = _SCRIPT_ROOT / "masonry" / "agent_snapshots"

_KAREN_JSON_INSTRUCTION = (
    "Respond ONLY with a valid JSON object and no other text. "
    'The JSON must have exactly these keys: '
    '"doc_files_written" (integer: number of doc files that need updating, 0 if none), '
    '"reverted" (boolean: true only if this is a revert commit).'
)

_RESEARCH_JSON_INSTRUCTION = (
    "You are being evaluated on a research assessment task. "
    "You are given a question_text describing a hypothesis or claim to stress-test. "
    "Based ONLY on your knowledge and the provided context, assess whether the claim holds. "
    "Respond ONLY with a valid JSON object and no other text. "
    'The JSON must have exactly these keys: '
    '"verdict" (one of: "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "PROMISING"), '
    '"summary" (1-2 sentence summary of your assessment), '
    '"evidence" (detailed evidence string, minimum 300 characters, include specific numbers or thresholds), '
    '"confidence" (decimal string 0.0-1.0 reflecting your certainty).'
)


def _ollama_chat(system: str, user: str, model: str = _SFT_MODEL, host: str = _OLLAMA_HOST) -> str:
    """Call Ollama chat API and return the assistant message content."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    return body["message"]["content"]


def _load_records(agent: str) -> list[dict]:
    records = []
    for line in _SCORED_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("agent") == agent and rec.get("score", 0) >= 80:
            records.append(rec)
    return records


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


def _extract_json(text: str) -> str:
    """Extract first JSON object from text (handles leading prose, Output: prefix, etc.)."""
    text = _strip_fences(text)
    # Find the first { and last } to extract JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _score_karen(record: dict, raw: str) -> tuple[float, dict]:
    """Score karen prediction against expected {doc_files_written, reverted}."""
    try:
        predicted = json.loads(_extract_json(raw))
    except (json.JSONDecodeError, ValueError):
        return 0.0, {}

    expected = record.get("output", {})
    exp_reverted = expected.get("reverted", False)
    exp_doc_files = int(expected.get("doc_files_written", 0) or 0)

    pred_reverted = predicted.get("reverted", None)
    pred_doc_files = predicted.get("doc_files_written", None)

    if pred_reverted is None and pred_doc_files is None:
        return 0.0, predicted

    score = 0.0
    if pred_reverted is not None and bool(pred_reverted) == bool(exp_reverted):
        score += 0.5
    if pred_doc_files is not None and (int(pred_doc_files) > 0) == (exp_doc_files > 0):
        score += 0.5
    return score, predicted


def _score_prose(text: str) -> float:
    _KEYWORDS = ("threshold", "baseline", "%", "ms", "pts", "seconds")
    has_numbers = bool(re.search(r"\d+\.?\d*", text))
    has_kw = any(kw in text.lower() for kw in _KEYWORDS)
    return 0.4 if len(text) > 300 and (has_numbers or has_kw) else 0.2


def _score_example(record: dict, raw: str, metric_fn: Any, prose: bool = False) -> tuple[float, dict]:
    try:
        predicted = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, ValueError):
        return (_score_prose(raw), {}) if prose else (0.0, {})

    expected = record.get("expected", record.get("output", {}))
    pred_ns = SimpleNamespace(**predicted) if isinstance(predicted, dict) else predicted
    exp_ns = SimpleNamespace(**expected) if isinstance(expected, dict) else expected
    try:
        score = float(metric_fn(exp_ns, pred_ns))
    except Exception:
        score = 0.0
    return score, predicted


def run_eval(agent: str, eval_size: int = 30, model: str = _SFT_MODEL) -> dict:
    records = _load_records(agent)
    if not records:
        print(f"[eval_sft] No records found for agent '{agent}' in scored_all.jsonl")
        sys.exit(1)

    random.seed(42)
    sampled = random.sample(records, min(eval_size, len(records)))
    print(f"[eval_sft] Evaluating {len(sampled)} examples for agent={agent} model={model}")

    is_karen = agent == "karen"
    metric_fn = build_metric(object)
    json_instruction = _KAREN_JSON_INSTRUCTION if is_karen else _RESEARCH_JSON_INSTRUCTION
    system_prompt = _find_agent_md(agent) or "You are a helpful AI assistant."

    passed = 0
    examples_out = []

    for i, rec in enumerate(sampled, 1):
        human = _format_human_turn(rec)
        # Karen: use training-format prompt (same human turn as training data)
        # Research: append JSON instruction to question
        if is_karen:
            user_msg = f"{human}\n\n{json_instruction}"
        else:
            user_msg = f"{json_instruction}\n\nInput:\n{json.dumps(rec.get('input', {}))}"

        try:
            raw = _ollama_chat(system=system_prompt, user=user_msg, model=model)
        except Exception as e:
            print(f"  [{i}/{len(sampled)}] ERROR: {e}")
            examples_out.append({"input": rec.get("input"), "score": 0.0, "error": str(e)})
            continue

        if is_karen:
            score, predicted = _score_karen(rec, raw)
        else:
            score, predicted = _score_example(rec, raw, metric_fn, prose=True)
        if score >= 0.5:
            passed += 1

        preview = human[:60].replace("\n", " ")
        print(f"  [{i}/{len(sampled)}] score={score:.2f}  {preview}")
        examples_out.append({
            "input": rec.get("input"),
            "expected": rec.get("output", {}),
            "predicted": predicted,
            "raw": raw[:200],
            "score": score,
        })

    overall = passed / len(sampled) if sampled else 0.0
    print(f"\n[eval_sft] score={overall:.2f} ({passed}/{len(sampled)} passed)  model={model}")

    out_dir = _SNAPSHOT_DIR / agent
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "agent": agent,
        "model": model,
        "score": overall,
        "eval_size": len(sampled),
        "passed": passed,
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "examples": examples_out,
    }
    suffix = "sft" if model == _SFT_MODEL else model.replace(":", "_").replace("/", "_")
    out_path = out_dir / f"eval_{suffix}_latest.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[eval_sft] Results written to {out_path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval bricklayer-sft via Ollama")
    parser.add_argument("agent", help="Agent name (e.g. karen, research-analyst)")
    parser.add_argument("--eval-size", type=int, default=30)
    parser.add_argument("--model", default=_SFT_MODEL, help=f"Ollama model (default: {_SFT_MODEL})")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Also run eval against Qwen2.5-3B base for comparison",
    )
    args = parser.parse_args()

    sft_result = run_eval(args.agent, args.eval_size, args.model)

    if args.compare:
        print("\n--- Baseline: Qwen2.5-3B (untuned) ---")
        base_result = run_eval(args.agent, args.eval_size, "qwen2.5:3b")
        print("\n=== Comparison ===")
        print(f"  bricklayer-sft : {sft_result['score']:.2f} ({sft_result['passed']}/{sft_result['eval_size']})")
        print(f"  qwen2.5:3b     : {base_result['score']:.2f} ({base_result['passed']}/{base_result['eval_size']})")
        delta = sft_result["score"] - base_result["score"]
        print(f"  delta          : {delta:+.2f}")


if __name__ == "__main__":
    main()
