"""Tests for optimize_routing.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def sample_agent_dir(tmp_path: Path) -> Path:
    d = tmp_path / "agents"
    d.mkdir()
    agent = d / "test-analyst.md"
    agent.write_text(
        "---\n"
        "name: test-analyst\n"
        "description: >-\n"
        "  Analyze test results and identify flaky tests, coverage gaps, and\n"
        "  regression patterns in CI pipelines.\n"
        "model: sonnet\n"
        "tier: candidate\n"
        "modes: [research]\n"
        "capabilities:\n"
        "  - test result analysis\n"
        "  - flaky test detection\n"
        "  - coverage gap identification\n"
        "tools: [Read, Grep, Bash]\n"
        "---\n"
        "# Test Analyst\n\nBody content.\n",
        encoding="utf-8",
    )
    return d


@pytest.fixture()
def sample_registry(tmp_path: Path) -> Path:
    reg = tmp_path / "registry.yml"
    reg.write_text(
        yaml.dump(
            {
                "version": 1,
                "agents": [
                    {
                        "name": "test-analyst",
                        "description": "Analyze test results and identify flaky tests, coverage gaps, and regression patterns in CI pipelines.",
                        "model": "sonnet",
                        "tier": "candidate",
                        "modes": ["research"],
                        "capabilities": [
                            "test result analysis",
                            "flaky test detection",
                            "coverage gap identification",
                        ],
                        "tools": ["Read", "Grep", "Bash"],
                        "file": "agents/test-analyst.md",
                    },
                    {
                        "name": "security",
                        "description": "Application security specialist for OWASP audits, vulnerability assessment, and secure code review.",
                        "model": "sonnet",
                        "tier": "production",
                        "modes": ["validate"],
                        "capabilities": [
                            "OWASP audit",
                            "vulnerability scanning",
                            "threat modeling",
                        ],
                        "tools": ["Read", "Grep", "Bash"],
                        "file": "agents/security.md",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return reg


class TestGenerateTestQueries:
    """Test query generation for routing evaluation."""

    def test_generates_positive_queries(self, sample_registry: Path) -> None:
        from masonry.scripts.optimize_routing import generate_test_queries

        queries = generate_test_queries(
            agent_name="test-analyst",
            description="Analyze test results and identify flaky tests",
            capabilities=["test result analysis", "flaky test detection"],
        )
        positives = [q for q in queries if q["expected_match"]]
        assert len(positives) >= 5

    def test_generates_negative_queries(self, sample_registry: Path) -> None:
        from masonry.scripts.optimize_routing import generate_test_queries

        queries = generate_test_queries(
            agent_name="test-analyst",
            description="Analyze test results and identify flaky tests",
            capabilities=["test result analysis", "flaky test detection"],
        )
        negatives = [q for q in queries if not q["expected_match"]]
        assert len(negatives) >= 5

    def test_query_structure(self) -> None:
        from masonry.scripts.optimize_routing import generate_test_queries

        queries = generate_test_queries(
            agent_name="security",
            description="OWASP audits and vulnerability assessment",
            capabilities=["OWASP audit", "vulnerability scanning"],
        )
        for q in queries:
            assert "query" in q
            assert "expected_match" in q
            assert isinstance(q["query"], str)
            assert isinstance(q["expected_match"], bool)
            assert len(q["query"]) > 5


class TestScoreRouting:
    """Test routing accuracy scoring."""

    def test_perfect_score(self) -> None:
        from masonry.scripts.optimize_routing import score_routing_results

        results = [
            {"query": "q1", "expected_match": True, "actual_match": True},
            {"query": "q2", "expected_match": False, "actual_match": False},
        ]
        assert score_routing_results(results) == 1.0

    def test_zero_score(self) -> None:
        from masonry.scripts.optimize_routing import score_routing_results

        results = [
            {"query": "q1", "expected_match": True, "actual_match": False},
            {"query": "q2", "expected_match": False, "actual_match": True},
        ]
        assert score_routing_results(results) == 0.0

    def test_partial_score(self) -> None:
        from masonry.scripts.optimize_routing import score_routing_results

        results = [
            {"query": "q1", "expected_match": True, "actual_match": True},
            {"query": "q2", "expected_match": True, "actual_match": False},
            {"query": "q3", "expected_match": False, "actual_match": False},
            {"query": "q4", "expected_match": False, "actual_match": True},
        ]
        assert score_routing_results(results) == 0.5

    def test_empty_results(self) -> None:
        from masonry.scripts.optimize_routing import score_routing_results

        assert score_routing_results([]) == 0.0


class TestSaveResults:
    """Test result persistence."""

    def test_saves_json(self, tmp_path: Path) -> None:
        import json

        from masonry.scripts.optimize_routing import save_eval_results

        results = {
            "agent": "test-analyst",
            "accuracy": 0.85,
            "queries": 20,
        }
        save_eval_results("test-analyst", results, tmp_path)
        output = tmp_path / "test-analyst" / "routing_eval.json"
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["accuracy"] == 0.85
