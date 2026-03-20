"""
Tests for the overseer registry.json auto-regen step.

Tests generateRegistry() from masonry/src/core/registry.js via node subprocess.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path


REGISTRY_JS = "C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/core/registry.js"
BL_ROOT = "C:/Users/trg16/Dev/Bricklayer2.0"
_SEP = chr(92)


def _run_generate(project_dir: Path) -> dict:
    """Run generateRegistry() by writing JS to a temp file and running node.

    Temp-file approach avoids shell-quoting and pytest PIPE handle errors on Windows.
    """
    reg_js = REGISTRY_JS.replace(_SEP, "/")
    proj = str(project_dir).replace(_SEP, "/")
    script_lines = [
        "const {generateRegistry} = require(" + chr(39) + reg_js + chr(39) + ");",
        "const r = generateRegistry(" + chr(39) + proj + chr(39) + ");",
        "console.log(JSON.stringify(r));",
    ]
    script = chr(10).join(script_lines)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(script)
        tmpname = fh.name
    try:
        result = subprocess.run(
            ["node", tmpname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    finally:
        os.unlink(tmpname)
    assert result.returncode == 0, "node failed: " + result.stderr
    return json.loads(result.stdout.strip())


def _make_agent(
    agents_dir: Path, name: str, description: str = "Test agent.", model: str = "sonnet"
) -> None:
    """Create a minimal valid agent .md file with YAML frontmatter."""
    lines = [
        "---",
        "name: " + name,
        "model: " + model,
        "description: >",
        "  " + description,
        "tools:",
        "  - Read",
        "  - Write",
        "---",
        "",
        "You are the " + name + " agent.",
        "",
    ]
    (agents_dir / (name + ".md")).write_text(chr(10).join(lines), encoding="utf-8")


def test_registry_js_exists() -> None:
    """registry.js must exist at the expected path."""
    assert Path(REGISTRY_JS).exists(), "registry.js not found at " + REGISTRY_JS


def test_registry_generated_with_agents(tmp_path: Path) -> None:
    """generateRegistry() creates registry.json with 2 agents."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(
        agents_dir, "quantitative-analyst", "Runs quantitative analysis.", "sonnet"
    )
    _make_agent(
        agents_dir, "regulatory-researcher", "Researches regulatory landscape.", "opus"
    )

    registry = _run_generate(tmp_path)
    assert (tmp_path / "registry.json").exists(), "registry.json was not created"
    assert len(registry["agents"]) == 2, "Expected 2 agents, got " + str(
        len(registry["agents"])
    )


def test_registry_fields(tmp_path: Path) -> None:
    """Each agent entry has name, file, model, and description fields."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "alpha-agent", "Alpha does alpha things.", "haiku")

    registry = _run_generate(tmp_path)
    assert len(registry["agents"]) == 1
    agent = registry["agents"][0]
    assert agent["name"] == "alpha-agent"
    assert "file" in agent
    assert agent["file"].endswith("alpha-agent.md"), "unexpected file: " + agent["file"]
    assert agent["model"] == "haiku"
    assert "description" in agent and len(agent["description"]) > 0


def test_registry_updates_on_new_agent(tmp_path: Path) -> None:
    """Re-running generateRegistry() after adding a 3rd agent produces 3 entries."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "agent-one")
    _make_agent(agents_dir, "agent-two")
    assert len(_run_generate(tmp_path)["agents"]) == 2

    _make_agent(agents_dir, "agent-three", "Third agent.", "opus")
    registry = _run_generate(tmp_path)
    assert len(registry["agents"]) == 3, "Expected 3, got " + str(
        len(registry["agents"])
    )
    assert "agent-three" in {a["name"] for a in registry["agents"]}


def test_registry_skips_files_without_frontmatter(tmp_path: Path) -> None:
    """Files without valid YAML frontmatter are excluded from registry."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "valid-agent")
    bad = "# No frontmatter" + chr(10) + chr(10) + "Just text." + chr(10)
    (agents_dir / "malformed.md").write_text(bad, encoding="utf-8")

    registry = _run_generate(tmp_path)
    assert len(registry["agents"]) == 1
    assert registry["agents"][0]["name"] == "valid-agent"


def test_registry_sorted_alphabetically(tmp_path: Path) -> None:
    """Agents in registry.json are sorted alphabetically by name."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "zebra-agent")
    _make_agent(agents_dir, "apple-agent")
    _make_agent(agents_dir, "mango-agent")

    registry = _run_generate(tmp_path)
    names = [a["name"] for a in registry["agents"]]
    assert names == sorted(names), "Not sorted: " + str(names)
