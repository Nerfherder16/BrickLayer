"""Tests for masonry/mcp_server/tools/fleet.py."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from masonry.mcp_server.tools.fleet import (
    _tool_masonry_fleet,
    _tool_masonry_recall_search,
    _tool_masonry_optimization_status,
)


class TestMasonryFleet:
    def test_returns_agents_list(self, tmp_path):
        registry = {"agents": [{"name": "rough-in", "tier": "trusted"}]}
        (tmp_path / "registry.json").write_text(json.dumps(registry))
        result = _tool_masonry_fleet({"project_dir": str(tmp_path)})
        assert len(result["agents"]) == 1
        assert result["agents"][0]["name"] == "rough-in"

    def test_merges_scores_from_agent_db(self, tmp_path):
        (tmp_path / "registry.json").write_text(json.dumps({"agents": [{"name": "karen"}]}))
        (tmp_path / "agent_db.json").write_text(json.dumps({"karen": {"score": 0.9}}))
        result = _tool_masonry_fleet({"project_dir": str(tmp_path)})
        assert result["agents"][0]["score"] == 0.9
        assert result["has_scores"] is True

    def test_empty_dir_returns_empty_list(self, tmp_path):
        result = _tool_masonry_fleet({"project_dir": str(tmp_path)})
        assert result["agents"] == []
        assert result["count"] == 0

    def test_limit_respected(self, tmp_path):
        agents = [{"name": f"agent-{i}"} for i in range(10)]
        (tmp_path / "registry.json").write_text(json.dumps({"agents": agents}))
        result = _tool_masonry_fleet({"project_dir": str(tmp_path), "limit": 3})
        assert len(result["agents"]) == 3


class TestMasonryRecallSearch:
    def test_missing_query_returns_error(self):
        result = _tool_masonry_recall_search({})
        assert "error" in result

    def test_success_returns_results(self):
        with patch("bl.recall_bridge.search_prior_findings", return_value=[{"id": "1", "text": "finding"}]):
            result = _tool_masonry_recall_search({"query": "test query"})
        assert result["count"] == 1
        assert len(result["results"]) == 1

    def test_exception_returns_error(self):
        with patch("bl.recall_bridge.search_prior_findings", side_effect=Exception("recall down")):
            result = _tool_masonry_recall_search({"query": "test"})
        assert "error" in result


class TestMasonryOptimizationStatus:
    def test_missing_dir_returns_empty(self, tmp_path):
        result = _tool_masonry_optimization_status({"optimized_dir": str(tmp_path / "nonexistent")})
        assert result == {"agents": [], "count": 0}

    def test_reads_json_files(self, tmp_path):
        (tmp_path / "karen.json").write_text(json.dumps({"score": 0.85}))
        (tmp_path / "mortar.json").write_text(json.dumps({"score": 0.72}))
        result = _tool_masonry_optimization_status({"optimized_dir": str(tmp_path)})
        assert result["count"] == 2
        names = {a["agent"] for a in result["agents"]}
        assert "karen" in names
        assert "mortar" in names
