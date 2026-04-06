"""Registry loader — reads agent_registry.yml and filters by mode."""
from __future__ import annotations

from pathlib import Path

import yaml

from masonry.src.schemas.payloads import AgentRegistryEntry


def load_registry(registry_path: Path) -> list[AgentRegistryEntry]:
    """Load agent_registry.yml and return a list of AgentRegistryEntry objects."""
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    agents_raw = data.get("agents", data) if isinstance(data, dict) else data
    entries = []
    for item in agents_raw or []:
        if not isinstance(item, dict):
            continue
        entries.append(
            AgentRegistryEntry(
                name=item.get("name", ""),
                file=item.get("file", ""),
                description=item.get("description", ""),
                capabilities=item.get("capabilities") or [],
                modes=item.get("modes") or [],
                tier=item.get("tier", "standard"),
                routing_keywords=item.get("routing_keywords") or [],
                model=item.get("model"),
            )
        )
    return entries


def get_agents_for_mode(
    registry: list[AgentRegistryEntry],
    mode: str,
) -> list[AgentRegistryEntry]:
    """Return agents whose modes list includes the given mode string."""
    return [entry for entry in registry if mode in entry.modes]
