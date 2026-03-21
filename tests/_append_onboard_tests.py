"""Helper script to append new tests to test_onboard_agent.py."""

from pathlib import Path

new_tests = """

# ------------------------------------------------------------------
# No keyword inference — frontmatter fields read directly
# ------------------------------------------------------------------


class TestNoKeywordInference:
    def test_modes_from_frontmatter_only(self, tmp_path):
        agent_path = tmp_path / "pure-frontmatter.md"
        agent_path.write_text(
            "---\\n"
            "name: pure-frontmatter\\n"
            "model: sonnet\\n"
            "description: A focused agent\\n"
            "modes:\\n"
            "  - research\\n"
            "capabilities:\\n"
            "  - analysis\\n"
            "---\\n"
            "\\n"
            "This agent diagnoses simulates synthesizes audits fixes plans.\\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["modes"] == ["research"]

    def test_empty_modes_when_not_in_frontmatter(self, tmp_path):
        agent_path = tmp_path / "no-modes.md"
        agent_path.write_text(
            "---\\n"
            "name: no-modes\\n"
            "model: sonnet\\n"
            "description: No modes declared\\n"
            "---\\n"
            "\\n"
            "This agent simulates, diagnoses, researches, audits, synthesizes.\\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["modes"] == []

    def test_capabilities_from_frontmatter_only(self, tmp_path):
        agent_path = tmp_path / "cap-agent.md"
        agent_path.write_text(
            "---\\n"
            "name: cap-agent\\n"
            "model: haiku\\n"
            "description: Capability test\\n"
            "capabilities:\\n"
            "  - sweep\\n"
            "  - benchmark\\n"
            "---\\n"
            "body text\\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta["capabilities"] == ["sweep", "benchmark"]

    def test_input_output_schema_from_frontmatter(self, tmp_path):
        agent_path = tmp_path / "schema-agent.md"
        agent_path.write_text(
            "---\\n"
            "name: schema-agent\\n"
            "model: sonnet\\n"
            "description: Schema test\\n"
            "input_schema: DiagnosePayload\\n"
            "output_schema: DiagnosisPayload\\n"
            "---\\n"
            "body\\n",
            encoding="utf-8",
        )

        meta = extract_agent_metadata(agent_path)
        assert meta.get("input_schema") == "DiagnosePayload"
        assert meta.get("output_schema") == "DiagnosisPayload"

    def test_tier_from_frontmatter(self, tmp_path):
        agent_path = tmp_path / "trusted-agent.md"
        agent_path.write_text(
            "---\\n"
            "name: trusted-agent\\n"
            "model: opus\\n"
            "description: Trusted agent\\n"
            "tier: trusted\\n"
            "---\\n"
            "body\\n",
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

        entry = AgentRegistryEntry(name="agent-b", file="agents/agent-b.md", tier="draft")
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

        entry = AgentRegistryEntry(name="stable-agent", file="agents/stable-agent.md", tier="draft")
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
"""

target = Path("tests/test_onboard_agent.py")
current = target.read_text(encoding="utf-8")
target.write_text(current + new_tests, encoding="utf-8")
print("Appended successfully")
