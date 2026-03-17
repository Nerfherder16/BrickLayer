"""
bl/skill_forge.py — Skill registry and forge utilities.

Tracks skills created by BrickLayer campaigns so the overseer can review,
repair, or retire them. Skills live at ~/.claude/skills/{name}/SKILL.md.

Registry: {project_dir}/skill_registry.json
  Maps skill_name → {source, created, campaign, last_updated, description}

The skill-forge agent calls write_skill() after creating each skill.
The overseer reads list_project_skills() to review them at wave end.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


_CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _registry_path(project_root: Path) -> Path:
    return project_root / "skill_registry.json"


def _load_registry(project_root: Path) -> dict:
    path = _registry_path(project_root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(project_root: Path, registry: dict) -> None:
    _registry_path(project_root).write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_skill(
    name: str,
    content: str,
    project_root: Path,
    description: str = "",
    source_finding: str = "",
) -> Path:
    """
    Write a skill to ~/.claude/skills/{name}/SKILL.md and register it.

    Returns the path of the written skill file.
    """
    skill_dir = _CLAUDE_SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")

    # Register in project registry
    registry = _load_registry(project_root)
    now = datetime.now(timezone.utc).isoformat()
    if name not in registry:
        registry[name] = {
            "created": now,
            "last_updated": now,
            "description": description,
            "source_finding": source_finding,
            "campaign": project_root.name,
            "repair_count": 0,
        }
    else:
        registry[name]["last_updated"] = now
        registry[name]["repair_count"] = registry[name].get("repair_count", 0) + 1

    _save_registry(project_root, registry)
    return skill_path


def skill_exists(name: str) -> bool:
    """Return True if the skill already exists in ~/.claude/skills/."""
    return (_CLAUDE_SKILLS_DIR / name / "SKILL.md").exists()


def read_skill(name: str) -> str | None:
    """Read a skill's content, or None if it doesn't exist."""
    path = _CLAUDE_SKILLS_DIR / name / "SKILL.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def list_project_skills(project_root: Path) -> list[dict]:
    """Return all skills created by this project's campaigns, with current content."""
    registry = _load_registry(project_root)
    result = []
    for name, meta in registry.items():
        path = _CLAUDE_SKILLS_DIR / name / "SKILL.md"
        result.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "description": meta.get("description", ""),
                "source_finding": meta.get("source_finding", ""),
                "campaign": meta.get("campaign", ""),
                "created": meta.get("created", ""),
                "last_updated": meta.get("last_updated", ""),
                "repair_count": meta.get("repair_count", 0),
            }
        )
    return sorted(result, key=lambda x: x["created"])


def global_skill_inventory() -> list[dict]:
    """Return all skills in ~/.claude/skills/ regardless of project origin."""
    if not _CLAUDE_SKILLS_DIR.exists():
        return []
    result = []
    for skill_dir in sorted(_CLAUDE_SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            # Extract description from frontmatter if present
            desc = ""
            for line in content.splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
            result.append(
                {
                    "name": skill_dir.name,
                    "path": str(skill_file),
                    "description": desc,
                }
            )
    return result
