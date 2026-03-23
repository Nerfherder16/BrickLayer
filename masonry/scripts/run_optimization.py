"""masonry/scripts/run_optimization.py

CLI entry point for the Kiln OPTIMIZE button.

Usage:
    python masonry/scripts/run_optimization.py <agent_name> [--base-dir DIR]

Prints progress lines to stdout (streamed back to Kiln as optimization-progress events).
Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the BrickLayer root is on sys.path so `masonry` package is importable.
# This script is invoked as: python masonry/scripts/run_optimization.py <agent>
# with cwd=blRoot, so __file__ is blRoot/masonry/scripts/run_optimization.py.
_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent  # blRoot
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))


def load_training_data_from_scored_all(
    scored_all_path: Path,
    agent_name: str,
) -> list[dict]:
    """Load training examples for agent_name from scored_all.jsonl."""
    if not scored_all_path.exists():
        return []

    examples = []
    for line in scored_all_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("agent") != agent_name:
            continue

        inp = rec.get("input", {})
        out = rec.get("output", {})
        examples.append({
            "question_text": inp.get("question_text", inp.get("question_id", "")),
            "project_context": "",
            "constraints": "",
            "verdict": out.get("verdict", ""),
            "severity": out.get("severity", ""),
            "evidence": out.get("evidence", ""),
            "mitigation": "",
            "confidence": str(out.get("confidence") or 0.75),
        })

    return examples


def load_karen_training_data(scored_all_path: Path) -> list[dict]:
    """Load training examples for the karen agent from scored_all.jsonl.

    Maps ops-domain fields to KarenSig I/O:
    - input.commit_subject  → commit_subject
    - input.files_modified  → files_changed (comma-separated string)
    - score / 100.0         → quality_score
    """
    if not scored_all_path.exists():
        return []

    examples = []
    for line in scored_all_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("agent") != "karen":
            continue

        inp = rec.get("input", {})
        out = rec.get("output", {})
        commit_subject = inp.get("commit_subject", "")
        if not commit_subject:
            continue  # skip records without a commit subject

        files_modified = inp.get("files_modified", [])
        files_changed = ", ".join(files_modified) if files_modified else ""
        reverted = bool(out.get("reverted", False))
        doc_files_written = int(out.get("doc_files_written", 0))
        quality_score = str(rec.get("score", 100) / 100.0)
        action = "reverted" if reverted else ("updated" if doc_files_written > 0 else "skipped")

        examples.append({
            "commit_subject": commit_subject,
            "files_changed": files_changed,
            "doc_context": "",
            "action": action,
            "doc_updates": files_changed,
            "changelog_entry": commit_subject,
            "quality_score": quality_score,
        })

    return examples


def update_registry_dspy_status(
    registry_path: Path,
    agent_name: str,
    optimized_at: str,
) -> None:
    """Update agent_registry.yml to mark DSPy optimization complete."""
    if not registry_path.exists():
        return

    content = registry_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    in_target = False
    updated = []

    for line in lines:
        name_match = line.strip().startswith("- name:") or (
            line.strip().startswith("name:") and not line.strip().startswith("name: #")
        )
        if name_match and agent_name in line:
            in_target = True
        elif name_match:
            in_target = False

        if in_target and "dspy_status:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + "dspy_status: optimized"
        elif in_target and "last_optimized:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + f"last_optimized: {optimized_at}"

        updated.append(line)

    registry_path.write_text("\n".join(updated), encoding="utf-8")


def run(
    agent_name: str,
    base_dir: Path,
    backend: str = "anthropic",
    num_trials: int = 10,
    valset_size: int = 100,
    signature: str = "research",
) -> int:
    """Run optimization for agent_name. Returns exit code (0=success, 1=failure).

    Args:
        agent_name: Name of the agent to optimize.
        base_dir: BrickLayer root directory.
        backend: LM backend — ``"anthropic"`` or ``"ollama"``.
        num_trials: Number of Bayesian optimization trials (default: 10).
        valset_size: Validation set size for trials (default: 100).
        signature: DSPy signature to use — ``"research"`` (default) or ``"karen"``.
    """

    print(f"[init] Starting optimization for: {agent_name}")
    print(f"[init] Base directory: {base_dir}")
    print(f"[init] Backend: {backend}")
    print(f"[init] Num trials: {num_trials}")
    print(f"[init] Valset size: {valset_size}")
    print(f"[init] Signature: {signature}")

    # ── Load training data ───────────────────────────────────────────────────
    # Self-research mode: CWD is masonry/ dir
    _self_research_td = base_dir / "training_data"
    _normal_td = base_dir / "masonry" / "training_data"
    _td_dir = _self_research_td if _self_research_td.exists() else _normal_td
    scored_all_path = _td_dir / "scored_all.jsonl"
    print(f"[data] Loading training data from scored_all.jsonl ...")

    if signature == "karen":
        examples = load_karen_training_data(scored_all_path)
    else:
        examples = load_training_data_from_scored_all(scored_all_path, agent_name)

    # Fallback: try the old build_dataset() approach if scored_all is empty
    if not examples:
        print(f"[data] No records in scored_all.jsonl for {agent_name}, trying legacy extractor ...")
        try:
            from masonry.src.dspy_pipeline.training_extractor import build_dataset
            agent_db_path = base_dir / "masonry" / "agent_db.json"
            datasets = build_dataset(projects_dir=base_dir, agent_db_path=agent_db_path)
            examples = datasets.get(agent_name, [])
        except Exception as exc:
            print(f"[data] Legacy extractor failed: {exc}")

    if not examples:
        print(f"[error] No training data found for {agent_name}.")
        print(f"[error] Run 'Score All' first to generate training data.")
        return 1

    print(f"[data] Found {len(examples)} training examples.")

    if len(examples) < 3:
        print(f"[error] Only {len(examples)} example(s) — need at least 3 to optimize.")
        print(f"[error] Run more campaigns to accumulate training data, then Score All.")
        return 1
    elif len(examples) < 10:
        print(f"[warn] Only {len(examples)} examples — optimization works best with 10+.")
        print(f"[warn] Proceeding anyway.")

    # ── Configure DSPy ───────────────────────────────────────────────────────
    _model_label = "qwen3:14b (Ollama)" if backend == "ollama" else "claude-sonnet-4-6 (Anthropic)"
    print(f"[dspy] Configuring DSPy with {_model_label} ...")
    try:
        from masonry.src.dspy_pipeline.optimizer import configure_dspy, optimize_agent
        from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig
        configure_dspy(backend=backend)
        print(f"[dspy] DSPy configured.")
    except ImportError as exc:
        if "dspy" in str(exc).lower():
            print(f"[error] DSPy not installed: {exc}")
            print(f"[error] Install with: pip install dspy-ai")
        else:
            print(f"[error] Import failed: {exc}")
            print(f"[error] Check that PYTHONPATH includes the BrickLayer root.")
        return 1
    except Exception as exc:
        print(f"[error] DSPy configuration failed: {exc}")
        return 1

    # ── Run optimization ─────────────────────────────────────────────────────
    output_dir = base_dir / "masonry" / "optimized_prompts"
    print(f"[optimize] Running MIPROv2 for {agent_name} ...")
    print(f"[optimize] This may take several minutes ...")

    try:
        result = optimize_agent(
            agent_name=agent_name,
            signature_cls=ResearchAgentSig,
            dataset=examples,
            output_dir=output_dir,
            backend=backend,
            num_trials=num_trials,
            valset_size=valset_size,
        )
    except Exception as exc:
        print(f"[error] Optimization failed: {exc}")
        return 1

    score = result.get("score", 0.0)
    optimized_at = result.get("optimized_at", "")
    output_file = output_dir / f"{agent_name}.json"

    print(f"[optimize] Complete. Best score: {score:.3f}")
    print(f"[optimize] Saved to: {output_file}")

    # ── Update registry ──────────────────────────────────────────────────────
    registry_path = base_dir / "masonry" / "agent_registry.yml"
    if registry_path.exists() and optimized_at:
        try:
            update_registry_dspy_status(registry_path, agent_name, optimized_at)
            print(f"[registry] Updated agent_registry.yml — dspy_status: optimized")
        except Exception as exc:
            print(f"[warn] Could not update registry: {exc}")

    print(f"[done] Optimization complete for {agent_name}.")
    return 0


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimize a Masonry agent prompt via DSPy MIPROv2."
    )
    parser.add_argument("agent_name", help="Name of the agent to optimize")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="BrickLayer root directory (default: cwd)",
    )
    parser.add_argument(
        "--backend",
        default="anthropic",
        choices=["anthropic", "ollama"],
        help='LM backend: "anthropic" (default) or "ollama" (uses http://192.168.50.62:11434)',
    )
    parser.add_argument(
        "--num-trials",
        type=int,
        default=10,
        help="Number of Bayesian optimization trials (default: 10)",
    )
    parser.add_argument(
        "--valset-size",
        type=int,
        default=100,
        help="Validation set size for trials (default: 100)",
    )
    args = parser.parse_args()

    sys.exit(run(
        agent_name=args.agent_name,
        base_dir=args.base_dir.resolve(),
        backend=args.backend,
        num_trials=args.num_trials,
        valset_size=args.valset_size,
    ))


if __name__ == "__main__":
    _main()
