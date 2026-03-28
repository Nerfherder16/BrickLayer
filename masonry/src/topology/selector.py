"""
Adaptive topology selector — picks the right swarm shape for a task list.

Topologies:
  parallel      — all tasks independent, dispatch simultaneously (default)
  pipeline      — tasks are a strict sequence (output of N feeds N+1)
  mesh          — tasks need peer review between workers (quality-critical)
  hierarchical  — large task list (>8) with coordinator + worker groups
"""

from __future__ import annotations

import json
import sys

_MESH_KEYWORDS = frozenset({"review", "verify", "audit", "security"})


def select_topology(tasks: list[dict]) -> tuple[str, str]:
    """Select optimal swarm topology based on task characteristics.

    Args:
        tasks: list of dicts with keys id, description, depends_on (list), status

    Returns:
        Tuple of (topology, reason) where topology is one of:
        "parallel" | "pipeline" | "mesh" | "hierarchical"
    """
    if not tasks:
        return "parallel", "no tasks — defaulting to parallel"

    total = len(tasks)

    # Count tasks that have dependencies
    tasks_with_deps = sum(
        1 for t in tasks if t.get("depends_on") and len(t["depends_on"]) > 0
    )
    dep_ratio = tasks_with_deps / total

    # Rule 1: >50% of tasks have deps → pipeline
    if dep_ratio > 0.5:
        return (
            "pipeline",
            f"{tasks_with_deps}/{total} tasks have dependencies (>{50}%) — strict sequence required",
        )

    # Rule 2: >8 tasks → hierarchical
    if total > 8:
        return (
            "hierarchical",
            f"{total} tasks exceeds threshold of 8 — coordinator + worker groups for manageability",
        )

    # Rule 3: any task description contains quality-review keywords → mesh
    for task in tasks:
        desc = (task.get("description") or "").lower()
        if any(kw in desc for kw in _MESH_KEYWORDS):
            matched = next(kw for kw in _MESH_KEYWORDS if kw in desc)
            return (
                "mesh",
                f'task "{task.get("description", "")[:60]}" contains quality keyword "{matched}" — peer review topology',
            )

    # Default: fully parallel
    return (
        "parallel",
        f"all {total} tasks are independent with no quality-review keywords — parallel dispatch",
    )


def _cli_main() -> None:
    """CLI entry point: reads JSON from argv[1], prints topology JSON."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: selector.py '<json>'"}), file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON: {exc}"}), file=sys.stderr)
        sys.exit(1)

    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        print(json.dumps({"error": "'tasks' must be a list"}), file=sys.stderr)
        sys.exit(1)

    topology, reason = select_topology(tasks)
    print(json.dumps({"topology": topology, "reason": reason}))


if __name__ == "__main__":
    _cli_main()
