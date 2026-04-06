"""Tests for masonry/src/schemas/registry_loader.py — load_registry and get_agents_for_mode."""

from __future__ import annotations

import pytest
import yaml

from masonry.src.schemas.registry_loader import get_agents_for_mode, load_registry
from masonry.src.schemas.payloads import AgentRegistryEntry


def _write_registry(tmp_path, agents: list[dict]) -> object:
    path = tmp_path / "agent_registry.yml"
    path.write_text(yaml.dump({"version": 1, "agents": agents}), encoding="utf-8")
    return path


class TestLoadRegistry:
    def test_returns_list_of_entries(self, tmp_path):
        path = _write_registry(tmp_path, [{"name": "rough-in", "tier": "trusted"}])
        result = load_registry(path)
        assert len(result) == 1
        assert result[0].name == "rough-in"
        assert result[0].tier == "trusted"

    def test_sets_defaults_for_missing_fields(self, tmp_path):
        path = _write_registry(tmp_path, [{"name": "minimal"}])
        result = load_registry(path)
        entry = result[0]
        assert entry.file == ""
        assert entry.description == ""
        assert entry.capabilities == []
        assert entry.modes == []
        assert entry.tier == "standard"
        assert entry.routing_keywords == []
        assert entry.model is None

    def test_parses_all_fields(self, tmp_path):
        path = _write_registry(tmp_path, [{
            "name": "karen",
            "file": ".claude/agents/karen.md",
            "description": "Doc agent",
            "capabilities": ["docs", "audit"],
            "modes": ["research", "audit"],
            "tier": "trusted",
            "routing_keywords": ["changelog", "docs"],
            "model": "sonnet",
        }])
        result = load_registry(path)
        entry = result[0]
        assert entry.name == "karen"
        assert entry.file == ".claude/agents/karen.md"
        assert entry.capabilities == ["docs", "audit"]
        assert entry.modes == ["research", "audit"]
        assert entry.routing_keywords == ["changelog", "docs"]
        assert entry.model == "sonnet"

    def test_empty_agents_list(self, tmp_path):
        path = tmp_path / "agent_registry.yml"
        path.write_text(yaml.dump({"version": 1, "agents": []}), encoding="utf-8")
        result = load_registry(path)
        assert result == []

    def test_multiple_agents(self, tmp_path):
        path = _write_registry(tmp_path, [
            {"name": "alpha"},
            {"name": "beta"},
            {"name": "gamma"},
        ])
        result = load_registry(path)
        assert len(result) == 3
        names = [e.name for e in result]
        assert "alpha" in names
        assert "gamma" in names


class TestGetAgentsForMode:
    def test_filters_by_mode(self):
        agents = [
            AgentRegistryEntry(name="a", modes=["research"]),
            AgentRegistryEntry(name="b", modes=["audit"]),
            AgentRegistryEntry(name="c", modes=["research", "audit"]),
        ]
        result = get_agents_for_mode(agents, "research")
        assert len(result) == 2
        assert {e.name for e in result} == {"a", "c"}

    def test_no_match_returns_empty(self):
        agents = [AgentRegistryEntry(name="x", modes=["research"])]
        result = get_agents_for_mode(agents, "frontier")
        assert result == []

    def test_empty_registry_returns_empty(self):
        result = get_agents_for_mode([], "research")
        assert result == []
