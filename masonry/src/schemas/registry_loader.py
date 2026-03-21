"""Registry loader — parses agent_registry.yml into AgentRegistryEntry models.

Provides helpers for mode-based and name-based agent lookup.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from masonry.src.schemas.payloads import AgentRegistryEntry


def load_registry(path: Path) -> list[AgentRegistryEntry]:
    """Parse a YAML registry file into validated AgentRegistryEntry objects.

    Entries that fail Pydantic validation are skipped with a warning logged to
    stderr.  If the file does not exist or cannot be parsed, an empty list is
    returned — never raises.
    """
    if yaml is None:
        print("[registry_loader] PyYAML is not installed.", file=sys.stderr)
        return []

    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError):
        return []

    try:
        data: dict[str, Any] = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        print(f"[registry_loader] Failed to parse YAML: {exc}", file=sys.stderr)
        return []

    raw_agents: list[dict[str, Any]] = data.get("agents") or []
    entries: list[AgentRegistryEntry] = []

    for raw_entry in raw_agents:
        try:
            entry = AgentRegistryEntry.model_validate(raw_entry)
            entries.append(entry)
        except ValidationError as exc:
            name = raw_entry.get("name", "<unknown>")
            print(
                f"[registry_loader] Skipping invalid agent '{name}': {exc}",
                file=sys.stderr,
            )

    return entries


def get_agents_for_mode(
    registry: list[AgentRegistryEntry], mode: str
) -> list[AgentRegistryEntry]:
    """Return all agents whose modes list includes *mode*."""
    return [a for a in registry if mode in a.modes]


def get_agent_by_name(
    registry: list[AgentRegistryEntry], name: str
) -> AgentRegistryEntry | None:
    """Return the first agent with an exact name match, or None."""
    for agent in registry:
        if agent.name == name:
            return agent
    return None
