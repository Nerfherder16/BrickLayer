"""Backfill the Masonry agent registry from agent .md files on disk.

Adds agents whose .md files exist but are missing from the registry.
Removes registry entries whose .md files no longer exist (phantom cleanup).

CLI usage:
    python masonry/scripts/backfill_registry.py [--agents-dir PATH ...] \
        [--registry PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SKIP_STEMS = frozenset({"SCHEMA", "AGENTS", "README", "INDEX", "AUDIT_REPORT"})

_DEFAULT_AGENTS_DIRS: list[Path] = [
    Path.home() / ".claude" / "agents",
    Path(".claude") / "agents",
]
_DEFAULT_REGISTRY = Path("masonry/agent_registry.yml")


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a .md file.

    Args:
        path: Path to the .md file.

    Returns:
        Dict of frontmatter fields (empty dict if none found).
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        fm = yaml.safe_load(parts[1]) or {}
        return fm if isinstance(fm, dict) else {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------


def _load_registry(registry_path: Path) -> dict[str, Any]:
    """Load the registry YAML file, returning a dict with 'agents' list."""
    if not registry_path.exists():
        return {"version": 1, "agents": []}
    try:
        raw = registry_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return {"version": 1, "agents": []}
        if "agents" not in data:
            data["agents"] = []
        if "version" not in data:
            data["version"] = 1
        return data
    except yaml.YAMLError:
        return {"version": 1, "agents": []}


def _save_registry(registry_path: Path, data: dict[str, Any]) -> None:
    """Write the registry dict back to YAML."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Agent file discovery
# ---------------------------------------------------------------------------


def _collect_agent_files(agents_dirs: list[Path]) -> dict[str, Path]:
    """Return a mapping of agent stem -> Path for all valid .md files.

    Args:
        agents_dirs: Directories to scan.

    Returns:
        Dict mapping agent name (stem) to its file Path.
    """
    found: dict[str, Path] = {}
    for agents_dir in agents_dirs:
        if not agents_dir.is_dir():
            continue
        for md_file in sorted(agents_dir.glob("*.md")):
            if md_file.stem.upper() in _SKIP_STEMS:
                continue
            # Use frontmatter 'name' if present, else stem
            fm = _parse_frontmatter(md_file)
            name = str(fm.get("name", "") or md_file.stem)
            found[name] = md_file
    return found


# ---------------------------------------------------------------------------
# Entry building
# ---------------------------------------------------------------------------


def _build_entry(name: str, md_path: Path) -> dict[str, Any]:
    """Build a registry entry dict from a .md file.

    All frontmatter fields are included. DSPy defaults are applied.
    registrySource is set to 'frontmatter'.

    Args:
        name: Agent name (from frontmatter or stem).
        md_path: Path to the .md file.

    Returns:
        Dict suitable for appending to the registry agents list.
    """
    fm = _parse_frontmatter(md_path)

    # Compute a portable file path string
    try:
        rel = md_path.relative_to(Path.cwd())
        file_str = str(rel).replace("\\", "/")
    except ValueError:
        # Global agent outside project root — keep absolute but normalize
        file_str = str(md_path).replace("\\", "/")

    entry: dict[str, Any] = {
        "name": name,
        "file": file_str,
        "model": fm.get("model") or "sonnet",
        "description": fm.get("description") or "",
        "modes": fm.get("modes") or [],
        "capabilities": fm.get("capabilities") or [],
        "input_schema": fm.get("input_schema") or "QuestionPayload",
        "output_schema": fm.get("output_schema") or "FindingPayload",
        "tier": fm.get("tier") or "draft",
        # DSPy / tracking defaults
        "dspy_status": "not_optimized",
        "drift_status": "ok",
        "last_score": None,
        "runs_since_optimization": 0,
        "registrySource": "frontmatter",
    }
    return entry


# ---------------------------------------------------------------------------
# Core backfill logic
# ---------------------------------------------------------------------------


def backfill(
    agents_dirs: list[Path],
    registry_path: Path,
) -> tuple[int, int]:
    """Synchronise the registry with agent .md files on disk.

    Adds entries for agents not yet registered.
    Removes entries whose .md files no longer exist.

    Args:
        agents_dirs: Directories to scan for agent .md files.
        registry_path: Path to the agent_registry.yml file.

    Returns:
        Tuple of (added_count, removed_count).
    """
    data = _load_registry(registry_path)
    existing_entries: list[dict[str, Any]] = data.get("agents", [])

    # Build lookup: name -> entry for existing registry
    registry_by_name: dict[str, dict[str, Any]] = {
        e["name"]: e for e in existing_entries if "name" in e
    }

    # Discover all agent files on disk
    disk_agents = _collect_agent_files(agents_dirs)

    # ── Phantom removal ─────────────────────────────────────────────────────
    # An entry is a phantom if its name is not present in any agents_dir on disk.
    retained: list[dict[str, Any]] = []
    removed_count = 0
    for entry in existing_entries:
        entry_name = entry.get("name", "")
        if entry_name in disk_agents:
            retained.append(entry)
        else:
            removed_count += 1

    # ── New agent addition ───────────────────────────────────────────────────
    registered_names = {e.get("name", "") for e in retained}
    added_count = 0
    for name, md_path in sorted(disk_agents.items()):
        if name not in registered_names:
            new_entry = _build_entry(name, md_path)
            retained.append(new_entry)
            added_count += 1

    data["agents"] = retained
    _save_registry(registry_path, data)

    return added_count, removed_count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill the Masonry agent registry from agent .md files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agents-dir",
        action="append",
        dest="agents_dirs",
        metavar="PATH",
        help="Directory to scan for agent .md files (repeatable). "
        f"Defaults: {[str(d) for d in _DEFAULT_AGENTS_DIRS]}",
    )
    parser.add_argument(
        "--registry",
        dest="registry",
        metavar="PATH",
        default=str(_DEFAULT_REGISTRY),
        help=f"Path to the agent registry YAML. Default: {_DEFAULT_REGISTRY}",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    agents_dirs: list[Path] = (
        [Path(d) for d in args.agents_dirs]
        if args.agents_dirs
        else _DEFAULT_AGENTS_DIRS
    )
    registry_path = Path(args.registry)

    added, removed = backfill(agents_dirs=agents_dirs, registry_path=registry_path)

    data = _load_registry(registry_path)
    total = len(data.get("agents", []))
    print(f"Added {added} agents, removed {removed} phantoms, registry now has {total} total entries")


if __name__ == "__main__":
    main()
