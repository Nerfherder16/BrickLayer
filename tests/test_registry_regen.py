import json
import subprocess
from pathlib import Path


REGISTRY_JS = Path("C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/core/registry.js")
BL_ROOT = "C:/Users/trg16/Dev/Bricklayer2.0"


def _run_generate(project_dir):
    reg_js = str(REGISTRY_JS).replace(chr(92), "/")
    proj_dir = str(project_dir).replace(chr(92), "/")
    script = (
        "const {generateRegistry} = require('" + reg_js + "');"
        "const r = generateRegistry('" + proj_dir + "');"
        "console.log(JSON.stringify(r));"
    )
    result = subprocess.run(
        ["node", "-e", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"node failed: {result.stderr}"
    return json.loads(result.stdout.strip())


def _make_agent(agents_dir, name, description="Test agent", model="sonnet"):
    parts = [
        "---",
        f"name: {name}",
        f"model: {model}",
        "description: >",
        f"  {description}",
        "tools:",
        "  - Read",
        "  - Write",
        "---",
        "",
        f"You are the {name} agent.",
    ]
    agent_file = agents_dir / f"{name}.md"
    agent_file.write_text(chr(10).join(parts))
    return agent_file


def test_registry_js_exists():
    assert REGISTRY_JS.exists(), f"registry.js not found at {REGISTRY_JS}"


def test_node_can_require_registry_js():
    reg_js = str(REGISTRY_JS).replace(chr(92), "/")
    r = subprocess.run(
        ["node", "-e", f"require('{reg_js}'); console.log('ok');"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert r.returncode == 0, f"require failed: {r.stderr}"
    assert "ok" in r.stdout


def test_generate_registry_empty_project(tmp_path):
    registry = _run_generate(tmp_path)
    assert "agents" in registry
    assert len(registry["agents"]) == 0


def test_generate_registry_two_agents(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "quantitative-analyst", "Runs simulations")
    _make_agent(agents_dir, "regulatory-researcher", "Checks compliance")
    assert len(_run_generate(tmp_path)["agents"]) == 2


def test_registry_agent_has_required_fields(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "test-agent", "A test agent", model="opus")
    reg = _run_generate(tmp_path)
    assert len(reg["agents"]) == 1
    a = reg["agents"][0]
    assert a["name"] == "test-agent"
    assert "file" in a
    assert a["model"] == "opus"
    assert "description" in a


def test_registry_json_written_to_project_dir(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "mortar", "Build orchestrator")
    _run_generate(tmp_path)
    registry_file = tmp_path / "registry.json"
    assert registry_file.exists()
    data = json.loads(registry_file.read_text())
    assert len(data["agents"]) == 1


def test_registry_file_paths_use_forward_slashes(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "path-test", "Path test")
    reg = _run_generate(tmp_path)
    fp = reg["agents"][0]["file"]
    assert chr(92) not in fp, f"Backslash in path: {fp}"


def test_adding_agent_updates_registry_count(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "agent-one", "First")
    _make_agent(agents_dir, "agent-two", "Second")
    assert len(_run_generate(tmp_path)["agents"]) == 2
    _make_agent(agents_dir, "agent-three", "Third")
    assert len(_run_generate(tmp_path)["agents"]) == 3


def test_agents_without_frontmatter_are_skipped(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "valid-agent", "Has frontmatter")
    (agents_dir / "no-frontmatter.md").write_text("# No YAML")
    reg = _run_generate(tmp_path)
    assert len(reg["agents"]) == 1
    assert reg["agents"][0]["name"] == "valid-agent"


def test_overseer_step5_node_command(tmp_path):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    _make_agent(agents_dir, "quantitative-analyst", "Runs simulations")
    bl = BL_ROOT.replace(chr(92), "/")
    pd = str(tmp_path).replace(chr(92), "/")
    script = (
        "const path = require('path');"
        "const {generateRegistry} = require('" + bl + "/masonry/src/core/registry.js');"
        "const reg = generateRegistry('" + pd + "');"
        "console.log('[OVERSEER] registry.json regenerated -- ' + reg.agents.length + ' agents indexed');"
    )
    result = subprocess.run(
        ["node", "-e", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Step 5 failed: {result.stderr}"
    assert "[OVERSEER] registry.json regenerated" in result.stdout
    assert "1 agents indexed" in result.stdout
