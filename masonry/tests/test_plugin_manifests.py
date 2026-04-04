"""
Task 30: JSON parse validation for BrickLayer Claude plugin manifests.
Verifies that both manifest files parse as valid JSON and contain required fields.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_JSON = REPO_ROOT / "plugins" / "bricklayer" / "plugin.json"


def test_marketplace_json_exists():
    assert MARKETPLACE_JSON.exists(), f"Missing: {MARKETPLACE_JSON}"


def test_marketplace_json_parses():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_marketplace_json_required_fields():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "bricklayer"
    assert data["version"] == "2.0.0"
    assert isinstance(data["commands"], list)
    assert len(data["commands"]) > 0
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) > 0
    assert isinstance(data["mcpServers"], list)
    assert len(data["mcpServers"]) > 0


def test_marketplace_json_commands_have_name_and_description():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    for cmd in data["commands"]:
        assert "name" in cmd, f"Command missing 'name': {cmd}"
        assert "description" in cmd, f"Command missing 'description': {cmd}"


def test_marketplace_json_agents_have_name_and_description():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    for agent in data["agents"]:
        assert "name" in agent, f"Agent missing 'name': {agent}"
        assert "description" in agent, f"Agent missing 'description': {agent}"


def test_marketplace_json_mcp_servers_have_required_field():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    for server in data["mcpServers"]:
        assert "name" in server
        assert "required" in server
        assert isinstance(server["required"], bool)


def test_plugin_json_exists():
    assert PLUGIN_JSON.exists(), f"Missing: {PLUGIN_JSON}"


def test_plugin_json_parses():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_plugin_json_required_fields():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "bricklayer"
    assert data["version"] == "2.0.0"
    assert isinstance(data["install_steps"], list)
    assert len(data["install_steps"]) > 0
    assert isinstance(data["post_install"], list)
    assert len(data["post_install"]) > 0


def test_plugin_json_install_steps_have_action():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    for step in data["install_steps"]:
        assert "action" in step, f"Install step missing 'action': {step}"


def test_readme_exists():
    readme = REPO_ROOT / ".claude-plugin" / "README.md"
    assert readme.exists(), f"Missing: {readme}"
    content = readme.read_text(encoding="utf-8")
    assert "claude install bricklayer" in content
    assert "/teach-bricklayer" in content
    assert "/plan" in content
    assert "/build" in content
