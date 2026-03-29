"""
backfill_routing_keywords.py

Backfill routing_keywords for agents that are missing them.

Usage:
    python backfill_routing_keywords.py [--dry-run] [--agents-dir PATH] [--registry PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from backfill_keywords_extractor import extract_keywords


DEFAULT_AGENTS_DIR = Path.home() / ".claude" / "agents"
DEFAULT_REGISTRY = Path("C:/Users/trg16/Dev/Bricklayer2.0/masonry/agent_registry.yml")


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def split_frontmatter(raw: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Raises ValueError on malformed."""
    if not raw.startswith("---"):
        raise ValueError("No leading ---")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Only one --- delimiter found")
    return parts[1], parts[2]


def load_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter. Returns (fm_dict, body_text)."""
    fm_block, body = split_frontmatter(raw)
    try:
        fm = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error: {exc}") from exc
    if not isinstance(fm, dict):
        raise ValueError("Frontmatter did not parse to a mapping")
    return fm, body


def write_frontmatter(fm: dict[str, Any], body: str) -> str:
    """Serialize updated frontmatter back into the full file string."""
    fm_yaml = yaml.safe_dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm_yaml}---{body}"


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def load_registry(path: Path) -> tuple[list[dict[str, Any]], bool]:
    """Load registry. Returns (agent_list, has_agents_key)."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw, False
    if isinstance(raw, dict) and "agents" in raw:
        return raw["agents"], True
    raise ValueError(f"Unrecognized registry shape in {path}")


def save_registry(path: Path, agents: list[dict[str, Any]], has_agents_key: bool) -> None:
    data: Any = {"agents": agents} if has_agents_key else agents
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Agent processing
# ---------------------------------------------------------------------------

def resolve_md_path(entry: dict[str, Any], agents_dir: Path) -> Path | None:
    if "file" in entry and entry["file"]:
        p = Path(entry["file"])
        if p.exists():
            return p
    name = entry.get("name", "")
    if name:
        p = agents_dir / f"{name}.md"
        if p.exists():
            return p
    return None


def process_agent(entry: dict[str, Any], agents_dir: Path) -> tuple[list[str], str] | None:
    """Returns (keywords, source_label) or None if agent should be skipped."""
    name = entry.get("name", "<unknown>")

    md_path = resolve_md_path(entry, agents_dir)
    if md_path is None:
        print(f"  Skipping {name}: file not found", file=sys.stderr)
        return None

    raw = md_path.read_text(encoding="utf-8")
    try:
        fm, body = load_frontmatter(raw)
    except ValueError as exc:
        print(f"  Skipping {name}: malformed frontmatter ({exc})", file=sys.stderr)
        return None

    # Sync gap fix: frontmatter already has keywords but registry is missing them
    existing = fm.get("routing_keywords")
    if existing and isinstance(existing, list) and existing:
        return existing, "frontmatter_existing"

    return extract_keywords(fm, body)


# ---------------------------------------------------------------------------
# Main run logic
# ---------------------------------------------------------------------------

def run(agents_dir: Path, registry_path: Path, dry_run: bool) -> int:
    agents, has_agents_key = load_registry(registry_path)

    targets = [
        entry for entry in agents
        if not entry.get("routing_keywords") or
           (isinstance(entry.get("routing_keywords"), list) and
            len(entry["routing_keywords"]) == 0)
    ]

    if not targets:
        print("All agents already have routing_keywords. Nothing to do.")
        return 0

    print(f"Found {len(targets)} agent(s) needing routing_keywords backfill.\n")

    col_name, col_kw, col_src = 30, 60, 20
    print(f"{'Agent':<{col_name}} {'Keywords':<{col_kw}} {'Source':<{col_src}}")
    print("-" * (col_name + col_kw + col_src + 2))

    results: list[tuple[dict[str, Any], list[str], str]] = []
    stubs_skipped = 0

    for entry in targets:
        name = entry.get("name", "<unknown>")
        outcome = process_agent(entry, agents_dir)
        if outcome is None:
            stubs_skipped += 1
            print(f"{'  ' + name:<{col_name}} {'(skipped)':<{col_kw}} {'':<{col_src}}")
            continue
        keywords, source = outcome
        kw_display = ", ".join(keywords) if keywords else "(none extracted)"
        if len(kw_display) > col_kw - 1:
            kw_display = kw_display[: col_kw - 4] + "..."
        print(f"{name:<{col_name}} {kw_display:<{col_kw}} {source:<{col_src}}")
        results.append((entry, keywords, source))

    print()

    if dry_run:
        total_kw = sum(len(kw) for _, kw, _ in results)
        print("[dry-run] No files written.")
        print(
            f"Summary (dry-run): {len(results)} agents would be updated, "
            f"{total_kw} total keywords, {stubs_skipped} stubs skipped."
        )
        return 0

    # Write back
    updated = 0
    total_kw = 0

    for entry, keywords, _ in results:
        if not keywords:
            continue
        md_path = resolve_md_path(entry, agents_dir)
        if md_path is None:
            continue
        raw = md_path.read_text(encoding="utf-8")
        try:
            fm, body = load_frontmatter(raw)
        except ValueError:
            continue
        fm["routing_keywords"] = keywords
        md_path.write_text(write_frontmatter(fm, body), encoding="utf-8")
        entry["routing_keywords"] = keywords
        updated += 1
        total_kw += len(keywords)

    save_registry(registry_path, agents, has_agents_key)
    print(
        f"Summary: {updated} agents updated, "
        f"{total_kw} total keywords written, "
        f"{stubs_skipped} stubs skipped."
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill routing_keywords for agents missing them."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print keyword table without writing any files.")
    parser.add_argument("--agents-dir", type=Path, default=DEFAULT_AGENTS_DIR,
                        help=f"Agent .md files directory (default: {DEFAULT_AGENTS_DIR})")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                        help=f"Path to agent_registry.yml (default: {DEFAULT_REGISTRY})")
    args = parser.parse_args()

    if not args.registry.exists():
        print(f"ERROR: Registry not found: {args.registry}", file=sys.stderr)
        sys.exit(1)
    if not args.agents_dir.exists():
        print(f"WARNING: agents-dir not found: {args.agents_dir}", file=sys.stderr)

    sys.exit(run(args.agents_dir, args.registry, args.dry_run))


if __name__ == "__main__":
    main()
