"""Registry loader — reads agent_registry.yml and filters by mode."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import yaml

from masonry.src.schemas.payloads import AgentRegistryEntry

_KNOWN_FIELDS = {
    "name", "file", "description", "capabilities", "modes", "tier",
    "routing_keywords", "model", "input_schema", "output_schema", "optimized_prompt",
}


def load_registry(registry_path: Path) -> list[AgentRegistryEntry]:
    """Load agent_registry.yml and return a list of AgentRegistryEntry objects.

    Entries that fail Pydantic validation are skipped with a warning to stderr.
    """
    if not registry_path.exists():
        return []

    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    agents_raw = data.get("agents", data) if isinstance(data, dict) else data
    entries: list[AgentRegistryEntry] = []

    for item in agents_raw or []:
        if not isinstance(item, dict):
            continue
        filtered = {k: v for k, v in item.items() if k in _KNOWN_FIELDS}
        try:
            entries.append(AgentRegistryEntry.model_validate(filtered))
        except Exception as exc:
            print(
                f"WARNING: skipping invalid registry entry "
                f"{item.get('name', '<unnamed>')!r}: {exc}",
                file=sys.stderr,
            )

    return entries


def get_agents_for_mode(
    registry: list[AgentRegistryEntry],
    mode: str,
) -> list[AgentRegistryEntry]:
    """Return agents whose modes list includes the given mode string."""
    return [entry for entry in registry if mode in entry.modes]


def get_agent_by_name(
    registry: list[AgentRegistryEntry],
    name: str,
) -> Optional[AgentRegistryEntry]:
    """Return the first agent with an exact case-sensitive name match, or None."""
    for entry in registry:
        if entry.name == name:
            return entry
    return None
