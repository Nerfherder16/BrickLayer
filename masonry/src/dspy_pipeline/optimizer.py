"""DSPy MIPROv2 optimization pipeline for Masonry agents.

Optimizes agent prompts using campaign findings as training data.
Uses a heuristic metric (no LLM judge required) to keep costs low.
"""

from __future__ import annotations

import json
import os
import re
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
    - evidence_quality (0.4): len > 300 AND (has_numbers OR threshold_language) = 1.0, else 0.5
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

        # Evidence quality (0.4 weight) — Phase 17 change #1 (F25.2)
        # Content signal check: length > 300 chars AND (contains numbers OR threshold language)
        # Rationale: replaces the old binary length > 100 check which was satisfied by verbose filler.
        # Qualitative findings without quantitative evidence receive 0.2 partial credit.
        _THRESHOLD_KEYWORDS = ("threshold", "baseline", "%", "ms", "pts", "seconds")
        try:
            evidence = str(getattr(prediction, "evidence", "") or "")
            has_numbers = bool(re.search(r"\d+\.?\d*", evidence))
            has_threshold_language = any(kw in evidence.lower() for kw in _THRESHOLD_KEYWORDS)
            if len(evidence) > 300 and (has_numbers or has_threshold_language):
                score += 0.4
            else:
                score += 0.2  # partial credit for short or purely qualitative evidence
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


def build_karen_metric() -> Any:
    """Build heuristic scoring metric for KarenSig (ops-domain documentation agent).

    Matches the hook-defined KarenSig output schema: quality_score, action,
    doc_updates, changelog_entry.

    Components:
    - quality_score_proximity (0.5): |predicted_score - actual_score| ≤ 0.1 = 0.5, else 0.25
    - action_match (0.3): predicted action matches expected action
    - changelog_quality (0.2): non-empty changelog_entry when action != "skipped"

    Returns a callable(example, prediction, trace) -> float.
    """

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0

        # quality_score proximity (0.5 weight) — F27.1 fix
        # Separate parse-failure path from proximity check:
        # - if prediction quality_score is non-parseable (empty/non-numeric): 0.25 partial credit
        # - if parseable: apply proximity check (|pred - actual| <= 0.1 -> 0.5, else 0.25)
        # This prevents empty-string predictions from accidentally triggering the proximity
        # bonus via the `or "1.0"` fallback (V26.1 calibration gap).
        try:
            ex_qs = str(getattr(example, "quality_score", "1.0") or "1.0")
            pred_qs_raw = str(getattr(prediction, "quality_score", "") or "")
            m = re.search(r"\d+\.?\d*", pred_qs_raw)
            ex_val = float(ex_qs)
            if m:
                pred_val = float(m.group())
                if abs(ex_val - pred_val) <= 0.1:
                    score += 0.5
                else:
                    score += 0.25  # partial credit for reasonable but off estimates
            else:
                score += 0.25  # partial credit — prediction quality_score not parseable
        except Exception:
            score += 0.25  # default partial credit on example parse failure

        # action match (0.3 weight)
        try:
            ex_action = str(getattr(example, "action", "") or "").lower().strip()
            pred_action = str(getattr(prediction, "action", "") or "").lower().strip()
            if ex_action and pred_action and ex_action == pred_action:
                score += 0.3
            elif ex_action and pred_action and (
                (ex_action in ("updated", "created")) == (pred_action in ("updated", "created"))
            ):
                score += 0.15  # partial credit for getting the write/no-write direction right
        except Exception:
            pass

        # changelog_entry quality (0.2 weight)
        try:
            entry = str(getattr(prediction, "changelog_entry", "") or "")
            ex_action = str(getattr(example, "action", "skipped") or "skipped").lower()
            if ex_action != "skipped" and len(entry) > 10:
                score += 0.2
            elif ex_action == "skipped":
                score += 0.2  # no entry needed when action is skipped
        except Exception:
            pass

        return score

    return metric


# ── configure_dspy ──────────────────────────────────────────────────────────


def configure_dspy(
    model: str | None = None,
    backend: str = "anthropic",
    api_key: str | None = None,
) -> None:
    """Configure DSPy with the specified LM backend.

    Args:
        model: Model name to use. Defaults to ``qwen3:14b`` for Ollama and
            ``claude-sonnet-4-6`` for Anthropic when not specified.
        backend: Either ``"anthropic"`` (uses ANTHROPIC_API_KEY or Claude Max
            session credentials) or ``"ollama"`` (uses local Ollama at
            http://192.168.50.62:11434).
        api_key: Optional API key passed directly to ``dspy.LM`` (via LiteLLM).
            When ``None`` and ``ANTHROPIC_API_KEY`` is not set, falls back to
            litellm's ``claude/`` provider which uses Claude Code session
            credentials (Claude Max subscriptions).
    """
    if backend == "ollama":
        effective_model = model or "qwen3:14b"
        ollama_kwargs: dict[str, Any] = {
            "api_base": os.environ.get("OLLAMA_URL", "http://100.70.195.84:11434"),
            "max_tokens": 4096,
        }
        if api_key is not None:
            ollama_kwargs["api_key"] = api_key
        lm = dspy.LM(f"ollama_chat/{effective_model}", **ollama_kwargs)
    else:
        effective_model = model or "claude-sonnet-4-6"
        # Prefer explicit api_key, then env var, then Claude Max session (claude/ provider).
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if resolved_key:
            lm = dspy.LM(f"anthropic/{effective_model}", api_key=resolved_key)
        else:
            # No API key — use litellm's claude/ provider which routes through
            # the active Claude Code session (Claude Max subscriptions).
            lm = dspy.LM(f"claude/{effective_model}")
    dspy.configure(lm=lm)


# ── optimize_agent ──────────────────────────────────────────────────────────


def optimize_agent(
    agent_name: str,
    signature_cls: type,
    dataset: list[dict],
    output_dir: Path,
    backend: str = "anthropic",
    num_trials: int = 10,
    valset_size: int = 100,
    metric_fn: Any = None,
    optimizer_mode: str = "bootstrap",
) -> dict[str, Any]:
    """Optimize a single agent's prompt using BootstrapFewShot or MIPROv2.

    Args:
        agent_name: Name of the agent to optimize.
        signature_cls: DSPy Signature class defining the I/O contract.
        dataset: List of training examples (dicts matching signature fields).
        output_dir: Directory to save the optimized module JSON.
        backend: LM backend to use — ``"anthropic"`` or ``"ollama"``.
            Passed through to :func:`configure_dspy` when called by the caller.
        num_trials: Number of Bayesian optimization trials (MIPROv2 only, default: 10).
        valset_size: Number of examples to use as the validation set (default: 100).
            The last ``valset_size`` examples are held out; the rest become trainset.
        metric_fn: Optional custom metric callable. When ``None``, defaults to
            :func:`build_metric` for the given signature. Pass
            :func:`build_karen_metric` when optimizing the karen agent.
        optimizer_mode: ``"bootstrap"`` (default) uses BootstrapFewShot — fast,
            no LLM instruction generation, selects best few-shot examples.
            ``"mipro"`` uses MIPROv2 — full Bayesian instruction search, slower.

    Returns:
        Dict with agent, score, and optimized_at fields.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the module
    module = dspy.ChainOfThought(signature_cls)
    metric = metric_fn if metric_fn is not None else build_metric(signature_cls)

    # Convert dataset dicts to DSPy Examples first so we know actual sizes.
    input_keys = list(signature_cls.input_fields.keys())  # type: ignore[attr-defined]
    all_examples = [dspy.Example(**ex).with_inputs(*input_keys) for ex in dataset]

    # Split into train / val — DSPy 3.x takes valset as an explicit list.
    # Cap valset at 25% of dataset to keep enough training examples.
    actual_valset_size = min(valset_size, max(1, len(all_examples) // 4))
    trainset = all_examples[:-actual_valset_size] if actual_valset_size < len(all_examples) else all_examples
    valset = all_examples[-actual_valset_size:]

    # Run optimization
    if optimizer_mode == "mipro":
        # MIPROv2: full Bayesian instruction + few-shot search.
        # DSPy 3.x: auto=None requires num_candidates in the constructor.
        optimizer = dspy.MIPROv2(
            metric=metric,
            num_threads=1,
            auto=None,
            num_candidates=num_trials,
        )

        # minibatch_size goes to compile(), not the constructor.
        # Cap it to len(valset) — MIPROv2 raises if it exceeds valset size.
        _minibatch_size = min(35, len(valset))

        try:
            optimized = optimizer.compile(
                module,
                trainset=trainset,
                valset=valset,
                max_bootstrapped_demos=3,
                max_labeled_demos=3,
                num_trials=num_trials,
                minibatch_size=_minibatch_size,
                # data_aware_proposer does re.search on bootstrap predictions which
                # can be None when Ollama omits a field — disable to avoid TypeError.
                data_aware_proposer=False,
            )
        except Exception as exc:
            print(f"[optimizer] MIPROv2 failed for {agent_name}: {exc}", file=sys.stderr)
            optimized = module  # fall back to unoptimized
    else:
        # BootstrapFewShot: fast few-shot selection, no LLM instruction generation.
        optimizer = dspy.BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=4,
            max_labeled_demos=4,
        )
        try:
            optimized = optimizer.compile(module, trainset=trainset)
        except Exception as exc:
            print(f"[optimizer] BootstrapFewShot failed for {agent_name}: {exc}", file=sys.stderr)
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
    optimizer_mode: str = "bootstrap",
) -> list[dict[str, Any]]:
    """Optimize all agents that have sufficient training data.

    Skips agents with fewer than 5 training examples.

    Args:
        registry: List of agents to consider for optimization.
        datasets: Mapping of agent name to list of training example dicts.
        output_dir: Directory to save optimized module JSON files.
        backend: LM backend to use — ``"anthropic"`` or ``"ollama"``.
            Passed through to :func:`optimize_agent`.
        optimizer_mode: ``"bootstrap"`` (default) or ``"mipro"``.
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

        # Dispatch table — add new agent signatures here.
        # Agents not listed fall back to ResearchAgentSig + build_metric (the
        # general research-finding schema).  karen uses KarenSig because its
        # training examples are shaped around commit/changelog fields rather than
        # question/verdict fields.
        from masonry.src.dspy_pipeline.signatures import KarenSig, ResearchAgentSig

        _AGENT_SIGNATURES: dict[str, tuple[type, Any]] = {
            "karen": (KarenSig, build_karen_metric),
        }
        _DEFAULT_SIG = (ResearchAgentSig, build_metric)

        sig_class, metric_fn = _AGENT_SIGNATURES.get(agent.name, _DEFAULT_SIG)
        sig = sig_class
        metric = metric_fn(sig_class) if metric_fn is build_metric else metric_fn()

        result = optimize_agent(agent.name, sig, agent_dataset, output_dir, backend=backend, metric_fn=metric, optimizer_mode=optimizer_mode)
        results.append(result)

    return results
