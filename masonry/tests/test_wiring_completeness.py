"""
Wiring Completeness Test Suite
================================
Catches dead code, broken wiring, and orphan assets across the full BrickLayer stack.
Designed to run on every commit or CI push.

Run: pytest masonry/tests/test_wiring_completeness.py -v

Categories:
  W1  Hook files ↔ settings.json (bidirectional)
  W2  Agent .md files ↔ agent_registry.yml (bidirectional)
  W3  /build skill subagent references → agent files exist
  W4  Python import graph (masonry/scripts/)
  W5  Skills have SKILL.md frontmatter
  W6  No files modified in last 24h are unregistered/unreachable

Failure modes caught:
  - File created but not registered (T5/T6 issue pattern)
  - Registry entry pointing to missing file
  - /build references an agent that doesn't exist anywhere
  - Python script imports a module that was deleted
  - New skill directory missing SKILL.md
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# ── Roots ────────────────────────────────────────────────────────────────────
REPO = Path("C:/Users/trg16/Dev/Bricklayer2.0")
CLAUDE = Path("C:/Users/trg16/.claude")
MASONRY = REPO / "masonry"
HOOKS_DIR = MASONRY / "src/hooks"
REGISTRY = MASONRY / "agent_registry.yml"
SETTINGS = CLAUDE / "settings.json"
TEMPLATE_AGENTS = REPO / "template/.claude/agents"
GLOBAL_AGENTS = CLAUDE / "agents"
GLOBAL_SKILLS = CLAUDE / "skills"
BUILD_SKILL = CLAUDE / "skills/build/SKILL.md"

# Hooks intentionally NOT in settings.json (documented exemptions)
# Format: filename → reason
EXEMPT_HOOKS = {
    "masonry-statusline.js": "registered from ~/.claude/hud/ path, not masonry/src/hooks/",
    "masonry-observe-helpers.js": "helper module required by masonry-observe.js, not a standalone hook",
    "masonry-approver-helpers.js": "helper module required by masonry-approver.js, not a standalone hook",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _all_hook_files() -> list[Path]:
    return sorted(HOOKS_DIR.glob("*.js"))


def _settings_hook_commands() -> set[str]:
    """Return all hook command strings from settings.json."""
    settings = json.loads(_read(SETTINGS))
    commands = set()
    for event_hooks in settings.get("hooks", {}).values():
        for group in event_hooks:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                if cmd:
                    commands.add(cmd)
    return commands


def _registry_agent_names() -> set[str]:
    """Return all agent names from agent_registry.yml."""
    if not REGISTRY.exists():
        return set()
    with open(REGISTRY, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        return {entry.get("name", "") for entry in data if entry.get("name")}
    if isinstance(data, dict):
        agents = data.get("agents", data.get("entries", []))
        return {a.get("name", "") for a in agents if a.get("name")}
    return set()


def _agent_md_names(directory: Path) -> set[str]:
    """Return agent names (stem) from non-stub .md files in a directory."""
    # Files that are reference docs, not agent definitions
    skip = {"AUDIT_REPORT", "AGENTS"}
    names = set()
    if not directory.exists():
        return names
    for f in directory.glob("*.md"):
        if f.stem in skip:
            continue
        text = _read(f).strip()
        if text == "STUB":
            continue
        names.add(f.stem)
    return names


def _build_skill_subagent_types() -> set[str]:
    """Parse all subagent_type values from the build SKILL.md."""
    if not BUILD_SKILL.exists():
        return set()
    text = _read(BUILD_SKILL)
    # Match: subagent_type: name, subagent_type: "name", subagent_type: 'name'
    return set(re.findall(r'subagent_type:\s*["\']?(\S+?)["\']?\s', text))


def _agent_exists(name: str) -> bool:
    """Check agent exists in global OR template agents directory."""
    return (GLOBAL_AGENTS / f"{name}.md").exists() or \
           (TEMPLATE_AGENTS / f"{name}.md").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# W1 — Hook Files ↔ Settings.json (bidirectional)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHookWiring:

    def test_w1a_all_hook_files_registered(self):
        """Every hook .js file is referenced in settings.json (or explicitly exempt)."""
        commands = _settings_hook_commands()
        # Collapse to just filenames for matching
        registered_filenames = {Path(c.split()[-1]).name for c in commands if "masonry" in c.lower()}

        orphans = []
        for hook in _all_hook_files():
            if hook.name in EXEMPT_HOOKS:
                continue
            if hook.name not in registered_filenames:
                orphans.append(f"{hook.name}  (reason: new file never wired to settings.json)")

        assert not orphans, (
            f"\n\nORPHAN HOOKS — exist but not registered in settings.json:\n"
            + "\n".join(f"  ✗ {o}" for o in sorted(orphans))
            + "\n\nFix: add to settings.json PreToolUse/PostToolUse/Stop hooks."
        )

    def test_w1b_all_registered_hooks_exist(self):
        """Every hook path in settings.json resolves to an existing file."""
        settings = json.loads(_read(SETTINGS))
        missing = []
        for event, event_hooks in settings.get("hooks", {}).items():
            for group in event_hooks:
                for hook in group.get("hooks", []):
                    cmd = hook.get("command", "")
                    if not cmd:
                        continue
                    # Extract the file path — last whitespace-delimited token after "node"
                    parts = cmd.strip().split()
                    if parts[0] in ("node",):
                        file_path = Path(parts[1])
                    else:
                        continue  # non-node commands (npx etc.) skipped
                    if not file_path.exists():
                        missing.append(f"{event}: {file_path}")

        assert not missing, (
            f"\n\nBROKEN HOOK PATHS — registered but file missing:\n"
            + "\n".join(f"  ✗ {m}" for m in sorted(missing))
        )

    def test_w1c_hook_files_are_valid_js(self):
        """Every registered hook file passes Node.js syntax check."""
        commands = _settings_hook_commands()
        syntax_errors = []
        for cmd in sorted(commands):
            parts = cmd.strip().split()
            if parts[0] != "node" or len(parts) < 2:
                continue
            file_path = Path(parts[1])
            if not file_path.exists():
                continue  # caught by W1b
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                syntax_errors.append(f"{file_path.name}: {result.stderr.strip()[:120]}")

        assert not syntax_errors, (
            "\n\nHOOK SYNTAX ERRORS:\n"
            + "\n".join(f"  ✗ {e}" for e in syntax_errors)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# W2 — Agent Registry ↔ Agent .md Files (bidirectional)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentRegistryWiring:

    # Agents in the registry that are planned but not yet built.
    # These are acknowledged gaps — not blocking any active workflow.
    # Remove from this set as agents are built.
    REGISTRY_ONLY_PLANNED = {
        "adbp-model-analyst", "bug-catcher", "commit-reviewer", "crucible",
        "fix-agent", "forge", "lint-guard", "perf-optimizer", "probe-runner",
        "regression-guard", "scope-analyzer", "scout", "security-hardener",
        "triage", "type-strictener",
    }

    def test_w2a_registry_entries_have_md_file(self):
        """Every non-planned registry entry has a .md file (global or template)."""
        registry_names = _registry_agent_names()
        assert registry_names, "agent_registry.yml appears empty or unparseable"

        missing_md = [
            name for name in sorted(registry_names)
            if not _agent_exists(name)
            and name not in self.REGISTRY_ONLY_PLANNED
        ]
        assert not missing_md, (
            f"\n\nREGISTRY ENTRIES WITH NO .md FILE (not in planned backlog):\n"
            + "\n".join(f"  ✗ {n}" for n in missing_md)
            + "\n\nFix: create agent .md in ~/.claude/agents/ or template/.claude/agents/"
            + f"\n\n(Acknowledged planned-but-not-built: {len(self.REGISTRY_ONLY_PLANNED)} agents)"
        )

    def test_w2b_agent_md_files_in_registry(self):
        """Every non-stub agent .md file has a registry entry."""
        registry_names = _registry_agent_names()
        global_agents = _agent_md_names(GLOBAL_AGENTS)
        template_agents = _agent_md_names(TEMPLATE_AGENTS)
        all_agent_mds = global_agents | template_agents

        orphan_mds = sorted(all_agent_mds - registry_names)
        assert not orphan_mds, (
            f"\n\nORPHAN AGENT .md FILES — not in registry:\n"
            + "\n".join(f"  ✗ {n}" for n in orphan_mds)
            + "\n\nFix: run masonry_onboard or add entry to agent_registry.yml"
        )

    def test_w2c_agent_md_files_have_frontmatter(self):
        """Every non-stub agent .md file starts with YAML frontmatter (---)."""
        missing_fm = []
        for directory in [GLOBAL_AGENTS, TEMPLATE_AGENTS]:
            for f in (directory.glob("*.md") if directory.exists() else []):
                if f.stem in ("AUDIT_REPORT", "AGENTS"):
                    continue
                text = _read(f).strip()
                if text == "STUB":
                    continue
                if not text.startswith("---"):
                    missing_fm.append(f"{directory.name}/{f.name}")

        assert not missing_fm, (
            "\n\nAGENTS MISSING YAML FRONTMATTER:\n"
            + "\n".join(f"  ✗ {f}" for f in sorted(missing_fm))
            + "\n\nFix: add ---\\nname: ...\\ndescription: ...\\nmodel: ...\\n--- at top"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# W3 — /build Skill Subagent References → Agent Files Exist
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildSkillAgentReferences:

    def test_w3a_all_referenced_agents_exist(self):
        """Every subagent_type in build/SKILL.md resolves to an agent file."""
        agent_types = _build_skill_subagent_types()
        assert agent_types, "Could not parse any subagent_type from build/SKILL.md"

        missing = [
            name for name in sorted(agent_types)
            if not _agent_exists(name)
        ]
        assert not missing, (
            "\n\nBUILD SKILL REFERENCES UNDEFINED AGENTS:\n"
            + "\n".join(f"  ✗ {n}" for n in missing)
            + "\n\nFix: create agent .md file or update SKILL.md reference"
        )

    def test_w3b_core_pipeline_agents_exist(self):
        """The 6 agents that /build calls unconditionally all exist."""
        required = [
            "test-writer",
            "developer",
            "code-reviewer",
            "senior-developer",
            "diagnose-analyst",
            "fix-implementer",
        ]
        missing = [n for n in required if not _agent_exists(n)]
        assert not missing, (
            f"\n\nCORE BUILD PIPELINE AGENTS MISSING:\n"
            + "\n".join(f"  ✗ {n}" for n in missing)
        )

    def test_w3c_sparc_phase0_agents_exist(self):
        """Phase 0 agents (pseudocode-writer, architecture-writer) both exist."""
        for name in ["pseudocode-writer", "architecture-writer"]:
            assert _agent_exists(name), (
                f"Phase 0 agent missing: {name} — /build will fail at SPARC context generation"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# W4 — Python Import Graph (masonry/scripts/)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPythonImportGraph:

    def _masonry_imports_in(self, script: Path) -> list[str]:
        """Return all 'from masonry.X import' and 'import masonry.X' statements."""
        text = _read(script)
        found = re.findall(r'(?:from|import)\s+(masonry\.\S+)', text)
        # Normalize: "masonry.src.foo.bar" → "masonry/src/foo/bar"
        return [m.split(".")[0:] for m in found]

    def test_w4a_no_broken_masonry_imports(self):
        """masonry/scripts/*.py only import modules that exist."""
        broken = []
        scripts_dir = MASONRY / "scripts"
        if not scripts_dir.exists():
            pytest.skip("masonry/scripts/ not found")

        for script in sorted(scripts_dir.glob("*.py")):
            # Check only actual import lines (not string literals inside JSON data etc.)
            for line in _read(script).splitlines():
                stripped = line.strip()
                if not (stripped.startswith("from ") or stripped.startswith("import ")):
                    continue
                match = re.search(r'(?:from|import)\s+(masonry\.src\.[a-zA-Z0-9_.]+)', stripped)
                if not match:
                    continue
                module_path = match.group(1)
                parts = module_path.split(".")
                # Build candidate paths: masonry/src/foo/bar.py or masonry/src/foo/bar/__init__.py
                candidate_file = REPO / Path(*parts[:-1]) / f"{parts[-1]}.py"
                candidate_pkg = REPO / Path(*parts) / "__init__.py"
                # Also check if it's the package itself (masonry/src/foo/)
                candidate_dir = REPO / Path(*parts)
                if not (candidate_file.exists() or candidate_pkg.exists() or
                        (candidate_dir.exists() and candidate_dir.is_dir())):
                    broken.append(f"{script.name}: import {module_path}")

        assert not broken, (
            "\n\nBROKEN PYTHON IMPORTS:\n"
            + "\n".join(f"  ✗ {b}" for b in sorted(broken))
        )

    def test_w4b_masonry_package_importable(self):
        """masonry package is importable without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import masonry"],
            capture_output=True, text=True,
            cwd=str(REPO), timeout=15
        )
        assert result.returncode == 0, (
            f"masonry package import failed:\n{result.stderr[:400]}"
        )

    def test_w4c_key_schema_modules_importable(self):
        """Core schema modules import cleanly."""
        modules = [
            "masonry.src.schemas.payloads",
            "masonry.src.routing.router",
            "masonry.src.scoring.rubrics",
        ]
        broken = []
        for mod in modules:
            result = subprocess.run(
                [sys.executable, "-c", f"import {mod}"],
                capture_output=True, text=True,
                cwd=str(REPO), timeout=15
            )
            if result.returncode != 0:
                broken.append(f"{mod}: {result.stderr.strip()[:120]}")

        assert not broken, (
            "\n\nKEY MODULES FAIL TO IMPORT:\n"
            + "\n".join(f"  ✗ {b}" for b in broken)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# W5 — Skills Completeness
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillsCompleteness:

    def test_w5a_all_skill_dirs_have_skill_md(self):
        """Every directory in ~/.claude/skills/ has a SKILL.md file."""
        if not GLOBAL_SKILLS.exists():
            pytest.skip("~/.claude/skills/ not found")

        missing = []
        for skill_dir in sorted(GLOBAL_SKILLS.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").exists():
                missing.append(skill_dir.name)

        assert not missing, (
            "\n\nSKILL DIRECTORIES MISSING SKILL.md:\n"
            + "\n".join(f"  ✗ {s}" for s in missing)
        )

    def test_w5b_skill_md_files_have_frontmatter(self):
        """Every SKILL.md has valid YAML frontmatter with name and description."""
        if not GLOBAL_SKILLS.exists():
            pytest.skip("~/.claude/skills/ not found")

        broken = []
        for skill_dir in sorted(GLOBAL_SKILLS.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            text = _read(skill_md)
            if not text.startswith("---"):
                broken.append(f"{skill_dir.name}: missing frontmatter")
                continue
            end = text.find("---", 3)
            if end == -1:
                broken.append(f"{skill_dir.name}: unclosed frontmatter")
                continue
            fm = text[3:end]
            if "name:" not in fm:
                broken.append(f"{skill_dir.name}: frontmatter missing 'name:'")
            if "description:" not in fm:
                broken.append(f"{skill_dir.name}: frontmatter missing 'description:'")

        assert not broken, (
            "\n\nSKILL.md FRONTMATTER ISSUES:\n"
            + "\n".join(f"  ✗ {b}" for b in broken)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# W6 — Recent Changes Wiring Check (last 24 hours)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecentChangesWiring:

    def _recent_files(self, hours: int = 24) -> list[Path]:
        """Return files changed in the last N hours via git log."""
        result = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--name-only", "--pretty=format:"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            p = REPO / line
            if p.exists():
                files.append(p)
        return files

    def test_w6a_recent_hook_files_are_registered(self):
        """Hook files changed in the last 24h are registered in settings.json."""
        commands = _settings_hook_commands()
        registered_filenames = {Path(c.split()[-1]).name for c in commands if "masonry" in c.lower()}

        recent = self._recent_files()
        newly_unregistered = []
        for f in recent:
            if f.parent == HOOKS_DIR and f.suffix == ".js":
                if f.name not in registered_filenames and f.name not in EXEMPT_HOOKS:
                    newly_unregistered.append(f.name)

        assert not newly_unregistered, (
            "\n\nRECENTLY CHANGED HOOKS NOT REGISTERED (added in last 24h):\n"
            + "\n".join(f"  ✗ {n}" for n in newly_unregistered)
            + "\n\nFix: register in settings.json before committing."
        )

    def test_w6b_recent_agent_files_in_registry(self):
        """Agent .md files changed in last 24h are in agent_registry.yml."""
        registry_names = _registry_agent_names()
        recent = self._recent_files()
        unregistered = []
        for f in recent:
            if f.parent in (GLOBAL_AGENTS, TEMPLATE_AGENTS) and f.suffix == ".md":
                if f.stem == "AUDIT_REPORT":
                    continue
                text = _read(f).strip()
                if text == "STUB":
                    continue
                if f.stem not in registry_names:
                    unregistered.append(f"{f.parent.name}/{f.name}")

        assert not unregistered, (
            "\n\nRECENTLY CHANGED AGENTS NOT IN REGISTRY:\n"
            + "\n".join(f"  ✗ {a}" for a in unregistered)
            + "\n\nFix: run masonry_onboard or add to agent_registry.yml"
        )

    def test_w6c_recent_python_modules_not_broken(self):
        """Python modules changed in last 24h still import cleanly."""
        recent = self._recent_files()
        broken = []
        for f in recent:
            if f.suffix != ".py":
                continue
            if not any(str(f).startswith(str(MASONRY / d)) for d in ["src", "scripts"]):
                continue
            result = subprocess.run(
                [sys.executable, "-c", f"import py_compile; py_compile.compile(r'{f}', doraise=True)"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                broken.append(f"{f.name}: {result.stderr.strip()[:100]}")

        assert not broken, (
            "\n\nRECENTLY CHANGED PYTHON FILES HAVE SYNTAX ERRORS:\n"
            + "\n".join(f"  ✗ {b}" for b in broken)
        )
