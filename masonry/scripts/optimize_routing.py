"""Routing description optimizer for Masonry agents.

Generates test queries for an agent, runs them through semantic routing,
scores accuracy, and optionally proposes improved descriptions.

Usage:
    python masonry/scripts/optimize_routing.py <agent-name> [--registry PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_REGISTRY = Path("masonry/agent_registry.yml")
_DEFAULT_SNAPSHOTS = Path("masonry/agent_snapshots")


def generate_test_queries(
    agent_name: str,
    description: str,
    capabilities: list[str],
) -> list[dict[str, Any]]:
    """Generate test queries for routing evaluation.

    Returns 10 should-match and 10 should-NOT-match queries
    derived from description and capabilities keywords.
    """
    queries: list[dict[str, Any]] = []

    # Positive queries — rephrasings of what the agent does
    cap_phrases = [c.strip() for c in capabilities if c.strip()]

    # From capabilities: direct requests
    for cap in cap_phrases[:5]:
        queries.append(
            {
                "query": f"I need help with {cap}",
                "expected_match": True,
            }
        )
    # From description: task-oriented rephrasings
    if description:
        queries.append(
            {
                "query": f"Can you {description.lower().rstrip('.')}?",
                "expected_match": True,
            }
        )
        queries.append(
            {
                "query": f"Help me {description.lower().rstrip('.')}",
                "expected_match": True,
            }
        )
    # Generic task patterns using agent name
    human_name = agent_name.replace("-", " ").replace("_", " ")
    queries.append(
        {
            "query": f"I need a {human_name}",
            "expected_match": True,
        }
    )
    queries.append(
        {
            "query": f"Run {human_name} on this codebase",
            "expected_match": True,
        }
    )
    queries.append(
        {
            "query": f"Activate {human_name} for this task",
            "expected_match": True,
        }
    )

    # Negative queries — clearly unrelated tasks
    unrelated = [
        "What's the weather like today?",
        "Help me write a poem about cats",
        "Calculate the square root of 144",
        "Translate this text to French",
        "What are the best restaurants nearby?",
        "Help me plan my vacation itinerary",
        "Fix my CSS flexbox layout issues",
        "Debug this Kubernetes deployment YAML",
        "Optimize my SQL database queries",
        "Write unit tests for my React component",
    ]
    for neg in unrelated[:10]:
        queries.append(
            {
                "query": neg,
                "expected_match": False,
            }
        )

    # Ensure at least 10 positive, 10 negative
    while len([q for q in queries if q["expected_match"]]) < 10:
        queries.append(
            {
                "query": f"Perform {human_name} analysis on the project",
                "expected_match": True,
            }
        )
    while len([q for q in queries if not q["expected_match"]]) < 10:
        queries.append(
            {
                "query": "Unrelated generic request",
                "expected_match": False,
            }
        )

    return queries[:20]


def score_routing_results(results: list[dict[str, Any]]) -> float:
    """Score routing accuracy from test results.

    Returns accuracy as a float 0.0-1.0.
    """
    if not results:
        return 0.0
    correct = sum(1 for r in results if r["expected_match"] == r["actual_match"])
    return correct / len(results)


def save_eval_results(
    agent_name: str,
    results: dict[str, Any],
    snapshots_dir: Path = _DEFAULT_SNAPSHOTS,
) -> Path:
    """Save evaluation results to agent_snapshots/{agent}/routing_eval.json."""
    output_dir = snapshots_dir / agent_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "routing_eval.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return output_path


def load_agent_from_registry(
    agent_name: str,
    registry_path: Path = _DEFAULT_REGISTRY,
) -> dict[str, Any] | None:
    """Load an agent's metadata from the registry."""
    if not registry_path.exists():
        return None
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    for entry in data.get("agents", []):
        if entry.get("name") == agent_name:
            return entry
    return None


def run_eval(
    agent_name: str,
    registry_path: Path = _DEFAULT_REGISTRY,
    snapshots_dir: Path = _DEFAULT_SNAPSHOTS,
    live_routing: bool = False,
) -> dict[str, Any]:
    """Run a full routing evaluation for an agent.

    If live_routing=True, uses the actual semantic router (requires Ollama).
    Otherwise, runs in dry-run mode with generated queries only.
    """
    agent = load_agent_from_registry(agent_name, registry_path)
    if not agent:
        return {"error": f"Agent '{agent_name}' not found in registry"}

    description = agent.get("description", "")
    capabilities = agent.get("capabilities", [])

    queries = generate_test_queries(agent_name, description, capabilities)

    results_list: list[dict[str, Any]] = []

    if live_routing:
        # Import and use the actual semantic router
        from masonry.src.routing.semantic import route_semantic
        from masonry.src.schemas.payloads import AgentRegistryEntry

        # Load full registry for routing context
        reg_data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        registry_entries = []
        for entry in reg_data.get("agents", []):
            try:
                registry_entries.append(AgentRegistryEntry(**entry))
            except Exception:
                continue

        for q in queries:
            decision = route_semantic(q["query"], registry_entries)
            actual_match = decision is not None and decision.target_agent == agent_name
            results_list.append(
                {
                    "query": q["query"],
                    "expected_match": q["expected_match"],
                    "actual_match": actual_match,
                    "routed_to": decision.target_agent if decision else None,
                    "confidence": decision.confidence if decision else 0.0,
                }
            )
    else:
        # Dry-run: just output queries without routing
        for q in queries:
            results_list.append(
                {
                    "query": q["query"],
                    "expected_match": q["expected_match"],
                    "actual_match": False,  # placeholder
                }
            )

    accuracy = score_routing_results(results_list) if live_routing else None

    eval_results = {
        "agent": agent_name,
        "description": description,
        "capabilities": capabilities,
        "accuracy": accuracy,
        "queries": len(results_list),
        "results": results_list,
        "live": live_routing,
    }

    save_eval_results(agent_name, eval_results, snapshots_dir)
    return eval_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate routing accuracy for an agent."
    )
    parser.add_argument("agent_name", help="Agent name to evaluate")
    parser.add_argument(
        "--registry", default=str(_DEFAULT_REGISTRY), help="Registry path"
    )
    parser.add_argument(
        "--snapshots", default=str(_DEFAULT_SNAPSHOTS), help="Snapshots dir"
    )
    parser.add_argument(
        "--live", action="store_true", help="Run live routing via Ollama"
    )
    args = parser.parse_args()

    result = run_eval(
        args.agent_name,
        Path(args.registry),
        Path(args.snapshots),
        live_routing=args.live,
    )

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if result.get("live"):
        print(f"Agent: {result['agent']}")
        print(f"Accuracy: {result['accuracy']:.0%} ({result['queries']} queries)")
    else:
        print(f"Agent: {result['agent']}")
        print(f"Generated {result['queries']} test queries (dry-run, no live routing)")
        print(
            f"Results saved to {_DEFAULT_SNAPSHOTS}/{result['agent']}/routing_eval.json"
        )


if __name__ == "__main__":
    main()
