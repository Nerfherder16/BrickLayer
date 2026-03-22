"""Auto-onboarding script for Masonry agents.

Reads YAML frontmatter directly — no keyword inference from body text.
All fields (modes, capabilities, input_schema, output_schema, tier) are
read exclusively from frontmatter.

CLI usage:
    python masonry/scripts/onboard_agent.py [--agents-dir PATH ...] \\
        [--registry PATH] [--dspy-dir PATH]

Hook usage (masonry-agent-onboard.js calls with a single file path):
    python masonry/scripts/onboard_agent.py <filepath>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from masonry.src.schemas import AgentRegistryEntry

# ── Constants ────────────────────────────────────────────────────────────────

_SKIP_STEMS = frozenset({"SCHEMA", "AGENTS", "README", "INDEX"})

_DEFAULT_AGENTS_DIRS: list[Path] = [
    Path.home() / ".claude" / "agents",
    Path("agents"),
]
_DEFAULT_REGISTRY = Path("masonry/agent_registry.yml")
_DEFAULT_DSPY_DIR = Path("masonry/src/dspy_pipeline/generated")


# ── detect_new_agents ────────────────────────────────────────────────────────


def detect_new_agents(
    agents_dirs: list[Path],
    registry_path: Path,
) -> list[Path]:
    """Return paths to .md agent files not present in the registry.

    Args:
        agents_dirs: Directories to scan for agent .md files.
        registry_path: Path to the agent registry YAML.

    Returns:
        List of Path objects for unregistered agent files.
    """
    registered_names: set[str] = set()
    if registry_path.exists():
        try:
            raw = registry_path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw) or {}
            for entry in data.get("agents", []):
                name = entry.get("name", "")
                if name:
                    registered_names.add(name)
        except Exception:
            pass  # treat as empty registry on parse error

    new_agents: list[Path] = []
    for agents_dir in agents_dirs:
        if not agents_dir.is_dir():
            continue
        for md_file in sorted(agents_dir.glob("*.md")):
            if md_file.stem.upper() in _SKIP_STEMS:
                continue
            stem = md_file.stem
            if stem not in registered_names:
                new_agents.append(md_file)

    return new_agents


# ── detect_stale_registry_entries ────────────────────────────────────────────


def detect_stale_registry_entries(registry_path: Path) -> list[dict[str, Any]]:
    """Find registry entries whose file no longer exists at the path in 'file:'.

    Args:
        registry_path: Path to the agent registry YAML.

    Returns:
        List of raw agent dicts (from the YAML) whose file is missing.
    """
    if not registry_path.exists():
        return []

    try:
        raw = registry_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
    except Exception:
        return []

    stale: list[dict[str, Any]] = []
    for entry in data.get("agents", []):
        file_val = entry.get("file", "")
        if file_val and not Path(file_val).exists():
            stale.append(entry)

    return stale


# ── extract_agent_metadata ───────────────────────────────────────────────────


def extract_agent_metadata(agent_path: Path) -> dict[str, Any]:
    """Extract metadata from an agent .md file.

    Reads ONLY from YAML frontmatter — no keyword inference from body text.
    Fields read: name, model, description, modes, capabilities,
                 input_schema, output_schema, tier.

    Args:
        agent_path: Path to the agent .md file.

    Returns:
        Dict with keys: name, model, description, modes, capabilities,
        input_schema, output_schema, tier, file.
    """
    try:
        content = agent_path.read_text(encoding="utf-8")
    except Exception:
        content = ""

    frontmatter: dict[str, Any] = {}

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                frontmatter = {}

    # All fields read directly from frontmatter — no inference
    name: str = str(frontmatter.get("name", "") or agent_path.stem)
    model: str = str(frontmatter.get("model", "") or "sonnet")
    description: str = str(frontmatter.get("description", "") or "")

    # Modes: frontmatter only, no body scanning
    modes: list[str] = []
    fm_modes = frontmatter.get("modes", [])
    if isinstance(fm_modes, list):
        modes = [str(m) for m in fm_modes]

    # Capabilities: frontmatter only
    capabilities: list[str] = []
    fm_caps = frontmatter.get("capabilities", [])
    if isinstance(fm_caps, list):
        capabilities = [str(c) for c in fm_caps]

    # Schema and tier fields from frontmatter
    input_schema: str | None = frontmatter.get("input_schema") or None
    output_schema: str | None = frontmatter.get("output_schema") or None
    tier: str | None = frontmatter.get("tier") or None

    # Routing keywords: frontmatter only, no inference
    routing_keywords: list[str] = []
    fm_keywords = frontmatter.get("routing_keywords", [])
    if isinstance(fm_keywords, list):
        routing_keywords = [str(k) for k in fm_keywords if k]

    # Compute relative file path (best-effort)
    try:
        rel = agent_path.relative_to(Path.cwd())
        file_str = str(rel).replace("\\", "/")
    except ValueError:
        file_str = str(agent_path).replace("\\", "/")

    return {
        "name": name,
        "model": model,
        "description": description,
        "modes": modes,
        "capabilities": capabilities,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "tier": tier,
        "routing_keywords": routing_keywords,
        "file": file_str,
    }


# ── generate_registry_entry ──────────────────────────────────────────────────


def generate_registry_entry(meta: dict[str, Any]) -> AgentRegistryEntry:
    """Build an AgentRegistryEntry from extracted metadata.

    Defaults tier to "draft", input_schema to "QuestionPayload",
    output_schema to "FindingPayload". All values from frontmatter take
    precedence; missing values fall back to defaults.

    Args:
        meta: Dict as returned by extract_agent_metadata.

    Returns:
        Validated AgentRegistryEntry Pydantic model.
    """
    kwargs: dict[str, Any] = {
        "name": meta.get("name", ""),
        "file": meta.get("file", ""),
        "input_schema": meta.get("input_schema") or "QuestionPayload",
        "output_schema": meta.get("output_schema") or "FindingPayload",
        "tier": meta.get("tier") or "draft",
    }

    description = meta.get("description") or ""
    if description:
        kwargs["description"] = description

    model_val = meta.get("model") or "sonnet"
    kwargs["model"] = model_val if model_val in ("opus", "sonnet", "haiku") else "sonnet"

    kwargs["modes"] = meta.get("modes") or []
    kwargs["capabilities"] = meta.get("capabilities") or []
    kwargs["routing_keywords"] = meta.get("routing_keywords") or []

    return AgentRegistryEntry(**kwargs)


# ── append_to_registry ───────────────────────────────────────────────────────


def append_to_registry(
    entry: AgentRegistryEntry,
    registry_path: Path,
) -> None:
    """Append an AgentRegistryEntry to the YAML registry file.

    Creates the registry file if it does not exist. Preserves all
    existing agents. Does NOT check for duplicates — use upsert_registry_entry
    for idempotent writes.

    Args:
        entry: The AgentRegistryEntry to add.
        registry_path: Path to the registry YAML file.
    """
    data: dict[str, Any] = {"version": 1, "agents": []}
    if registry_path.exists():
        try:
            raw = registry_path.read_text(encoding="utf-8")
            loaded = yaml.safe_load(raw) or {}
            if isinstance(loaded, dict):
                data = loaded
                if "agents" not in data:
                    data["agents"] = []
                if "version" not in data:
                    data["version"] = 1
        except Exception:
            pass

    entry_dict = entry.model_dump(exclude_none=True)
    data["agents"].append(entry_dict)

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = registry_path.with_suffix(f".yml.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
        tmp_path.replace(registry_path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


# ── upsert_registry_entry ─────────────────────────────────────────────────────


def upsert_registry_entry(
    entry: AgentRegistryEntry,
    registry_path: Path,
    extra_fields: dict[str, Any] | None = None,
) -> bool:
    """Insert or update an AgentRegistryEntry in the YAML registry.

    If an entry with the same name already exists, it is updated in-place.
    If not, a new entry is appended. Running twice with the same entry
    produces the same result (idempotent).

    Args:
        entry: The AgentRegistryEntry to insert or update.
        registry_path: Path to the registry YAML file.
        extra_fields: Additional raw fields to merge into the stored dict
            (e.g. runtime state fields not part of the Pydantic model).

    Returns:
        True if a new entry was added, False if an existing one was updated.
    """
    data: dict[str, Any] = {"version": 1, "agents": []}
    if registry_path.exists():
        try:
            raw = registry_path.read_text(encoding="utf-8")
            loaded = yaml.safe_load(raw) or {}
            if isinstance(loaded, dict):
                data = loaded
                if "agents" not in data:
                    data["agents"] = []
                if "version" not in data:
                    data["version"] = 1
        except Exception:
            pass

    entry_dict = entry.model_dump(exclude_none=True)
    if extra_fields:
        entry_dict.update(extra_fields)

    # Find existing entry by name
    existing_idx: int | None = None
    for idx, existing in enumerate(data["agents"]):
        if existing.get("name") == entry.name:
            existing_idx = idx
            break

    is_new = existing_idx is None
    if is_new:
        data["agents"].append(entry_dict)
    else:
        # Preserve existing extra fields (like runtime state) unless overridden
        merged = dict(data["agents"][existing_idx])
        merged.update(entry_dict)
        data["agents"][existing_idx] = merged

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = registry_path.with_suffix(f".yml.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
        tmp_path.replace(registry_path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return is_new


# ── generate_dspy_signature_stub ─────────────────────────────────────────────


def generate_dspy_signature_stub(
    meta: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Generate a DSPy Signature stub Python file for an agent.

    Args:
        meta: Dict with at least 'name', 'input_schema', 'output_schema'.
        output_dir: Directory to write the generated file.

    Returns:
        Path to the generated .py file.
    """
    name = meta.get("name", "agent")
    input_schema = meta.get("input_schema") or "QuestionPayload"
    output_schema = meta.get("output_schema") or "FindingPayload"

    class_name = "".join(part.capitalize() for part in re.split(r"[-_]", name)) + "Sig"

    stub = f'''"""DSPy Signature stub for {name} agent.

Auto-generated by masonry/scripts/onboard_agent.py — edit with care.
"""

from __future__ import annotations

import dspy


class {class_name}(dspy.Signature):
    """Signature for the {name} agent.

    Input:  {input_schema}
    Output: {output_schema}
    """

    # Input fields
    question: str = dspy.InputField(
        default="",
        desc="The research question or task prompt for this agent.",
    )
    context: str = dspy.InputField(
        default="",
        desc="Optional background context (project brief, prior findings).",
    )

    # Output fields
    verdict: str = dspy.OutputField(
        default="",
        desc="Short verdict string (e.g. HEALTHY, WARNING, CRITICAL).",
    )
    evidence: str = dspy.OutputField(
        default="",
        desc="Supporting evidence and reasoning for the verdict.",
    )
    confidence: float = dspy.OutputField(
        default=0.75,
        desc="Confidence score between 0.0 and 1.0.",
    )
'''

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    output_path = output_dir / f"{safe_name}.py"
    output_path.write_text(stub, encoding="utf-8")
    return output_path


# ── onboard ──────────────────────────────────────────────────────────────────

_RUNTIME_STATE_DEFAULTS: dict[str, Any] = {
    "dspy_status": "not_optimized",
    "drift_status": "ok",
    "last_score": None,
    "runs_since_optimization": 0,
}


def onboard(
    agents_dirs: list[Path],
    registry_path: Path,
    dspy_output_dir: Path,
) -> dict[str, Any]:
    """Detect, register, and generate stubs for new agents.

    This function is idempotent: running twice produces the same registry
    (no duplicate entries). Uses upsert semantics for existing entries.

    Runtime state fields (dspy_status, drift_status, last_score,
    runs_since_optimization) are written for new entries only.

    Orchestrates the full onboarding pipeline:
    1. detect_new_agents
    2. extract_agent_metadata
    3. generate_registry_entry
    4. upsert_registry_entry (with runtime state for new entries)
    5. generate_dspy_signature_stub
    6. detect_stale_registry_entries

    Args:
        agents_dirs: Directories to scan for unregistered agents.
        registry_path: Path to the agent registry YAML.
        dspy_output_dir: Directory for generated DSPy signature stubs.

    Returns:
        Structured result dict:
        {
            "added": int,       # new agents registered
            "updated": int,     # existing entries updated
            "stale": int,       # registry entries with missing files
            "warnings": list[str],
        }
    """
    new_paths = detect_new_agents(agents_dirs, registry_path)
    added = 0
    updated = 0
    warnings: list[str] = []
    added_names: list[str] = []

    for agent_path in new_paths:
        meta = extract_agent_metadata(agent_path)
        entry = generate_registry_entry(meta)
        is_new = upsert_registry_entry(entry, registry_path, extra_fields=_RUNTIME_STATE_DEFAULTS)
        generate_dspy_signature_stub(meta, dspy_output_dir)

        if is_new:
            added += 1
            added_names.append(meta["name"])
            print(f"[onboard] Registered: {meta['name']}", file=sys.stderr)
        else:
            updated += 1
            print(f"[onboard] Updated: {meta['name']}", file=sys.stderr)

    stale = detect_stale_registry_entries(registry_path)

    return {
        "added": added,
        "updated": updated,
        "stale": len(stale),
        "warnings": warnings,
        "names": added_names,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-onboard new Masonry agents into the registry.",
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
    parser.add_argument(
        "--dspy-dir",
        dest="dspy_dir",
        metavar="PATH",
        default=str(_DEFAULT_DSPY_DIR),
        help=f"Output directory for DSPy signature stubs. Default: {_DEFAULT_DSPY_DIR}",
    )
    return parser


def main() -> None:
    parser = _build_parser()

    # Support legacy positional single-file invocation from the hook:
    #   python onboard_agent.py <filepath>
    # If the first arg looks like a file path (not a flag), treat as single-file mode.
    if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        agent_path = Path(sys.argv[1])
        agents_dir = agent_path.parent
        registry_path = Path(_DEFAULT_REGISTRY)
        dspy_output_dir = Path(_DEFAULT_DSPY_DIR)
        result = onboard([agents_dir], registry_path, dspy_output_dir)
        print(f"added={result['added']} updated={result['updated']} stale={result['stale']}")
        return

    args = parser.parse_args()

    agents_dirs: list[Path] = (
        [Path(d) for d in args.agents_dirs]
        if args.agents_dirs
        else _DEFAULT_AGENTS_DIRS
    )
    registry_path = Path(args.registry)
    dspy_output_dir = Path(args.dspy_dir)

    result = onboard(agents_dirs, registry_path, dspy_output_dir)

    if result["added"] or result["updated"]:
        print(
            f"Onboarded: {result['added']} added, {result['updated']} updated, "
            f"{result['stale']} stale."
        )
    else:
        print("No new agents found.")


if __name__ == "__main__":
    main()
