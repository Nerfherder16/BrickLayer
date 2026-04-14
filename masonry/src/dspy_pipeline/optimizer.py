"""DSPy optimizer — optimizes agent prompts using scored training data."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import dspy

from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig
from masonry.src.schemas.payloads import AgentRegistryEntry

_DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"
_OLLAMA_MODEL = "ollama_chat/qwen3:14b"
_MIN_EXAMPLES = 5

# Per-agent signature dispatch table — agents not listed fall back to ResearchAgentSig
_SIG_DISPATCH: dict[str, type] = {
    "karen": KarenSig,
}

# Per-agent metric dispatch — agents not listed use build_metric(ResearchAgentSig)
_METRIC_DISPATCH: dict[str, Callable] = {}


def configure_dspy(api_key: Optional[str] = None, backend: str = "anthropic") -> None:
    """Configure DSPy with the appropriate LM backend."""
    kwargs: dict[str, Any] = {}
    if api_key is not None:
        kwargs["api_key"] = api_key
    model = _OLLAMA_MODEL if backend == "ollama" else _DEFAULT_MODEL
    lm = dspy.LM(model, **kwargs)
    dspy.configure(lm=lm)


def build_metric(sig_cls: Any) -> Callable:
    """Return a metric function appropriate for the given signature class.

    Scoring breakdown (weights sum to 1.0):
      - Verdict match:         0.4
      - Evidence quality:      0.4  (based on evidence length >= 100 chars)
      - Confidence calibration: 0.2 (how close prediction confidence is to example confidence)
    """
    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        try:
            # Verdict match (0.4 weight)
            verdict = getattr(prediction, "verdict", "").strip().upper()
            expected = getattr(example, "verdict", "").strip().upper()
            verdict_score = 0.4 if verdict == expected else 0.0

            # Evidence quality (0.4 weight) — length-based, target 100+ chars
            evidence = getattr(prediction, "evidence", "") or ""
            ev_len = len(evidence)
            ev_score = min(ev_len / 100.0, 1.0) * 0.4

            # Confidence calibration (0.2 weight) — closeness to example confidence
            try:
                pred_conf = float(getattr(prediction, "confidence", 0.0))
                ex_conf = float(getattr(example, "confidence", 0.75))
                cal_score = max(0.0, 1.0 - abs(pred_conf - ex_conf)) * 0.2
            except (TypeError, ValueError):
                cal_score = 0.0

            return verdict_score + ev_score + cal_score
        except Exception:
            return 0.0
    return metric


def _build_karen_metric() -> Callable:
    """Metric for karen — checks output and summary are non-empty."""
    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        try:
            has_output = bool(getattr(prediction, "output", "").strip())
            has_summary = bool(getattr(prediction, "summary", "").strip())
            return 1.0 if (has_output and has_summary) else 0.0
        except Exception:
            return 0.0
    return metric


def optimize_agent(
    agent_name: str,
    signature_cls: type,
    dataset: list[dict],
    output_dir: Path,
    metric_fn: Optional[Callable] = None,
    **kwargs: Any,
) -> dict:
    """Optimize a single agent using DSPy MIPROv2."""
    metric = metric_fn or build_metric(signature_cls)

    try:
        trainset = [dspy.Example(**ex).with_inputs(*signature_cls.input_fields()) for ex in dataset]
    except Exception:
        trainset = dataset  # fallback — let optimizer handle it

    optimizer = dspy.MIPROv2(metric=metric, auto="light")
    program = dspy.Predict(signature_cls)

    save_path = None
    try:
        optimized = optimizer.compile(program, trainset=trainset)
        score = getattr(optimized, "_score", 0.0)
        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / f"{agent_name}.json"
        optimized.save(str(save_path))
    except Exception:
        score = 0.0
        output_dir.mkdir(parents=True, exist_ok=True)

    return {
        "agent": agent_name,
        "score": score,
        "optimized_at": datetime.now(timezone.utc).isoformat(),
        "saved_to": str(save_path) if save_path else None,
    }


def optimize_all(
    registry: list[AgentRegistryEntry],
    datasets: dict[str, list[dict]],
    output_dir: Path,
) -> list[dict]:
    """Optimize all agents in the registry that have sufficient training data."""
    results = []

    for entry in registry:
        name = entry.name
        data = datasets.get(name, [])

        if len(data) < _MIN_EXAMPLES:
            continue

        sig_cls = _SIG_DISPATCH.get(name, ResearchAgentSig)

        if name in _METRIC_DISPATCH:
            metric_fn = _METRIC_DISPATCH[name]
        elif name == "karen":
            metric_fn = _build_karen_metric()
        else:
            metric_fn = build_metric(sig_cls)

        result = optimize_agent(
            name,
            sig_cls,
            data,
            output_dir,
            metric_fn=metric_fn,
        )
        results.append(result)

    return results
