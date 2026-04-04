"""bl/tmux/wave.py — Batch spawn and collect for agent waves."""

from __future__ import annotations

import subprocess
from bl.tmux.core import AgentResult, SpawnResult, spawn_agent, wait_for_agent
from bl.tmux.helpers import in_tmux


def spawn_wave(
    agents: list[dict[str, object]],
    max_concurrency: int | None = None,
) -> list[SpawnResult]:
    """Spawn a batch of agents. Returns list of SpawnResults for collection.

    Each dict in agents must have 'agent_name' and 'prompt'; other keys are
    forwarded as kwargs to spawn_agent.
    """
    batch = agents[:max_concurrency] if max_concurrency else agents

    spawns: list[SpawnResult] = []
    for spec in batch:
        spawns.append(spawn_agent(**spec))  # pyright: ignore[reportArgumentType]

    if in_tmux() and spawns:
        try:
            _ = subprocess.run(
                ["tmux", "select-layout", "tiled"],
                capture_output=True,
                timeout=5,
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

    return spawns


def collect_wave(
    spawns: list[SpawnResult],
    *,
    timeout: int = 600,
) -> list[AgentResult]:
    """Wait for all spawns and return their results."""
    return [wait_for_agent(s, timeout=timeout) for s in spawns]
