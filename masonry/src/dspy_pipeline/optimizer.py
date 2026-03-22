"""DSPy MIPROv2 optimization pipeline for Masonry agents.

Optimizes agent prompts using campaign findings as training data.
Uses a heuristic metric (no LLM judge required) to keep costs low.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dspy

from masonry.src.schemas.payloads import AgentRegistryEntry


# ── Metric ──────────────────────────────────────────────────────────────────


def build_metric(signature_cls: type) -> Any:
    """Build a heuristic scoring metric for the given DSPy Signature.

    Components:
    - verdict_match (0.4): exact string match of verdict field
    - evidence_quality (0.4): length > 100 chars = 1.0, else 0.5
    - confidence_calibration (0.2): 1 - |predicted - 0.75|

    Returns a callable(example, prediction, trace) -> float.
    The trace parameter is passed by DSPy's MIPROv2 bootstrapper and is ignored here.
    """

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0

        # Verdict match (0.4 weight)
        try:
            ex_verdict = str(getattr(example, "verdict", "") or "").strip()
            pred_verdict = str(getattr(prediction, "verdict", "") or "").strip()
            if ex_verdict and pred_verdict and ex_verdict == pred_verdict:
                score += 0.4
        except Exception:
            pass

        # Evidence quality (0.4 weight)
        try:
            evidence = str(getattr(prediction, "evidence", "") or "")
            if len(evidence) > 100:
                score += 0.4
            else:
                score += 0.2  # partial credit for short evidence
        except Exception:
            pass

        # Confidence calibration (0.2 weight)
        try:
            raw = str(getattr(prediction, "confidence", "0.75") or "0.75")
            pred_conf = float(raw)
            calibration = 1.0 - abs(pred_conf - 0.75)
            score += 0.2 * calibration
        except (ValueError, TypeError):
            score += 0.0  # no calibration if parse fails

        return score

    return metric


# ── configure_dspy ──────────────────────────────────────────────────────────


def configure_dspy(model: str | None = None, backend: str = "anthropic") -> None:
    """Configure DSPy with the specified LM backend.

    Args:
        model: Model name to use. Defaults to ``qwen3:14b`` for Ollama and
            ``claude-sonnet-4-6`` for Anthropic when not specified.
        backend: Either ``"anthropic"`` (requires ANTHROPIC_API_KEY) or
            ``"ollama"`` (uses local Ollama at http://192.168.50.62:11434).
    """
    if backend == "ollama":
        effective_model = model or "qwen3:14b"
        lm = dspy.LM(
            f"ollama_chat/{effective_model}",
            api_base="http://192.168.50.62:11434",
            max_tokens=4096,
        )
    else:
        effective_model = model or "claude-sonnet-4-6"
        lm = dspy.LM(f"anthropic/{effective_model}")
    dspy.configure(lm=lm)


# ── optimize_agent ──────────────────────────────────────────────────────────


def optimize_agent(
    agent_name: str,
    signature_cls: type,
    dataset: list[dict],
    output_dir: Path,
    backend: str = "anthropic",
) -> dict[str, Any]:
    """Optimize a single agent's prompt using MIPROv2.

    Args:
        agent_name: Name of the agent to optimize.
        signature_cls: DSPy Signature class defining the I/O contract.
        dataset: List of training examples (dicts matching signature fields).
        output_dir: Directory to save the optimized module JSON.
        backend: LM backend to use — ``"anthropic"`` or ``"ollama"``.
            Passed through to :func:`configure_dspy` when called by the caller.

    Returns:
        Dict with agent, score, and optimized_at fields.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the module
    module = dspy.ChainOfThought(signature_cls)
    metric = build_metric(signature_cls)

    # Configure optimizer with low-cost settings
    optimizer = dspy.MIPROv2(
        metric=metric,
        num_threads=1,
    )

    # Convert dataset dicts to DSPy Examples
    input_keys = list(signature_cls.input_fields.keys())  # type: ignore[attr-defined]
    trainset = [dspy.Example(**ex).with_inputs(*input_keys) for ex in dataset]

    # Run optimization
    try:
        optimized = optimizer.compile(
            module,
            trainset=trainset,
            max_bootstrapped_demos=3,
            max_labeled_demos=3,
        )
    except Exception as exc:
        print(f"[optimizer] MIPROv2 failed for {agent_name}: {exc}", file=sys.stderr)
        optimized = module  # fall back to unoptimized

    # Save the optimized module
    output_file = output_dir / f"{agent_name}.json"
    try:
        optimized.save(str(output_file))
    except Exception as exc:
        print(f"[optimizer] Failed to save module for {agent_name}: {exc}", file=sys.stderr)
        # Write a minimal JSON to signal optimization was attempted
        output_file.write_text(
            json.dumps({"agent": agent_name, "score": 0.0, "error": str(exc)}),
            encoding="utf-8",
        )

    optimized_at = datetime.now(timezone.utc).isoformat()

    # MIPROv2 sets `optimized.score = best_score` on the returned program
    # (mipro_optimizer_v2.py line 665, gated by track_stats=True which is the default).
    # `optimizer.best_score` does not exist — the score lives on the returned module.
    best_score = 0.0
    try:
        if hasattr(optimized, "score"):
            best_score = float(optimized.score)
    except Exception:
        pass

    result = {
        "agent": agent_name,
        "score": best_score,
        "optimized_at": optimized_at,
    }

    # Update the output file with result metadata
    try:
        existing = json.loads(output_file.read_text(encoding="utf-8")) if output_file.exists() else {}
        existing.update(result)
        output_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        pass

    return result


# ── optimize_all ────────────────────────────────────────────────────────────


def optimize_all(
    registry: list[AgentRegistryEntry],
    datasets: dict[str, list[dict]],
    output_dir: Path,
    backend: str = "anthropic",
) -> list[dict[str, Any]]:
    """Optimize all agents that have sufficient training data.

    Skips agents with fewer than 5 training examples.

    Args:
        registry: List of agents to consider for optimization.
        datasets: Mapping of agent name to list of training example dicts.
        output_dir: Directory to save optimized module JSON files.
        backend: LM backend to use — ``"anthropic"`` or ``"ollama"``.
            Passed through to :func:`optimize_agent`.
    """
    results: list[dict[str, Any]] = []

    for agent in registry:
        agent_dataset = datasets.get(agent.name, [])
        if len(agent_dataset) < 5:
            print(
                f"[optimizer] Skipping {agent.name}: only {len(agent_dataset)} examples (need >= 5)",
                file=sys.stderr,
            )
            continue

        print(f"[optimizer] Optimizing {agent.name} ({len(agent_dataset)} examples)...", file=sys.stderr)

        # All agents use ResearchAgentSig — build_dataset() always shapes examples
        # to ResearchAgentSig fields (question_text, project_context, constraints,
        # verdict, severity, evidence, mitigation, confidence).
        # DiagnoseAgentSig (symptoms, affected_files) is not currently populated
        # by build_dataset(); using it causes a silent field mismatch (R5.2).
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig
        sig = ResearchAgentSig

        result = optimize_agent(agent.name, sig, agent_dataset, output_dir, backend=backend)
        results.append(result)

    return results
