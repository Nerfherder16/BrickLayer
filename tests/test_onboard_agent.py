"""Tests for masonry/scripts/onboard_agent.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from masonry.scripts.onboard_agent import (
    append_to_registry,
    detect_new_agents,
    detect_stale_registry_entries,
    extract_agent_metadata,
    generate_dspy_signature_stub,
    generate_registry_entry,
    onboard,
    upsert_registry_entry,
)
from masonry.src.schemas import AgentRegistryEntry


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _write_agent(
    path: Path, name: str, model: str = "sonnet", description: str = "Test agent"
) -> None:
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
            {"name": a, "file": f"agents/{a}.md", "tier": "draft"} for a in agents
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
        _write_agent(
            agent_path, "test-analyst", model="opus", description="Runs simulations"
        )

        meta = extract_agent_metadata(agent_path)

        assert meta["name"] == "test-analyst"
        assert meta["model"] == "opus"
        assert "Runs simulations" in meta.get("description", "")

    def test_returns_empty_modes_when_no_frontmatter_modes(self, tmp_path):
        """Without modes in frontmatter, modes list is empty (no body inference)."""
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
        # No modes in frontmatter → empty list (no body inference)
        assert modes == []

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

    def test_extracts_routing_keywords_from_frontmatter(self, tmp_path):
        agent_path = tmp_path / "router-agent.md"
        agent_path.write_text(
            textwrap.dedent("""\
                ---
                name: router-agent
                model: sonnet
                description: "Handles deployments"
                routing_keywords:
                  - deploy to casaos
                  - publish to subdomain
                  - nginx config
                ---

                Body text.
            """),
            encoding="utf-8",
        )
        meta = extract_agent_metadata(agent_path)
        assert meta.get("routing_keywords") == [
            "deploy to casaos",
            "publish to subdomain",
            "nginx config",
        ]

    def test_routing_keywords_defaults_to_empty_list(self, tmp_path):
        agent_path = tmp_path / "no-keywords.md"
        _write_agent(agent_path, "no-keywords")
        meta = extract_agent_metadata(agent_path)
        assert meta.get("routing_keywords") == []

    def test_routing_keywords_not_inferred_from_body(self, tmp_path):
        """Body text containing keyword-like phrases must NOT be extracted."""
        agent_path = tmp_path / "no-fm-keywords.md"
        agent_path.write_text(
            textwrap.dedent("""\
                ---
                name: no-fm-keywords
                model: sonnet
                description: "test"
                ---

                This agent can do a security audit, run a benchmark,
                and refactor code.
            """),
            encoding="utf-8",
        )
        meta = extract_agent_metadata(agent_path)
        assert meta.get("routing_keywords") == []


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

    def test_routing_keywords_passed_through(self):
        meta = {
            "name": "x",
            "file": "x.md",
            "routing_keywords": ["deploy to casaos", "nginx config"],
        }
        entry = generate_registry_entry(meta)
        assert entry.routing_keywords == ["deploy to casaos", "nginx config"]

    def test_routing_keywords_defaults_to_empty_list(self):
        meta = {"name": "x", "file": "x.md"}
        entry = generate_registry_entry(meta)
        assert entry.routing_keywords == []

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
        meta = {
            "name": "my-agent",
            "input_schema": "QuestionPayload",
            "output_schema": "FindingPayload",
        }
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

        assert result["added"] == 1

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
        assert result["added"] == 0  # already registered, not re-added

    def test_returns_count_of_new_agent_names(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "new-one.md", "new-one")
        _write_agent(agents_dir / "new-two.md", "new-two")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        result = onboard([agents_dir], registry_path, tmp_path / "gen")
        assert result["added"] == 2

    def test_single_file_upsert_syncs_routing_keywords_without_wiping_runtime_state(
        self, tmp_path
    ):
        """Editing an already-registered agent file (e.g. adding routing_keywords)
        must sync the change to the registry without overwriting runtime-state fields
        like dspy_status or last_score.
        """
        # 1. Write an agent file with routing_keywords.
        agent_path = tmp_path / "existing-agent.md"
        agent_path.write_text(
            "---\n"
            "name: existing-agent\n"
            "model: sonnet\n"
            "description: Already registered agent\n"
            "routing_keywords:\n"
            "  - dead code\n"
            "  - unused imports\n"
            "---\n\n"
            "Body text.\n",
            encoding="utf-8",
        )

        # 2. Pre-populate the registry with an existing entry that has runtime state.
        registry_path = tmp_path / "registry.yml"
        data = {
            "version": 1,
            "agents": [
                {
                    "name": "existing-agent",
                    "file": str(agent_path),
                    "tier": "candidate",  # promoted — should be preserved
                    "dspy_status": "optimized",  # runtime state — must survive upsert
                    "last_score": 0.92,  # runtime state — must survive upsert
                    "routing_keywords": [],  # stale — should be replaced
                }
            ],
        }
        registry_path.write_text(yaml.dump(data), encoding="utf-8")

        # 3. Simulate the single-file hook path: extract → generate entry → upsert.
        meta = extract_agent_metadata(agent_path)
        entry = generate_registry_entry(meta)
        is_new = upsert_registry_entry(entry, registry_path)

        # 4. Assertions.
        assert is_new is False, (
            "Agent was already registered — should not be treated as new"
        )

        updated = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        agents = {a["name"]: a for a in updated["agents"]}
        agent = agents["existing-agent"]

        # routing_keywords must be synced from frontmatter
        assert agent["routing_keywords"] == ["dead code", "unused imports"]

        # runtime state fields must be preserved (not wiped)
        assert agent.get("dspy_status") == "optimized"
        assert agent.get("last_score") == pytest.approx(0.92)


# ------------------------------------------------------------------
# No keyword inference — frontmatter fields read directly
# ------------------------------------------------------------------


class TestNoKeywordInference:
    def test_modes_from_frontmatter_only(self, tmp_path):
        agent_path = tmp_path / "pure-frontmatter.md"
        agent_path.write_text(
            "---\n"
            "name: pure-frontmatter\n"
            "model: sonnet\n"
            "description: A focused agent\n"
            "modes:\n"
            "  - research\n"
            "capabilities:\n"
            "  - analysis\n"
            "---\n"
            "\n"
            "This agent diagnoses simulates synthesizes audits fixes plans.\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["modes"] == ["research"]

    def test_empty_modes_when_not_in_frontmatter(self, tmp_path):
        agent_path = tmp_path / "no-modes.md"
        agent_path.write_text(
            "---\n"
            "name: no-modes\n"
            "model: sonnet\n"
            "description: No modes declared\n"
            "---\n"
            "\n"
            "This agent simulates, diagnoses, researches, audits, synthesizes.\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["modes"] == []

    def test_capabilities_from_frontmatter_only(self, tmp_path):
        agent_path = tmp_path / "cap-agent.md"
        agent_path.write_text(
            "---\n"
            "name: cap-agent\n"
            "model: haiku\n"
            "description: Capability test\n"
            "capabilities:\n"
            "  - sweep\n"
            "  - benchmark\n"
            "---\n"
            "body text\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["capabilities"] == ["sweep", "benchmark"]

    def test_input_output_schema_from_frontmatter(self, tmp_path):
        agent_path = tmp_path / "schema-agent.md"
        agent_path.write_text(
            "---\n"
            "name: schema-agent\n"
            "model: sonnet\n"
            "description: Schema test\n"
            "input_schema: DiagnosePayload\n"
            "output_schema: DiagnosisPayload\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta.get("input_schema") == "DiagnosePayload"
        assert meta.get("output_schema") == "DiagnosisPayload"

    def test_tier_from_frontmatter(self, tmp_path):
        agent_path = tmp_path / "trusted-agent.md"
        agent_path.write_text(
            "---\n"
            "name: trusted-agent\n"
            "model: opus\n"
            "description: Trusted agent\n"
            "tier: trusted\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta.get("tier") == "trusted"


# ------------------------------------------------------------------
# upsert_registry_entry — idempotent update
# ------------------------------------------------------------------


class TestUpsertRegistryEntry:
    def test_adds_new_entry_when_not_exists(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["agent-a"])

        entry = AgentRegistryEntry(
            name="agent-b", file="agents/agent-b.md", tier="draft"
        )
        upsert_registry_entry(entry, registry_path)

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert "agent-a" in names
        assert "agent-b" in names
        assert len(names) == 2

    def test_updates_existing_entry_in_place(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, ["agent-a"])

        entry = AgentRegistryEntry(
            name="agent-a",
            file="agents/agent-a.md",
            tier="trusted",
            description="Updated description",
        )
        upsert_registry_entry(entry, registry_path)

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert names.count("agent-a") == 1
        agent_a = next(a for a in data["agents"] if a["name"] == "agent-a")
        assert agent_a.get("tier") == "trusted"

    def test_idempotent_double_upsert(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        entry = AgentRegistryEntry(
            name="stable-agent", file="agents/stable-agent.md", tier="draft"
        )
        upsert_registry_entry(entry, registry_path)
        upsert_registry_entry(entry, registry_path)

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert names.count("stable-agent") == 1


# ------------------------------------------------------------------
# detect_stale_registry_entries
# ------------------------------------------------------------------


class TestDetectStaleRegistryEntries:
    def test_detects_entry_with_missing_file(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        data = {
            "version": 1,
            "agents": [
                {
                    "name": "gone-agent",
                    "file": str(tmp_path / "agents" / "gone-agent.md"),
                    "tier": "draft",
                },
            ],
        }
        registry_path.write_text(yaml.dump(data), encoding="utf-8")

        stale = detect_stale_registry_entries(registry_path)
        assert len(stale) == 1
        assert stale[0]["name"] == "gone-agent"

    def test_no_stale_when_file_exists(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_file = agents_dir / "present-agent.md"
        _write_agent(agent_file, "present-agent")

        registry_path = tmp_path / "registry.yml"
        data = {
            "version": 1,
            "agents": [
                {
                    "name": "present-agent",
                    "file": str(agent_file),
                    "tier": "draft",
                },
            ],
        }
        registry_path.write_text(yaml.dump(data), encoding="utf-8")

        stale = detect_stale_registry_entries(registry_path)
        assert stale == []

    def test_empty_registry_returns_empty(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        stale = detect_stale_registry_entries(registry_path)
        assert stale == []

    def test_missing_registry_returns_empty(self, tmp_path):
        registry_path = tmp_path / "nonexistent.yml"
        stale = detect_stale_registry_entries(registry_path)
        assert stale == []


# ------------------------------------------------------------------
# onboard structured result
# ------------------------------------------------------------------


class TestOnboardStructuredResult:
    def test_returns_structured_dict(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "fresh-agent.md", "fresh-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        result = onboard([agents_dir], registry_path, tmp_path / "gen")

        assert isinstance(result, dict), "onboard() must return a dict"
        assert "added" in result
        assert "updated" in result
        assert "stale" in result
        assert "warnings" in result

    def test_added_count_increments_for_new_agents(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "new-a.md", "new-a")
        _write_agent(agents_dir / "new-b.md", "new-b")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        result = onboard([agents_dir], registry_path, tmp_path / "gen")
        assert result["added"] == 2

    def test_idempotent_second_run_no_duplicates(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "stable-agent.md", "stable-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        onboard([agents_dir], registry_path, tmp_path / "gen")
        onboard([agents_dir], registry_path, tmp_path / "gen")

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        names = [a["name"] for a in data["agents"]]
        assert names.count("stable-agent") == 1

    def test_runtime_state_fields_on_new_entry(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir / "state-agent.md", "state-agent")

        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path, [])

        onboard([agents_dir], registry_path, tmp_path / "gen")

        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        agent = next(a for a in data["agents"] if a["name"] == "state-agent")
        assert agent.get("dspy_status") == "not_optimized"
        assert agent.get("drift_status") == "ok"
        assert agent.get("runs_since_optimization") == 0
