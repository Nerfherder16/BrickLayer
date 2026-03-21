"""Tests for masonry/src/schemas/registry_loader.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from masonry.src.schemas.registry_loader import (
    get_agent_by_name,
    get_agents_for_mode,
    load_registry,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_REGISTRY = FIXTURES_DIR / "test_registry.yml"


# ──────────────────────────────────────────────────────────────────────────
# load_registry
# ──────────────────────────────────────────────────────────────────────────


class TestLoadRegistry:
    def test_loads_all_valid_agents(self):
        agents = load_registry(TEST_REGISTRY)
        assert len(agents) == 3

    def test_returns_agent_registry_entry_objects(self):
        from masonry.src.schemas import AgentRegistryEntry

        agents = load_registry(TEST_REGISTRY)
        for a in agents:
            assert isinstance(a, AgentRegistryEntry)

    def test_first_agent_has_correct_fields(self):
        agents = load_registry(TEST_REGISTRY)
        qa = next(a for a in agents if a.name == "quantitative-analyst")
        assert qa.model == "sonnet"
        assert qa.tier == "trusted"
        assert "simulate" in qa.modes
        assert "simulation" in qa.capabilities

    def test_nonexistent_file_returns_empty_list(self):
        agents = load_registry(Path("/does/not/exist/registry.yml"))
        assert agents == []

    def test_invalid_tier_entry_is_skipped(self, tmp_path):
        """An entry with invalid tier should be skipped, not crash."""
        bad_registry = tmp_path / "bad_registry.yml"
        bad_registry.write_text(
            textwrap.dedent("""\
                version: 1
                agents:
                  - name: valid-agent
                    file: agents/valid.md
                    model: sonnet
                    tier: trusted

                  - name: invalid-agent
                    file: agents/invalid.md
                    model: sonnet
                    tier: active_is_invalid
            """),
            encoding="utf-8",
        )
        agents = load_registry(bad_registry)
        assert len(agents) == 1
        assert agents[0].name == "valid-agent"

    def test_empty_agents_list(self, tmp_path):
        empty_registry = tmp_path / "empty.yml"
        empty_registry.write_text("version: 1\nagents: []\n", encoding="utf-8")
        agents = load_registry(empty_registry)
        assert agents == []

    def test_all_three_agents_loaded(self):
        agents = load_registry(TEST_REGISTRY)
        names = {a.name for a in agents}
        assert "quantitative-analyst" in names
        assert "fix-agent" in names
        assert "peer-reviewer" in names


# ──────────────────────────────────────────────────────────────────────────
# get_agents_for_mode
# ──────────────────────────────────────────────────────────────────────────


class TestGetAgentsForMode:
    def test_simulate_returns_quantitative_analyst(self):
        agents = load_registry(TEST_REGISTRY)
        results = get_agents_for_mode(agents, "simulate")
        assert len(results) == 1
        assert results[0].name == "quantitative-analyst"

    def test_fix_returns_fix_agent(self):
        agents = load_registry(TEST_REGISTRY)
        results = get_agents_for_mode(agents, "fix")
        assert len(results) == 1
        assert results[0].name == "fix-agent"

    def test_unknown_mode_returns_empty(self):
        agents = load_registry(TEST_REGISTRY)
        results = get_agents_for_mode(agents, "nonexistent_mode")
        assert results == []

    def test_empty_registry_returns_empty(self):
        results = get_agents_for_mode([], "simulate")
        assert results == []

    def test_mode_with_multiple_agents(self, tmp_path):
        """Two agents sharing same mode should both be returned."""
        registry_file = tmp_path / "multi.yml"
        registry_file.write_text(
            textwrap.dedent("""\
                version: 1
                agents:
                  - name: agent-a
                    file: a.md
                    modes: [research]
                    tier: draft
                  - name: agent-b
                    file: b.md
                    modes: [research]
                    tier: draft
            """),
            encoding="utf-8",
        )
        agents = load_registry(registry_file)
        results = get_agents_for_mode(agents, "research")
        assert len(results) == 2


# ──────────────────────────────────────────────────────────────────────────
# get_agent_by_name
# ──────────────────────────────────────────────────────────────────────────


class TestGetAgentByName:
    def test_returns_correct_agent(self):
        agents = load_registry(TEST_REGISTRY)
        result = get_agent_by_name(agents, "quantitative-analyst")
        assert result is not None
        assert result.name == "quantitative-analyst"
        assert result.tier == "trusted"

    def test_nonexistent_name_returns_none(self):
        agents = load_registry(TEST_REGISTRY)
        result = get_agent_by_name(agents, "nonexistent-agent")
        assert result is None

    def test_empty_registry_returns_none(self):
        result = get_agent_by_name([], "anything")
        assert result is None

    def test_partial_name_does_not_match(self):
        agents = load_registry(TEST_REGISTRY)
        result = get_agent_by_name(agents, "quantitative")
        assert result is None

    def test_case_sensitive_match(self):
        agents = load_registry(TEST_REGISTRY)
        result = get_agent_by_name(agents, "Quantitative-Analyst")
        assert result is None
