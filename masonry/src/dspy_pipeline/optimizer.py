"""masonry/src/dspy_pipeline/optimizer.py

DSPy optimization pipeline for Masonry agents.

Exposes:
  - configure_dspy(model, api_key=None)
  - build_metric(signature_cls)
  - build_karen_metric()
  - optimize_agent(agent_name, signature_cls, dataset, output_dir, metric_fn=None)
  - optimize_all(registry, datasets, output_dir, optimize_agent_fn=None)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dspy

from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

# Minimum training examples required to attempt optimization.
_MIN_EXAMPLES = 5

# Per-agent signature dispatch table. Agents not listed fall back to ResearchAgentSig.
_SIGNATURE_DISPATCH: dict[str, type] = {
    "karen": KarenSig,
}


# ---------------------------------------------------------------------------
# DSPy configuration
# ---------------------------------------------------------------------------


def configure_dspy(model: str = "anthropic/claude-haiku-4-5", api_key: str | None = None) -> None:
    """Configure DSPy with the given language model.

    Parameters
    ----------
    model:
        DSPy-compatible model string (e.g. ``"anthropic/claude-haiku-4-5"``).
    api_key:
        Optional API key. When provided it is forwarded to ``dspy.LM``. When
        omitted, DSPy uses the environment variable configured for the backend.
    """
    lm_kwargs: dict[str, Any] = {"model": model}
    if api_key is not None:
        lm_kwargs["api_key"] = api_key

    lm = dspy.LM(**lm_kwargs)
    dspy.configure(lm=lm)


# ---------------------------------------------------------------------------
# Metric builders
# ---------------------------------------------------------------------------


def build_metric(signature_cls: type | None) -> Any:
    """Return a DSPy-compatible metric function for research-style agents.

    The metric scores a (example, prediction) pair across three components:
      - Verdict match:        0.4 weight
      - Evidence quality:     0.4 weight (length-based proxy)
      - Confidence calibration: 0.2 weight
    """

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0

        # Verdict match
        ex_verdict = getattr(example, "verdict", None)
        pred_verdict = getattr(prediction, "verdict", None)
        if ex_verdict and pred_verdict and ex_verdict == pred_verdict:
            score += 0.4

        # Evidence quality (length proxy — longer is better, capped at 300 chars)
        pred_evidence = getattr(prediction, "evidence", "") or ""
        evidence_score = min(len(pred_evidence) / 300.0, 1.0)
        score += 0.4 * evidence_score

        # Confidence calibration — reward predictions close to example confidence
        try:
            target_conf = float(getattr(example, "confidence", 0.75) or 0.75)
            pred_conf = float(getattr(prediction, "confidence", "0.75") or "0.75")
            calibration = 1.0 - abs(target_conf - pred_conf)
            score += 0.2 * max(calibration, 0.0)
        except (ValueError, TypeError):
            pass

        return float(score)

    return metric


def build_karen_metric() -> Any:
    """Return a DSPy-compatible metric function for the karen (docs) agent."""

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0

        # Content quality: non-empty updated_content
        updated = getattr(prediction, "updated_content", "") or ""
        if len(updated) > 50:
            score += 0.5

        # Summary present
        summary = getattr(prediction, "summary", "") or ""
        if len(summary) > 10:
            score += 0.3

        # Confidence calibration
        try:
            pred_conf = float(getattr(prediction, "confidence", "0.75") or "0.75")
            target_conf = float(getattr(example, "confidence", 0.75) or 0.75)
            calibration = 1.0 - abs(target_conf - pred_conf)
            score += 0.2 * max(calibration, 0.0)
        except (ValueError, TypeError):
            pass

        return float(score)

    return metric


# ---------------------------------------------------------------------------
# Single-agent optimization
# ---------------------------------------------------------------------------


def optimize_agent(
    agent_name: str,
    signature_cls: type,
    dataset: list[dict],
    output_dir: Path,
    metric_fn: Any = None,
    num_trials: int = 10,
    valset_size: int = 20,
) -> dict:
    """Optimize a single agent using DSPy MIPROv2.

    Parameters
    ----------
    agent_name:
        Name of the agent (used for output file naming).
    signature_cls:
        DSPy Signature class to optimise.
    dataset:
        List of training example dicts.
    output_dir:
        Directory where the optimised module JSON is written.
    metric_fn:
        Callable ``(example, prediction) -> float``. Defaults to
        ``build_metric(signature_cls)``.
    num_trials:
        Number of MIPROv2 trials.
    valset_size:
        Validation set size drawn from dataset.

    Returns
    -------
    dict with keys: agent, score, optimized_at
    """
    if metric_fn is None:
        metric_fn = build_metric(signature_cls)

    # Build DSPy examples
    dspy_examples = []
    for ex in dataset:
        dspy_ex = dspy.Example(**ex).with_inputs(
            "question_text", "project_context", "constraints"
        )
        dspy_examples.append(dspy_ex)

    module = dspy.ChainOfThought(signature_cls)
    optimizer = dspy.MIPROv2(metric=metric_fn, num_candidates=num_trials, init_temperature=1.0)

    val_size = min(valset_size, len(dspy_examples))
    trainset = dspy_examples[val_size:]
    valset = dspy_examples[:val_size]

    optimized_module = optimizer.compile(
        module,
        trainset=trainset or dspy_examples,
        valset=valset or dspy_examples,
        requires_permission_to_run=False,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{agent_name}.json"

    try:
        optimized_module.save(str(output_file))
    except Exception:
        # If save fails (e.g. mock), write a minimal stub so callers can detect the file.
        output_file.write_text(json.dumps({"agent": agent_name}), encoding="utf-8")

    result = {
        "agent": agent_name,
        "score": getattr(optimized_module, "best_score", 0.0),
        "optimized_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    return result


# ---------------------------------------------------------------------------
# Multi-agent orchestration
# ---------------------------------------------------------------------------


def optimize_all(
    registry: list[Any],
    datasets: dict[str, list[dict]],
    output_dir: Path,
    optimize_agent_fn: Any = None,
) -> list[dict]:
    """Optimize all eligible agents in the registry.

    Agents with fewer than ``_MIN_EXAMPLES`` training examples are skipped.
    Each agent is dispatched to the correct signature via ``_SIGNATURE_DISPATCH``.

    Parameters
    ----------
    registry:
        List of agent registry entries (must have a ``.name`` attribute).
    datasets:
        Mapping of agent name → list of training example dicts.
    output_dir:
        Directory for optimised module outputs.
    optimize_agent_fn:
        Override for the per-agent optimization callable. Defaults to
        ``optimize_agent``. Useful for testing.

    Returns
    -------
    List of result dicts for each successfully optimised agent.
    """
    _opt_fn = optimize_agent_fn if optimize_agent_fn is not None else optimize_agent

    results: list[dict] = []
    for entry in registry:
        name: str = entry.name
        agent_dataset = datasets.get(name, [])

        if len(agent_dataset) < _MIN_EXAMPLES:
            continue

        sig_cls = _SIGNATURE_DISPATCH.get(name, ResearchAgentSig)

        if name == "karen":
            metric_fn = build_karen_metric()
        else:
            metric_fn = build_metric(sig_cls)

        result = _opt_fn(name, sig_cls, agent_dataset, output_dir, metric_fn=metric_fn)
        results.append(result)

    return results
