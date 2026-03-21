"""Auto-onboarding script for Masonry agents.

Detects new .md agent files not yet in the registry, extracts metadata
from YAML frontmatter and body, registers them, and generates DSPy
signature stubs.

CLI usage:
    python masonry/scripts/onboard_agent.py [--agents-dir PATH ...] \
        [--registry PATH] [--dspy-dir PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from masonry.src.schemas import AgentRegistryEntry

# ── Constants ────────────────────────────────────────────────────────────────

_SKIP_STEMS = frozenset({"SCHEMA", "AGENTS", "README", "INDEX"})

_MODE_KEYWORDS: dict[str, list[str]] = {
    "simulate": ["simulat", "simulation", "model"],
    "diagnose": ["diagnos", "diagnose", "debug"],
    "research": ["research", "analys", "explore", "investigat"],
    "audit": ["audit", "review", "check", "inspect"],
    "synthesize": ["synthesiz", "summariz", "consolidat"],
    "fix": ["fix", "repair", "patch", "remediat"],
    "plan": ["plan", "design", "architect"],
}

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
    # Load registered names from the registry
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

    # Collect all .md files from agent directories
    new_agents: list[Path] = []
    for agents_dir in agents_dirs:
        if not agents_dir.is_dir():
            continue
        for md_file in sorted(agents_dir.glob("*.md")):
            if md_file.stem.upper() in _SKIP_STEMS:
                continue
            # Determine the effective name (stem, used for registry lookup)
            stem = md_file.stem
            if stem not in registered_names:
                new_agents.append(md_file)

    return new_agents


# ── extract_agent_metadata ───────────────────────────────────────────────────


def extract_agent_metadata(agent_path: Path) -> dict[str, Any]:
    """Extract metadata from an agent .md file.

    Parses YAML frontmatter for name/model/description, then scans the
    body for mode keywords to populate the modes list.

    Args:
        agent_path: Path to the agent .md file.

    Returns:
        Dict with keys: name, model, description, modes, capabilities, file.
    """
    try:
        content = agent_path.read_text(encoding="utf-8")
    except Exception:
        content = ""

    frontmatter: dict[str, Any] = {}
    body = content

    # Parse YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2]
            except Exception:
                frontmatter = {}

    # Extract fields with fallbacks
    name: str = str(frontmatter.get("name", "") or agent_path.stem)
    model: str = str(frontmatter.get("model", "") or "sonnet")
    description: str = str(frontmatter.get("description", "") or "")

    # Detect modes from body text
    body_lower = body.lower()
    modes: list[str] = []
    for mode, keywords in _MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in body_lower:
                if mode not in modes:
                    modes.append(mode)
                break

    # Also pick up explicit modes from frontmatter
    fm_modes = frontmatter.get("modes", [])
    if isinstance(fm_modes, list):
        for m in fm_modes:
            if m not in modes:
                modes.append(str(m))

    # Capabilities from frontmatter
    capabilities: list[str] = []
    fm_caps = frontmatter.get("capabilities", [])
    if isinstance(fm_caps, list):
        capabilities = [str(c) for c in fm_caps]

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
        "file": file_str,
    }


# ── generate_registry_entry ──────────────────────────────────────────────────


def generate_registry_entry(meta: dict[str, Any]) -> AgentRegistryEntry:
    """Build an AgentRegistryEntry from extracted metadata.

    Defaults tier to "draft", input_schema to "QuestionPayload",
    output_schema to "FindingPayload".

    Args:
        meta: Dict as returned by extract_agent_metadata.

    Returns:
        Validated AgentRegistryEntry Pydantic model.
    """
    # Build kwargs only for fields that have valid non-default values
    kwargs: dict[str, Any] = {
        "name": meta.get("name", ""),
        "file": meta.get("file", ""),
        "input_schema": meta.get("input_schema") or "QuestionPayload",
        "output_schema": meta.get("output_schema") or "FindingPayload",
        "tier": meta.get("tier") or "draft",
    }

    # Optional string fields — only set if non-empty
    description = meta.get("description") or ""
    if description:
        kwargs["description"] = description

    # model must be one of opus/sonnet/haiku — default to sonnet
    model_val = meta.get("model") or "sonnet"
    if model_val in ("opus", "sonnet", "haiku"):
        kwargs["model"] = model_val
    else:
        kwargs["model"] = "sonnet"

    # List fields — use empty list as default (matches schema default_factory)
    modes = meta.get("modes") or []
    capabilities = meta.get("capabilities") or []
    kwargs["modes"] = modes
    kwargs["capabilities"] = capabilities

    return AgentRegistryEntry(**kwargs)


# ── append_to_registry ───────────────────────────────────────────────────────


def append_to_registry(
    entry: AgentRegistryEntry,
    registry_path: Path,
) -> None:
    """Append an AgentRegistryEntry to the YAML registry file.

    Creates the registry file if it does not exist. Preserves all
    existing agents.

    Args:
        entry: The AgentRegistryEntry to add.
        registry_path: Path to the registry YAML file.
    """
    # Load existing data
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

    # Convert entry to dict, dropping None values
    entry_dict = entry.model_dump(exclude_none=True)

    # Append
    data["agents"].append(entry_dict)

    # Write back
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


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
    input_schema = meta.get("input_schema", "QuestionPayload")
    output_schema = meta.get("output_schema", "FindingPayload")

    # Convert kebab-case to PascalCase class name
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
    # Sanitize name for use as filename
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    output_path = output_dir / f"{safe_name}.py"
    output_path.write_text(stub, encoding="utf-8")
    return output_path


# ── onboard ──────────────────────────────────────────────────────────────────


def onboard(
    agents_dirs: list[Path],
    registry_path: Path,
    dspy_output_dir: Path,
) -> list[str]:
    """Detect, register, and generate stubs for new agents.

    Orchestrates the full onboarding pipeline:
    1. detect_new_agents
    2. extract_agent_metadata
    3. generate_registry_entry
    4. append_to_registry
    5. generate_dspy_signature_stub

    Args:
        agents_dirs: Directories to scan for unregistered agents.
        registry_path: Path to the agent registry YAML.
        dspy_output_dir: Directory for generated DSPy signature stubs.

    Returns:
        List of agent names that were onboarded.
    """
    new_paths = detect_new_agents(agents_dirs, registry_path)
    onboarded: list[str] = []

    for agent_path in new_paths:
        meta = extract_agent_metadata(agent_path)
        entry = generate_registry_entry(meta)
        append_to_registry(entry, registry_path)
        generate_dspy_signature_stub(meta, dspy_output_dir)
        onboarded.append(meta["name"])
        print(f"[onboard] Registered: {meta['name']}", file=sys.stderr)

    return onboarded


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
    args = parser.parse_args()

    agents_dirs: list[Path] = (
        [Path(d) for d in args.agents_dirs]
        if args.agents_dirs
        else _DEFAULT_AGENTS_DIRS
    )
    registry_path = Path(args.registry)
    dspy_output_dir = Path(args.dspy_dir)

    onboarded = onboard(agents_dirs, registry_path, dspy_output_dir)

    if onboarded:
        print(f"Onboarded {len(onboarded)} agent(s): {', '.join(onboarded)}")
    else:
        print("No new agents found.")


if __name__ == "__main__":
    main()
