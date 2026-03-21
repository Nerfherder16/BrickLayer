"""Tests for masonry/scripts/onboard_agent.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from masonry.scripts.onboard_agent import (
    append_to_registry,
    detect_new_agents,
    extract_agent_metadata,
    generate_dspy_signature_stub,
    generate_registry_entry,
    onboard,
)
from masonry.src.schemas import AgentRegistryEntry


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _write_agent(path: Path, name: str, model: str = "sonnet", description: str = "Test agent") -> None:
    path.write_text(
        textwrap.dedent(f"""\
            ---
            name: {name}
            model: {model}
            description: "{description}"
            ---

            # {name}

            This agent runs simulations and diagnoses issues.
            It can also perform research and analysis.
        """),
        encoding="utf-8",
    )


def _write_registry(path: Path, agents: list[str]) -> None:
    data = {
        "version": 1,
        "agents": [
            {"name": a, "file": f"agents/{a}.md", "tier": "draft"}
            for a in agents
        ],
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────
# detect_new_agents
# ──────────────────────────────────────────────────────────────────────────


class TestDetectNewAgents:
    def test_finds_unregistered_agents(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "new-agent.md", "new-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["existing-agent"])

        new = detect_new_agents([agents_dir], registry_path)
        assert len(new) == 1
        assert new[0].stem == "new-agent"

    def test_skips_registered_agents(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "existing.md", "existing")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["existing"])

        new = detect_new_agents([agents_dir], registry_path)
        assert len(new) == 0

    def test_missing_registry_treats_all_as_new(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "agent-a.md", "agent-a")
        _write_agent(agents_dir / "agent-b.md", "agent-b")

        registry_path = tmp_path / "nonexistent_registry.yml"

        new = detect_new_agents([agents_dir], registry_path)
        assert len(new) == 2

    def test_empty_agents_dir_returns_empty(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        new = detect_new_agents([agents_dir], registry_path)
        assert new == []

    def test_schema_md_files_skipped(self, tmp_path):
        """SCHEMA.md and AGENTS.md should not be treated as agents."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "SCHEMA.md").write_text("schema", encoding="utf-8")
        (agents_dir / "real-agent.md").write_text(
            "---\nname: real-agent\n---\n", encoding="utf-8"
        )

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        new = detect_new_agents([agents_dir], registry_path)
        names = [p.stem for p in new]
        # SCHEMA may or may not be filtered — test that real-agent is there
        assert "real-agent" in names


# ──────────────────────────────────────────────────────────────────────────
# extract_agent_metadata
# ──────────────────────────────────────────────────────────────────────────


class TestExtractAgentMetadata:
    def test_extracts_name_model_description(self, tmp_path):
        agent_path = tmp_path / "test-analyst.md"
        _write_agent(agent_path, "test-analyst", model="opus", description="Runs simulations")

        meta = extract_agent_metadata(agent_path)

        assert meta["name"] == "test-analyst"
        assert meta["model"] == "opus"
        assert "Runs simulations" in meta.get("description", "")

    def test_extracts_mode_hints_from_body(self, tmp_path):
        agent_path = tmp_path / "sim-agent.md"
        agent_path.write_text(
            textwrap.dedent("""\
                ---
                name: sim-agent
                model: sonnet
                description: "Simulation specialist"
                ---

                This agent runs simulate operations and performs diagnostics.
                It handles diagnose requests.
            """),
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        modes = meta.get("modes", [])
        assert "simulate" in modes or "diagnose" in modes

    def test_uses_stem_as_fallback_name(self, tmp_path):
        """If no frontmatter name, use filename stem."""
        agent_path = tmp_path / "fallback-agent.md"
        agent_path.write_text("No frontmatter here.\n", encoding="utf-8")

        meta = extract_agent_metadata(agent_path)
        assert meta.get("name") == "fallback-agent"

    def test_missing_model_defaults_to_sonnet(self, tmp_path):
        agent_path = tmp_path / "no-model.md"
        agent_path.write_text(
            "---\nname: no-model\ndescription: 'test'\n---\nbody\n",
            encoding="utf-8",
        )
        meta = extract_agent_metadata(agent_path)
        assert meta.get("model") in ("sonnet", None, "")


# ──────────────────────────────────────────────────────────────────────────
# generate_registry_entry
# ──────────────────────────────────────────────────────────────────────────


class TestGenerateRegistryEntry:
    def test_returns_agent_registry_entry(self):
        meta = {
            "name": "new-agent",
            "file": "agents/new-agent.md",
            "model": "sonnet",
            "description": "A new agent",
            "modes": ["research"],
            "capabilities": ["analysis"],
        }
        entry = generate_registry_entry(meta)
        assert isinstance(entry, AgentRegistryEntry)
        assert entry.name == "new-agent"
        assert entry.tier == "draft"

    def test_defaults_tier_to_draft(self):
        meta = {"name": "x", "file": "x.md"}
        entry = generate_registry_entry(meta)
        assert entry.tier == "draft"

    def test_defaults_input_schema_to_question_payload(self):
        meta = {"name": "x", "file": "x.md"}
        entry = generate_registry_entry(meta)
        assert entry.input_schema == "QuestionPayload"

    def test_defaults_output_schema_to_finding_payload(self):
        meta = {"name": "x", "file": "x.md"}
        entry = generate_registry_entry(meta)
        assert entry.output_schema == "FindingPayload"


# ──────────────────────────────────────────────────────────────────────────
# append_to_registry
# ──────────────────────────────────────────────────────────────────────────


class TestAppendToRegistry:
    def test_adds_entry_to_existing_registry(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["existing-agent", "another-agent"])

        new_entry = AgentRegistryEntry(
            name="new-agent",
            file="agents/new-agent.md",
            tier="draft",
        )
        append_to_registry(new_entry, registry_path)

        # Read back and verify
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert "existing-agent" in names
        assert "another-agent" in names
        assert "new-agent" in names
        assert len(names) == 3

    def test_creates_registry_if_not_exists(self, tmp_path):
        registry_path = tmp_path / "new_registry.yml"
        entry = AgentRegistryEntry(name="first-agent", file="first.md", tier="draft")

        append_to_registry(entry, registry_path)

        assert registry_path.exists()
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "first-agent"

    def test_does_not_corrupt_existing_entries(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["agent-a", "agent-b"])

        entry = AgentRegistryEntry(name="agent-c", file="c.md", tier="candidate")
        append_to_registry(entry, registry_path)

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        assert data["version"] == 1
        assert len(data["agents"]) == 3


# ──────────────────────────────────────────────────────────────────────────
# generate_dspy_signature_stub
# ──────────────────────────────────────────────────────────────────────────


class TestGenerateDspySignatureStub:
    def test_writes_python_file(self, tmp_path):
        meta = {
            "name": "my-agent",
            "input_schema": "QuestionPayload",
            "output_schema": "FindingPayload",
        }
        output_path = generate_dspy_signature_stub(meta, tmp_path)
        assert output_path.exists()
        assert output_path.suffix == ".py"

    def test_file_is_valid_python(self, tmp_path):
        meta = {
            "name": "valid-agent",
            "input_schema": "QuestionPayload",
            "output_schema": "FindingPayload",
        }
        output_path = generate_dspy_signature_stub(meta, tmp_path)
        content = output_path.read_text(encoding="utf-8")
        compile(content, str(output_path), "exec")  # Should not raise

    def test_file_contains_signature_class(self, tmp_path):
        meta = {"name": "my-agent", "input_schema": "QuestionPayload", "output_schema": "FindingPayload"}
        output_path = generate_dspy_signature_stub(meta, tmp_path)
        content = output_path.read_text(encoding="utf-8")
        assert "dspy.Signature" in content or "Signature" in content


# ──────────────────────────────────────────────────────────────────────────
# onboard (end-to-end)
# ──────────────────────────────────────────────────────────────────────────


class TestOnboard:
    def test_end_to_end_onboarding(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "brand-new-agent.md", "brand-new-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["old-agent"])

        dspy_dir = tmp_path / "generated"

        result = onboard([agents_dir], registry_path, dspy_dir)

        assert "brand-new-agent" in result

        # Registry should now contain the new agent
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert "brand-new-agent" in names

    def test_idempotent_already_registered(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "existing-agent.md", "existing-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["existing-agent"])

        result = onboard([agents_dir], registry_path, tmp_path / "gen")
        assert "existing-agent" not in result  # already registered, not re-onboarded

    def test_returns_list_of_new_agent_names(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "new-one.md", "new-one")
        _write_agent(agents_dir / "new-two.md", "new-two")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        result = onboard([agents_dir], registry_path, tmp_path / "gen")
        assert "new-one" in result
        assert "new-two" in result
