"""CLI to optimize a single agent using scored training data.

Usage:
    python masonry/scripts/run_optimization.py research-analyst
    python masonry/scripts/run_optimization.py karen --api-key sk-...
    python masonry/scripts/run_optimization.py karen --signature karen --num-trials 20
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def load_training_data_from_scored_all(
    scored_path: Path,
    agent_name: str,
    base_dir: Path | None = None,
) -> list[dict]:
    """Load and filter training examples for a specific agent from scored_all.jsonl."""
    project_context = ""
    if base_dir is not None:
        brief = Path(base_dir) / "project-brief.md"
        if brief.exists():
            project_context = brief.read_text(encoding="utf-8").strip()

    examples = []
    try:
        for line in Path(scored_path).read_text(encoding="utf-8").splitlines():
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
            examples.append({
                "question_text": inp.get("question_text", ""),
                "project_context": project_context,
                "constraints": inp.get("constraints", ""),
                "verdict": out.get("verdict", ""),
                "severity": out.get("severity", ""),
                "evidence": out.get("evidence", ""),
                "mitigation": out.get("mitigation", ""),
                "confidence": str(out.get("confidence", "")),
            })
    except OSError:
        pass

    return examples


def run(
    agent_name: str,
    base_dir: Path,
    backend: str,
    num_trials: int,
    valset_size: int,
    signature: str,
    api_key: str | None = None,
) -> int:
    """Run optimization for agent_name. Returns exit code."""
    from masonry.src.dspy_pipeline.optimizer import configure_dspy, optimize_agent
    from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

    configure_dspy(api_key=api_key, backend=backend)

    scored_path = Path(base_dir) / "scored_all.jsonl"
    examples = load_training_data_from_scored_all(scored_path, agent_name, base_dir=base_dir)

    sig_cls = KarenSig if signature == "karen" else ResearchAgentSig
    output_dir = Path(base_dir) / "optimized"

    result = optimize_agent(agent_name, sig_cls, examples, output_dir)
    print(json.dumps(result, indent=2))
    return 0


def _main() -> None:
    parser = argparse.ArgumentParser(description="Optimize an agent using DSPy.")
    parser.add_argument("agent_name", help="Name of the agent to optimize")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument("--backend", default="anthropic", choices=["anthropic", "ollama"])
    parser.add_argument("--num-trials", type=int, default=10)
    parser.add_argument("--valset-size", type=int, default=100)
    parser.add_argument("--signature", default="research", choices=["research", "karen"])
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    sys.exit(run(
        args.agent_name,
        args.base_dir,
        args.backend,
        args.num_trials,
        args.valset_size,
        args.signature,
        api_key=args.api_key,
    ))


if __name__ == "__main__":
    _main()
