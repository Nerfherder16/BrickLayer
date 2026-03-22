"""R23.1 — MIPROv2 optimization trial for quantitative-analyst.

Builds dataset manually from ADBP findings (inline **Agent**: field),
runs baseline metric score, then optimize_agent(), then post-optimization score.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from masonry.src.dspy_pipeline.training_extractor import (
    extract_finding,
    _load_project_brief,
)
from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
from masonry.src.dspy_pipeline.optimizer import (
    build_metric,
    configure_dspy,
    optimize_agent,
)

import dspy

_AGENT_RE = re.compile(r"^\*\*Agent\*\*:\s*(\S+)", re.MULTILINE)
_QUESTION_RE = re.compile(r"^\*\*Question\*\*:\s*(.+)", re.MULTILINE)


def load_qa_dataset(findings_dir: Path) -> list[dict]:
    """Load quantitative-analyst findings with inline **Agent** field."""
    examples = []
    for f in sorted(findings_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        agent_m = _AGENT_RE.search(text)
        if not agent_m or agent_m.group(1).strip() != "quantitative-analyst":
            continue
        ex = extract_finding(f)
        if ex is None:
            continue
        ex["agent"] = "quantitative-analyst"
        q_m = _QUESTION_RE.search(text)
        if q_m:
            ex["question_text"] = q_m.group(1).strip()
        ex["project_context"] = _load_project_brief(str(f))
        # Shape to ResearchAgentSig fields
        ex.setdefault("question_text", ex.get("question_id", ""))
        ex.setdefault("project_context", "")
        ex.setdefault("constraints", "")
        ex.setdefault("severity", "")
        ex.setdefault("evidence", "")
        ex.setdefault("mitigation", "")
        ex.setdefault("confidence", "0.75")
        examples.append(ex)
    return examples


def score_dataset(module: dspy.Module, trainset: list[dspy.Example], metric) -> float:
    """Score a module on the trainset using the heuristic metric."""
    if not trainset:
        return 0.0
    scores = []
    for ex in trainset:
        try:
            pred = module(**{k: getattr(ex, k) for k in ResearchAgentSig.input_fields})
            scores.append(metric(ex, pred))
        except Exception as e:
            print(f"  [score] error on example: {e}", file=sys.stderr)
            scores.append(0.0)
    return sum(scores) / len(scores)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    findings_dir = ROOT / "adbp" / "findings"
    output_dir = ROOT / "masonry" / "optimized_prompts"

    print(f"[R23.1] Loading quantitative-analyst dataset from {findings_dir}")
    raw_examples = load_qa_dataset(findings_dir)
    print(f"[R23.1] Found {len(raw_examples)} training examples")

    if len(raw_examples) < 5:
        print("[R23.1] FAILURE: insufficient training data (need >= 5)", file=sys.stderr)
        sys.exit(1)

    # Configure DSPy with Ollama backend
    print("[R23.1] Configuring DSPy with Ollama backend (qwen3:14b)")
    configure_dspy(backend="ollama")

    # Build DSPy Examples
    input_keys = list(ResearchAgentSig.input_fields.keys())
    trainset = [dspy.Example(**ex).with_inputs(*input_keys) for ex in raw_examples]
    print(f"[R23.1] Built {len(trainset)} DSPy Examples with input keys: {input_keys}")

    # Baseline score (unoptimized module)
    metric = build_metric(ResearchAgentSig)
    baseline_module = dspy.ChainOfThought(ResearchAgentSig)

    print("[R23.1] Scoring baseline (unoptimized) on first 10 examples...")
    sample = trainset[:10]
    t0 = time.time()
    baseline_score = score_dataset(baseline_module, sample, metric)
    baseline_elapsed = time.time() - t0
    print(f"[R23.1] Baseline score: {baseline_score:.4f} (elapsed {baseline_elapsed:.1f}s)")

    # Run MIPROv2 optimization
    print("[R23.1] Starting MIPROv2 optimization (this may take 5-15 minutes)...")
    t_opt_start = time.time()
    result = optimize_agent(
        agent_name="quantitative-analyst",
        signature_cls=ResearchAgentSig,
        dataset=raw_examples,
        output_dir=output_dir,
        backend="ollama",
    )
    opt_elapsed = time.time() - t_opt_start
    print(f"[R23.1] Optimization complete in {opt_elapsed:.1f}s")
    print(f"[R23.1] optimize_agent result: {json.dumps(result, indent=2)}")

    # Post-optimization score
    output_file = output_dir / "quantitative-analyst.json"
    post_score = result.get("score", 0.0)
    print(f"[R23.1] Post-optimization score (from result): {post_score:.4f}")
    print(f"[R23.1] Output file exists: {output_file.exists()}")
    if output_file.exists():
        raw_out = json.loads(output_file.read_text(encoding="utf-8"))
        print(f"[R23.1] Output file keys: {list(raw_out.keys())}")

    # Summary
    delta = post_score - baseline_score
    print()
    print("=" * 60)
    print(f"  Baseline score  : {baseline_score:.4f}")
    print(f"  Post-opt score  : {post_score:.4f}")
    print(f"  Delta           : {delta:+.4f}")
    print(f"  Wall-clock time : {opt_elapsed:.1f}s")
    print(f"  Training records: {len(raw_examples)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
