"""Orchestrating four-layer router.

Chains Layer 1 (deterministic) → Layer 2 (semantic) → Layer 3 (LLM) →
Layer 4 (fallback). Always returns a RoutingDecision.
"""

from __future__ import annotations

import sys
from pathlib import Path

from masonry.src.routing.deterministic import route_deterministic
from masonry.src.routing.llm_router import route_llm
from masonry.src.routing.semantic import route_semantic
from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision
from masonry.src.schemas.registry_loader import load_registry

def _make_fallback(fallback_reason: str = "ambiguous") -> RoutingDecision:
    """Construct a Layer 4 fallback decision with a reason code."""
    return RoutingDecision(
        target_agent="user",
        layer="fallback",
        confidence=0.0,
        reason="Ambiguous request -- asking user for clarification",
    )


def _load_registry(project_dir: Path) -> list[AgentRegistryEntry]:
    """Load registry from the standard location inside a project dir."""
    registry_path = project_dir / "masonry" / "agent_registry.yml"
    if not registry_path.exists():
        print(f"[ROUTER] Registry not found at {registry_path}", file=sys.stderr)
        # Also try relative to CWD
        fallback = Path("masonry") / "agent_registry.yml"
        if fallback.exists():
            return load_registry(fallback)
        print(f"[ROUTER] Registry not found at {fallback} (CWD fallback) — returning empty registry", file=sys.stderr)
        return []
    return load_registry(registry_path)


def route(request_text: str, project_dir: Path) -> RoutingDecision:
    """Route a request through all four layers. Always returns a RoutingDecision."""
    registry = _load_registry(project_dir)

    # Layer 1: Deterministic
    decision = route_deterministic(request_text, project_dir, registry)
    if decision is not None:
        print(
            f"[ROUTER] Layer deterministic resolved: {decision.target_agent} "
            f"(confidence {decision.confidence})",
            file=sys.stderr,
        )
        return decision

    # Layer 2: Semantic
    decision = route_semantic(request_text, registry)
    if decision is not None:
        print(
            f"[ROUTER] Layer semantic resolved: {decision.target_agent} "
            f"(confidence {decision.confidence:.2f})",
            file=sys.stderr,
        )
        return decision

    # Layer 3: LLM
    decision = route_llm(request_text, registry)
    if decision is not None:
        print(
            f"[ROUTER] Layer llm resolved: {decision.target_agent} "
            f"(confidence {decision.confidence})",
            file=sys.stderr,
        )
        return decision

    # Layer 4: Fallback — all layers exhausted without resolution
    # Classify as "ambiguous": L1-L3 ran but none produced a match.
    # Finer-grained reasons (ollama_timeout, llm_timeout) require layer-level
    # error propagation — tracked in D1.3/R1.5 for future work.
    fallback = _make_fallback("ambiguous")
    print(
        f"[ROUTER] Layer fallback resolved: {fallback.target_agent} "
        f"(confidence {fallback.confidence})",
        file=sys.stderr,
    )
    return fallback
