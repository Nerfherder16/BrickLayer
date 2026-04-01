"""Tests for the 5 new MCP server tools in masonry/mcp_server/server.py:
    masonry_route, masonry_optimization_status, masonry_onboard,
    masonry_drift_check, masonry_registry_list
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Helpers to import tool functions
# ---------------------------------------------------------------------------

from masonry.mcp_server.server import TOOLS


def _call(tool_name: str, args: dict) -> dict:
    spec = TOOLS[tool_name]
    return spec["fn"](args)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_registry(path: Path, agents: list[dict] | None = None) -> None:
    data = {
        "version": 1,
        "agents": agents
        or [
            {
                "name": "quantitative-analyst",
                "file": "agents/quantitative-analyst.md",
                "model": "sonnet",
                "description": "Runs simulations",
                "modes": ["simulate"],
                "capabilities": ["simulate"],
                "input_schema": "QuestionPayload",
                "output_schema": "FindingPayload",
                "tier": "trusted",
            },
            {
                "name": "fix-agent",
                "file": "agents/fix-agent.md",
                "model": "sonnet",
                "description": "Fixes issues",
                "modes": ["fix"],
                "capabilities": ["fix"],
                "input_schema": "QuestionPayload",
                "output_schema": "FindingPayload",
                "tier": "candidate",
            },
        ],
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def _write_agent_db(path: Path, agents: dict) -> None:
    path.write_text(json.dumps(agents), encoding="utf-8")


def _write_optimized_prompt(dir_path: Path, agent_name: str, score: float) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    data = {
        "agent": agent_name,
        "score": score,
        "optimized_at": "2026-01-01T00:00:00+00:00",
    }
    (dir_path / f"{agent_name}.json").write_text(json.dumps(data), encoding="utf-8")


def _write_agent_md(path: Path, name: str) -> None:
    path.write_text(
        textwrap.dedent(f"""\
            ---
            name: {name}
            model: sonnet
            description: "Test agent for {name}"
            ---

            This agent runs research and analysis.
        """),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# masonry_route
# ---------------------------------------------------------------------------


class TestMasonryRoute:
    def test_tool_exists(self):
        assert "masonry_route" in TOOLS

    def test_returns_routing_decision(self, tmp_path):
        _write_registry(tmp_path / "masonry" / "agent_registry.yml".split("/")[0] / "agent_registry.yml".split("/")[1]
                        if False else (tmp_path / "masonry").mkdir() or tmp_path / "masonry" / "agent_registry.yml",
                        None)
        # Use a simpler approach:
        registry_dir = tmp_path / "masonry"
        registry_dir.mkdir(exist_ok=True)
        _write_registry(registry_dir / "agent_registry.yml")

        result = _call("masonry_route", {
            "request_text": "/simulate what happens if revenue drops",
            "project_dir": str(tmp_path),
        })

        assert "target_agent" in result
        assert "layer" in result
        assert "confidence" in result

    def test_slash_command_routes_deterministically(self, tmp_path):
        registry_dir = tmp_path / "masonry"
        registry_dir.mkdir(exist_ok=True)
        _write_registry(registry_dir / "agent_registry.yml")

        result = _call("masonry_route", {
            "request_text": "/build implement the feature",
            "project_dir": str(tmp_path),
        })

        assert result["layer"] == "deterministic"
        assert result["confidence"] == 1.0

    def test_missing_request_text_returns_error(self, tmp_path):
        result = _call("masonry_route", {"project_dir": str(tmp_path)})
        assert "error" in result

    def test_returns_fallback_on_no_match(self, tmp_path):
        """When no routing signal is found, returns a valid decision (layer 4 fallback)."""
        registry_dir = tmp_path / "masonry"
        registry_dir.mkdir(exist_ok=True)
        _write_registry(registry_dir / "agent_registry.yml")

        result = _call("masonry_route", {
            "request_text": "xyzzy nothing happens abcde gibberish 12345",
            "project_dir": str(tmp_path),
        })

        # Should always return a valid response (layer 1-4)
        assert "target_agent" in result
        assert "confidence" in result


# ---------------------------------------------------------------------------
# masonry_optimization_status
# ---------------------------------------------------------------------------


class TestMasonryOptimizationStatus:
    def test_tool_exists(self):
        assert "masonry_optimization_status" in TOOLS

    def test_returns_agent_scores(self, tmp_path):
        _write_optimized_prompt(tmp_path / "optimized", "quantitative-analyst", 0.87)
        _write_optimized_prompt(tmp_path / "optimized", "fix-agent", 0.72)

        result = _call("masonry_optimization_status", {
            "optimized_dir": str(tmp_path / "optimized"),
        })

        assert "agents" in result
        names = [a["agent"] for a in result["agents"]]
        assert "quantitative-analyst" in names
        assert "fix-agent" in names

    def test_empty_dir_returns_empty_list(self, tmp_path):
        optimized_dir = tmp_path / "optimized"
        optimized_dir.mkdir()

        result = _call("masonry_optimization_status", {
            "optimized_dir": str(optimized_dir),
        })

        assert result["agents"] == []
        assert result["count"] == 0

    def test_missing_dir_returns_empty(self, tmp_path):
        result = _call("masonry_optimization_status", {
            "optimized_dir": str(tmp_path / "nonexistent"),
        })

        assert result["count"] == 0

    def test_scores_included_in_response(self, tmp_path):
        _write_optimized_prompt(tmp_path / "optimized", "my-agent", 0.91)

        result = _call("masonry_optimization_status", {
            "optimized_dir": str(tmp_path / "optimized"),
        })

        entry = next(a for a in result["agents"] if a["agent"] == "my-agent")
        assert entry["score"] == 0.91


# ---------------------------------------------------------------------------
# masonry_onboard
# ---------------------------------------------------------------------------


class TestMasonryOnboard:
    def test_tool_exists(self):
        assert "masonry_onboard" in TOOLS

    def test_onboards_new_agent(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent_md(agents_dir / "new-agent.md", "new-agent")

        registry_path = tmp_path / "registry.yml"
        registry_path.write_text(yaml.dump({"version": 1, "agents": []}), encoding="utf-8")

        dspy_dir = tmp_path / "generated"

        result = _call("masonry_onboard", {
            "agents_dirs": [str(agents_dir)],
            "registry_path": str(registry_path),
            "dspy_output_dir": str(dspy_dir),
        })

        assert "onboarded" in result
        assert "new-agent" in result["onboarded"]

    def test_idempotent_on_existing_agent(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent_md(agents_dir / "existing.md", "existing")

        registry_path = tmp_path / "registry.yml"
        registry_path.write_text(
            yaml.dump({"version": 1, "agents": [{"name": "existing", "file": "existing.md"}]}),
            encoding="utf-8",
        )

        result = _call("masonry_onboard", {
            "agents_dirs": [str(agents_dir)],
            "registry_path": str(registry_path),
            "dspy_output_dir": str(tmp_path / "gen"),
        })

        assert result["onboarded"] == []

    def test_returns_count(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent_md(agents_dir / "agent-a.md", "agent-a")
        _write_agent_md(agents_dir / "agent-b.md", "agent-b")

        registry_path = tmp_path / "registry.yml"
        registry_path.write_text(yaml.dump({"version": 1, "agents": []}), encoding="utf-8")

        result = _call("masonry_onboard", {
            "agents_dirs": [str(agents_dir)],
            "registry_path": str(registry_path),
            "dspy_output_dir": str(tmp_path / "gen"),
        })

        assert result["count"] == 2


# ---------------------------------------------------------------------------
# masonry_drift_check
# ---------------------------------------------------------------------------


class TestMasonryDriftCheck:
    def test_tool_exists(self):
        assert "masonry_drift_check" in TOOLS

    def test_returns_drift_reports(self, tmp_path):
        agent_db = {
            "quantitative-analyst": {
                "score": 0.9,
                "verdicts": ["HEALTHY", "WARNING", "HEALTHY"],
            },
        }
        db_path = tmp_path / "agent_db.json"
        _write_agent_db(db_path, agent_db)

        registry_path = tmp_path / "masonry" / "agent_registry.yml"
        registry_path.parent.mkdir(parents=True)
        _write_registry(registry_path)

        result = _call("masonry_drift_check", {
            "agent_db_path": str(db_path),
            "registry_path": str(registry_path),
        })

        assert "reports" in result
        assert len(result["reports"]) >= 1
        report = result["reports"][0]
        assert "agent_name" in report
        assert "alert_level" in report
        assert "drift_pct" in report

    def test_empty_agent_db_returns_empty_reports(self, tmp_path):
        db_path = tmp_path / "agent_db.json"
        _write_agent_db(db_path, {})

        registry_path = tmp_path / "masonry" / "agent_registry.yml"
        registry_path.parent.mkdir(parents=True)
        _write_registry(registry_path)

        result = _call("masonry_drift_check", {
            "agent_db_path": str(db_path),
            "registry_path": str(registry_path),
        })

        assert result["reports"] == []

    def test_missing_agent_db_returns_error(self, tmp_path):
        registry_path = tmp_path / "masonry" / "agent_registry.yml"
        registry_path.parent.mkdir(parents=True)
        _write_registry(registry_path)

        result = _call("masonry_drift_check", {
            "agent_db_path": str(tmp_path / "nonexistent.json"),
            "registry_path": str(registry_path),
        })

        # Either error key or empty reports — implementation may differ
        assert "error" in result or result.get("reports") == []

    def test_critical_drift_flagged(self, tmp_path):
        agent_db = {
            "quantitative-analyst": {
                "score": 1.0,  # baseline
                "verdicts": ["FAILURE", "FAILURE", "FAILURE", "FAILURE"],
            },
        }
        db_path = tmp_path / "agent_db.json"
        _write_agent_db(db_path, agent_db)

        registry_path = tmp_path / "masonry" / "agent_registry.yml"
        registry_path.parent.mkdir(parents=True)
        _write_registry(registry_path)

        result = _call("masonry_drift_check", {
            "agent_db_path": str(db_path),
            "registry_path": str(registry_path),
        })

        report = next(
            (r for r in result["reports"] if r["agent_name"] == "quantitative-analyst"),
            None,
        )
        assert report is not None
        assert report["alert_level"] == "critical"


# ---------------------------------------------------------------------------
# masonry_registry_list
# ---------------------------------------------------------------------------


class TestMasonryRegistryList:
    def test_tool_exists(self):
        assert "masonry_registry_list" in TOOLS

    def test_returns_all_agents(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path)

        result = _call("masonry_registry_list", {
            "registry_path": str(registry_path),
        })

        assert "agents" in result
        assert result["count"] == 2
        names = [a["name"] for a in result["agents"]]
        assert "quantitative-analyst" in names
        assert "fix-agent" in names

    def test_filter_by_tier(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path)

        result = _call("masonry_registry_list", {
            "registry_path": str(registry_path),
            "tier": "trusted",
        })

        assert result["count"] == 1
        assert result["agents"][0]["name"] == "quantitative-analyst"

    def test_filter_by_mode(self, tmp_path):
        registry_path = tmp_path / "registry.yml"
        _write_registry(registry_path)

        result = _call("masonry_registry_list", {
            "registry_path": str(registry_path),
            "mode": "fix",
        })

        assert result["count"] == 1
        assert result["agents"][0]["name"] == "fix-agent"

    def test_missing_registry_returns_empty(self, tmp_path):
        result = _call("masonry_registry_list", {
            "registry_path": str(tmp_path / "nonexistent.yml"),
        })

        assert result["agents"] == []
        assert result["count"] == 0

    def test_default_registry_path_used(self, tmp_path):
        """When no registry_path given, falls back to masonry/agent_registry.yml."""
        # This is a best-effort test — just verify no exception raised
        result = _call("masonry_registry_list", {})
        assert "agents" in result
        assert "count" in result
