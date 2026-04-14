"""masonry/mcp_server/tools/routing.py — Routing, onboarding, and registry tool implementations."""

from __future__ import annotations

import os
from pathlib import Path

from masonry.mcp_server.js_engine import _call_js_engine, _REPO_ROOT


def _python_route_fallback(request_text: str, project_dir: Path) -> dict:
    """Python fallback for masonry_route when JS engine is unavailable."""
    try:
        from masonry.src.routing.router import route  # noqa: PLC0415

        decision = route(request_text, project_dir)
        return decision.model_dump()
    except Exception as exc:
        return {
            "error": str(exc),
            "target_agent": "user",
            "layer": "fallback",
            "confidence": 0.0,
            "reason": f"Router unavailable: {str(exc)[:80]}",
        }


def _normalize_route_result(result: dict) -> dict:
    """Normalize routing result to canonical format with target_agent/layer/confidence keys."""
    if "target_agent" in result:
        return result
    # JS engine may return {agent, layer, confidence, note} — normalize to canonical
    normalized = dict(result)
    if "agent" in normalized and "target_agent" not in normalized:
        normalized["target_agent"] = normalized.pop("agent")
    # Normalize layer codes like "L1", "L1a", "L2", "L3" to descriptive names
    layer = normalized.get("layer", "")
    layer_map = {
        "L1": "deterministic", "L1a": "deterministic",
        "L2": "semantic",
        "L3": "llm",
        "L4": "fallback",
    }
    if layer in layer_map:
        normalized["layer"] = layer_map[layer]
    # Ensure confidence is present
    if "confidence" not in normalized:
        normalized["confidence"] = 1.0 if normalized.get("layer") == "deterministic" else 0.0
    return normalized


def _tool_masonry_route(args: dict) -> dict:
    """Route a request to the appropriate Masonry agent using the four-layer router."""
    request_text = args.get("request_text", "")
    project_dir = Path(args.get("project_dir", os.getcwd()))

    if not request_text:
        return {"error": "request_text is required"}

    # Try JS engine first (15s — Ollama semantic layer may be slow)
    js_args = ["--prompt", request_text]
    js_result = _call_js_engine("route.js", js_args, timeout=15)
    if js_result is not None:
        return _normalize_route_result(js_result)

    return _python_route_fallback(request_text, project_dir)


def _tool_masonry_onboard(args: dict) -> dict:
    """Detect and register new agent .md files not yet in the registry."""
    agents_dirs_raw = args.get("agents_dirs", [])
    registry_path_str = args.get(
        "registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml")
    )

    if isinstance(agents_dirs_raw, str):
        agents_dirs_raw = [agents_dirs_raw]

    agents_dirs = [Path(d) for d in agents_dirs_raw] if agents_dirs_raw else [
        Path.home() / ".claude" / "agents",
        Path("agents"),
    ]
    registry_path = Path(registry_path_str)
    dspy_output_dir = Path(args.get(
        "dspy_output_dir",
        str(_REPO_ROOT / "masonry" / "src" / "dspy_pipeline" / "generated"),
    ))

    try:
        from masonry.scripts.onboard_agent import onboard  # noqa: PLC0415

        result = onboard(agents_dirs, registry_path, dspy_output_dir)
        names = result.get("names", [])
        return {
            "onboarded": names,
            "count": result.get("added", len(names)),
            "updated": result.get("updated", 0),
            "stale": result.get("stale", 0),
            "warnings": result.get("warnings", []),
        }
    except Exception as exc:
        return {"error": str(exc), "onboarded": [], "count": 0}


def _tool_masonry_registry_list(args: dict) -> dict:
    """List agents from the Masonry agent registry YAML."""
    tier_filter = args.get("tier")
    mode_filter = args.get("mode")

    # Python fallback
    registry_path = Path(
        args.get("registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml"))
    )
    try:
        from masonry.src.schemas.registry_loader import (  # noqa: PLC0415
            load_registry,
            get_agents_for_mode,
        )

        agents = load_registry(registry_path)

        if mode_filter:
            agents = get_agents_for_mode(agents, mode_filter)
        if tier_filter:
            agents = [a for a in agents if a.tier == tier_filter]

        return {
            "agents": [
                {k: v for k, v in a.model_dump().items() if v is not None}
                for a in agents
            ],
            "count": len(agents),
        }
    except Exception as exc:
        return {"error": str(exc), "agents": [], "count": 0}
