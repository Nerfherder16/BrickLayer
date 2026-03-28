"""masonry/scripts/run_optimization.py

CLI entry point for running DSPy-based agent optimization.

Usage:
    python masonry/scripts/run_optimization.py <agent_name> [options]

    Options:
      --base-dir DIR         BrickLayer root (default: cwd)
      --backend BACKEND      LM backend: anthropic | ollama (default: anthropic)
      --num-trials N         MIPROv2 trials (default: 10)
      --valset-size N        Validation set size (default: 100)
      --signature SIG        Signature class: research | karen (default: research)
      --api-key KEY          API key (default: ANTHROPIC_API_KEY env var)

Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))


# ---------------------------------------------------------------------------
# Training data loader
# ---------------------------------------------------------------------------


def load_training_data_from_scored_all(
    scored_all_path: Path,
    agent_name: str,
    base_dir: Path | None = None,
) -> list[dict]:
    """Load training examples for *agent_name* from a scored_all.jsonl file.

    Parameters
    ----------
    scored_all_path:
        Path to the ``scored_all.jsonl`` file.
    agent_name:
        Only records with this agent name are returned.
    base_dir:
        Optional project root. When provided, ``project-brief.md`` is read and
        its contents placed into the ``project_context`` field of each example.

    Returns
    -------
    List of training example dicts with keys matching ResearchAgentSig input/output fields.
    """
    if not Path(scored_all_path).exists():
        return []

    # Load project context from project-brief.md if base_dir provided
    project_context = ""
    if base_dir is not None:
        brief_path = Path(base_dir) / "project-brief.md"
        if brief_path.exists():
            project_context = brief_path.read_text(encoding="utf-8").strip()

    examples: list[dict] = []
    for line in Path(scored_all_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if record.get("agent") != agent_name:
            continue

        inp = record.get("input", {})
        out = record.get("output", {})

        example = {
            "question_text": inp.get("question_text", ""),
            "project_context": project_context,
            "constraints": inp.get("constraints", ""),
            "verdict": out.get("verdict", ""),
            "severity": out.get("severity", ""),
            "evidence": out.get("evidence", ""),
            "mitigation": out.get("mitigation", ""),
            "confidence": str(out.get("confidence", "0.75")),
        }
        examples.append(example)

    return examples


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------


def run(
    agent_name: str,
    base_dir: Path,
    backend: str = "anthropic",
    num_trials: int = 10,
    valset_size: int = 100,
    signature: str = "research",
    api_key: str | None = None,
) -> int:
    """Run DSPy optimization for a single agent.

    Returns exit code (0 = success, 1 = failure).
    """
    from masonry.src.dspy_pipeline.optimizer import configure_dspy, optimize_agent
    from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

    sig_cls = KarenSig if signature == "karen" else ResearchAgentSig

    # Configure DSPy backend
    if backend == "ollama":
        model = "ollama_chat/llama3"
    else:
        model = "anthropic/claude-haiku-4-5"

    configure_dspy(model, api_key=api_key)

    # Load training data
    scored_all_path = base_dir / "scored_all.jsonl"
    dataset = load_training_data_from_scored_all(scored_all_path, agent_name, base_dir=base_dir)

    if len(dataset) < 5:
        print(f"[run_optimization] Not enough data for {agent_name}: {len(dataset)} examples (need 5)")
        return 1

    output_dir = base_dir / "masonry" / "optimized_prompts"
    result = optimize_agent(
        agent_name,
        sig_cls,
        dataset,
        output_dir,
        num_trials=num_trials,
        valset_size=valset_size,
    )
    print(f"[run_optimization] Optimized {agent_name}: score={result.get('score')}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run DSPy agent optimization")
    parser.add_argument("agent_name", help="Name of the agent to optimize")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument("--backend", default="anthropic", choices=["anthropic", "ollama"])
    parser.add_argument("--num-trials", type=int, default=10)
    parser.add_argument("--valset-size", type=int, default=100)
    parser.add_argument("--signature", default="research", choices=["research", "karen"])
    parser.add_argument("--api-key", default=None)

    args = parser.parse_args()

    # Fall back to environment variable when --api-key not provided
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")

    exit_code = run(
        agent_name=args.agent_name,
        base_dir=args.base_dir,
        backend=args.backend,
        num_trials=args.num_trials,
        valset_size=args.valset_size,
        signature=args.signature,
        api_key=api_key,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    _main()
