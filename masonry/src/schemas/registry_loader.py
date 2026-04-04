"""Registry loader — reads agent_registry.yml and filters by mode."""
from __future__ import annotations

from masonry.src.schemas.payloads import AgentRegistryEntry


def get_agents_for_mode(
    registry: list[AgentRegistryEntry],
    mode: str,
) -> list[AgentRegistryEntry]:
    """Return agents whose modes list includes the given mode string."""
    return [entry for entry in registry if mode in entry.modes]
