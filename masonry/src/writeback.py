"""masonry/src/writeback.py

Helpers for writing optimized agent instructions back to .md files
and updating agent_registry.yml. No DSPy dependency.
"""

from __future__ import annotations

import re
from pathlib import Path

_SECTION_HEADER = "## DSPy Optimized Instructions"
_SECTION_END = "<!-- /DSPy Optimized Instructions -->"
_SECTION_PATTERN = re.compile(
    rf"{re.escape(_SECTION_HEADER)}.*?{re.escape(_SECTION_END)}\n?",
    re.DOTALL,
)


def writeback_optimized_instructions(
    base_dir: Path,
    agent_name: str,
    instructions: str,
    optimized_at: str,
) -> list[Path]:
    """Inject optimized instructions into all copies of an agent .md file.

    Searches:
      - base_dir/.claude/agents/{agent}.md
      - base_dir/{project}/.claude/agents/{agent}.md  (one level deep)
      - ~/.claude/agents/{agent}.md

    Replaces existing section in-place, or appends if not present.
    Returns list of updated file paths.
    """
    section_text = (
        f"\n{_SECTION_HEADER}\n"
        f"{instructions}\n\n"
        f"{_SECTION_END}\n"
    )

    candidates: list[Path] = [
        base_dir / ".claude" / "agents" / f"{agent_name}.md",
    ]
    for child in base_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            p = child / ".claude" / "agents" / f"{agent_name}.md"
            if p.exists():
                candidates.append(p)
    candidates.append(Path.home() / ".claude" / "agents" / f"{agent_name}.md")

    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        resolved = c.resolve() if c.exists() else c
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)

    updated: list[Path] = []
    for md_path in unique:
        if not md_path.exists():
            continue
        content = md_path.read_text(encoding="utf-8")
        if _SECTION_PATTERN.search(content):
            new_content = _SECTION_PATTERN.sub(section_text.lstrip("\n"), content)
        else:
            new_content = content.rstrip("\n") + "\n" + section_text
        md_path.write_text(new_content, encoding="utf-8")
        updated.append(md_path)

    return updated


def strip_optimized_instructions(md_path: Path) -> bool:
    """Remove the optimized instructions section from an agent .md file.

    Returns True if a section was found and removed, False if nothing changed.
    """
    if not md_path.exists():
        return False
    content = md_path.read_text(encoding="utf-8")
    if not _SECTION_PATTERN.search(content):
        return False
    new_content = _SECTION_PATTERN.sub("", content).rstrip("\n") + "\n"
    md_path.write_text(new_content, encoding="utf-8")
    return True


def update_registry_dspy_status(
    registry_path: Path,
    agent_name: str,
    optimized_at: str,
) -> None:
    """Update dspy_status and last_optimized fields in agent_registry.yml."""
    if not registry_path.exists():
        return
    content = registry_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    in_target = False
    updated = []
    for line in lines:
        name_match = line.strip().startswith("- name:") or (
            line.strip().startswith("name:") and not line.strip().startswith("name: #")
        )
        if name_match and agent_name in line:
            in_target = True
        elif name_match:
            in_target = False
        if in_target and "dspy_status:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + "dspy_status: optimized"
        elif in_target and "last_optimized:" in line:
            indent = len(line) - len(line.lstrip())
            line = " " * indent + f"last_optimized: {optimized_at}"
        updated.append(line)
    registry_path.write_text("\n".join(updated), encoding="utf-8")
