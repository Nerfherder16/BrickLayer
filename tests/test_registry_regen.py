"""
Tests for overseer registry.json auto-regen step.

Tests generateRegistry() from masonry/src/core/registry.js via node subprocess.
"""

import json
import subprocess
from pathlib import Path


REGISTRY_JS = Path("C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/core/registry.js")
BL_ROOT = "C:/Users/trg16/Dev/Bricklayer2.0"

# Windows: avoid handle inheritance errors when pytest captures stdout/stderr
_SUBPROCESS_FLAGS = (
    subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
)


def _agent_content(
    name: str, model: str = "sonnet", description: str = "A test agent."
) -> str:
    return (
        f"---\nname: {name}\nmodel: {model}\ndescription: >\n  {description}\n"
        "tools:\n  - Read\n  - Write\n---\n\nYou are the agent.\n"
    )


def _write_agent(
    agents_dir: Path,
    name: str,
    model: str = "sonnet",
    description: str = "A test agent.",
) -> None:
    (agents_dir / f"{name}.md").write_text(
        _agent_content(name, model, description), encoding="utf-8"
    )


def _run_registry(project_dir: Path) -> subprocess.CompletedProcess:
    """Run generateRegistry() via node subprocess.
    Uses shell=True to avoid Windows handle-duplication errors (WinError 6) in pytest."""
    registry_js = str(REGISTRY_JS).replace("\\", "/")
    project = str(project_dir).replace("\\", "/")
    js = (
        f"const {{generateRegistry}} = require('{registry_js}');"
        f"const reg = generateRegistry('{project}');"
        "console.log(JSON.stringify(reg));"
    )
    cmd = f'node -e "{js}"'
    return subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )


def test_registry_generated_with_agents(tmp_path: Path) -> None:
    """generateRegistry() creates registry.json with the correct agent count."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _write_agent(
        agents_dir, "quantitative-analyst", "sonnet", "Runs quantitative analysis."
    )
    _write_agent(
        agents_dir, "regulatory-researcher", "opus", "Researches regulatory landscape."
    )

    result = _run_registry(tmp_path)
    assert result.returncode == 0, f"node failed:\n{result.stderr}"

    registry_file = tmp_path / "registry.json"
    assert registry_file.exists(), "registry.json was not created"

    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    assert "agents" in registry
    assert len(registry["agents"]) == 2, (
        f"Expected 2 agents, got {len(registry['agents'])}"
    )


def test_registry_fields(tmp_path: Path) -> None:
    """Each agent entry has name, file, model, and description fields."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _write_agent(agents_dir, "alpha-agent", "haiku", "Alpha does alpha things.")

    _run_registry(tmp_path)

    registry = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert len(registry["agents"]) == 1
    agent = registry["agents"][0]

    assert agent["name"] == "alpha-agent"
    assert "file" in agent
    assert agent["file"].endswith("alpha-agent.md"), (
        f"unexpected file path: {agent['file']}"
    )
    assert agent["model"] == "haiku"
    assert "description" in agent
    assert len(agent["description"]) > 0


def test_registry_updates_on_new_agent(tmp_path: Path) -> None:
    """Re-running generateRegistry() after adding a 3rd agent produces 3 entries."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _write_agent(agents_dir, "agent-one")
    _write_agent(agents_dir, "agent-two")

    # First run — 2 agents
    _run_registry(tmp_path)
    registry = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert len(registry["agents"]) == 2

    # Add a third agent and re-run
    _write_agent(agents_dir, "agent-three", "opus", "Third agent.")
    result = _run_registry(tmp_path)
    assert result.returncode == 0, f"second run failed:\n{result.stderr}"

    registry = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert len(registry["agents"]) == 3, f"Expected 3, got {len(registry['agents'])}"
    names = {a["name"] for a in registry["agents"]}
    assert "agent-three" in names


def test_registry_skips_files_without_frontmatter(tmp_path: Path) -> None:
    """Files without valid YAML frontmatter are excluded from registry."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _write_agent(agents_dir, "valid-agent")
    (agents_dir / "malformed.md").write_text(
        "# No frontmatter here\n\nJust text.\n", encoding="utf-8"
    )

    _run_registry(tmp_path)
    registry = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert len(registry["agents"]) == 1
    assert registry["agents"][0]["name"] == "valid-agent"


def test_registry_sorted_alphabetically(tmp_path: Path) -> None:
    """Agents in registry.json are sorted alphabetically by name."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _write_agent(agents_dir, "zebra-agent")
    _write_agent(agents_dir, "apple-agent")
    _write_agent(agents_dir, "mango-agent")

    _run_registry(tmp_path)
    registry = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    names = [a["name"] for a in registry["agents"]]
    assert names == sorted(names), f"Not sorted: {names}"
