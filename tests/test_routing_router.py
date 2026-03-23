"""Tests for masonry/src/routing/router.py and llm_router.py."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from masonry.src.routing.llm_router import route_llm
from masonry.src.routing.router import route
from masonry.src.schemas import AgentRegistryEntry, RoutingDecision


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


def make_registry() -> list[AgentRegistryEntry]:
    return [
        AgentRegistryEntry(
            name="quantitative-analyst",
            file="agents/qa.md",
            modes=["simulate"],
            capabilities=["simulation"],
            tier="trusted",
        ),
        AgentRegistryEntry(
            name="fix-agent",
            file="agents/fix.md",
            modes=["fix"],
            capabilities=["code-fix"],
            tier="trusted",
        ),
    ]


# ──────────────────────────────────────────────────────────────────────────
# LLM Router
# ──────────────────────────────────────────────────────────────────────────


class TestLLMRouter:
    def test_valid_json_output_parsed_correctly(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "target_agent": "quantitative-analyst",
            "reason": "Simulation question about parameter sweep",
        })

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("simulate parameter sweep", make_registry())

        assert result is not None
        assert result.target_agent == "quantitative-analyst"
        assert result.layer == "llm"
        assert result.confidence == 0.6
        assert "Simulation" in result.reason or len(result.reason) > 0

    def test_timeout_returns_none(self):
        with patch(
            "masonry.src.routing.llm_router.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=15),
        ):
            result = route_llm("ambiguous request", make_registry())

        assert result is None

    def test_garbage_stdout_returns_none(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "this is not JSON at all !!!"

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("ambiguous request", make_registry())

        assert result is None

    def test_subprocess_failure_returns_none(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("ambiguous request", make_registry())

        assert result is None

    def test_reason_truncated_to_100_chars(self):
        long_reason = "x" * 200
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "target_agent": "fix-agent",
            "reason": long_reason,
        })

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("fix this bug", make_registry())

        assert result is not None
        assert len(result.reason) <= 100

    def test_missing_reason_uses_default(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"target_agent": "fix-agent"})

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("fix this bug", make_registry())

        assert result is not None
        assert result.reason  # non-empty default

    def test_result_is_routing_decision(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "target_agent": "quantitative-analyst",
            "reason": "simulation task",
        })

        with patch("masonry.src.routing.llm_router.subprocess.run", return_value=mock_result):
            result = route_llm("simulate something", make_registry())

        assert isinstance(result, RoutingDecision)


# ──────────────────────────────────────────────────────────────────────────
# Four-Layer Router
# ──────────────────────────────────────────────────────────────────────────


class TestRouter:
    def _make_registry_file(self, tmp_path: Path) -> None:
        """Write a minimal registry file to tmp_path/masonry/agent_registry.yml."""
        registry_dir = tmp_path / "masonry"
        registry_dir.mkdir(exist_ok=True)
        registry_file = registry_dir / "agent_registry.yml"
        registry_file.write_text(
            """version: 1
agents:
  - name: quantitative-analyst
    file: agents/qa.md
    modes: [simulate]
    capabilities: [simulation]
    tier: trusted
""",
            encoding="utf-8",
        )

    def test_deterministic_layer_wins(self, tmp_path):
        """If Layer 1 returns a result, Layers 2+3 are not called."""
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic") as mock_l1, \
             patch("masonry.src.routing.router.route_semantic") as mock_l2, \
             patch("masonry.src.routing.router.route_llm") as mock_l3:

            mock_l1.return_value = RoutingDecision(
                target_agent="spec-writer",
                layer="deterministic",
                confidence=1.0,
                reason="/plan command",
            )

            result = route("/plan this", tmp_path)

        assert result.target_agent == "spec-writer"
        assert result.layer == "deterministic"
        mock_l2.assert_not_called()
        mock_l3.assert_not_called()

    def test_semantic_layer_used_when_deterministic_fails(self, tmp_path):
        """If Layer 1 returns None, Layer 2 is tried."""
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic", return_value=None), \
             patch("masonry.src.routing.router.route_semantic") as mock_l2, \
             patch("masonry.src.routing.router.route_llm") as mock_l3:

            mock_l2.return_value = RoutingDecision(
                target_agent="quantitative-analyst",
                layer="semantic",
                confidence=0.85,
                reason="Semantic match: 0.85",
            )

            result = route("run a simulation", tmp_path)

        assert result.target_agent == "quantitative-analyst"
        assert result.layer == "semantic"
        mock_l3.assert_not_called()

    def test_llm_layer_used_when_both_fail(self, tmp_path):
        """If Layers 1+2 return None, Layer 3 is tried."""
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic", return_value=None), \
             patch("masonry.src.routing.router.route_semantic", return_value=None), \
             patch("masonry.src.routing.router.route_llm") as mock_l3:

            mock_l3.return_value = RoutingDecision(
                target_agent="fix-agent",
                layer="llm",
                confidence=0.6,
                reason="LLM routing",
            )

            result = route("fix the broken thing", tmp_path)

        assert result.target_agent == "fix-agent"
        assert result.layer == "llm"

    def test_fallback_when_all_layers_fail(self, tmp_path):
        """If all three layers return None, fallback is returned."""
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic", return_value=None), \
             patch("masonry.src.routing.router.route_semantic", return_value=None), \
             patch("masonry.src.routing.router.route_llm", return_value=None):

            result = route("completely ambiguous request here", tmp_path)

        assert result.target_agent == "user"
        assert result.layer == "fallback"
        assert result.confidence == 0.0

    def test_fallback_reason_is_nonempty(self, tmp_path):
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic", return_value=None), \
             patch("masonry.src.routing.router.route_semantic", return_value=None), \
             patch("masonry.src.routing.router.route_llm", return_value=None):

            result = route("some request", tmp_path)

        assert len(result.reason) > 0

    def test_missing_registry_uses_empty_list(self, tmp_path):
        """If no registry file exists, routing still works with empty registry."""
        # No registry file created in tmp_path
        with patch("masonry.src.routing.router.route_deterministic") as mock_l1, \
             patch("masonry.src.routing.router.route_semantic") as mock_l2, \
             patch("masonry.src.routing.router.route_llm") as mock_l3:

            mock_l1.return_value = None
            mock_l2.return_value = None
            mock_l3.return_value = None

            result = route("some request", tmp_path)

        # Should reach fallback without crashing
        assert result.target_agent == "user"
        assert result.layer == "fallback"

    def test_result_is_routing_decision(self, tmp_path):
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic", return_value=None), \
             patch("masonry.src.routing.router.route_semantic", return_value=None), \
             patch("masonry.src.routing.router.route_llm", return_value=None):

            result = route("some request", tmp_path)

        assert isinstance(result, RoutingDecision)

    def test_log_to_stderr(self, tmp_path, capsys):
        """Router should log which layer resolved to stderr."""
        self._make_registry_file(tmp_path)

        with patch("masonry.src.routing.router.route_deterministic") as mock_l1, \
             patch("masonry.src.routing.router.route_semantic") as mock_l2, \
             patch("masonry.src.routing.router.route_llm") as mock_l3:

            mock_l1.return_value = RoutingDecision(
                target_agent="spec-writer",
                layer="deterministic",
                confidence=1.0,
                reason="/plan",
            )

            route("/plan feature", tmp_path)

        captured = capsys.readouterr()
        assert "[ROUTER]" in captured.err or "deterministic" in captured.err or "spec-writer" in captured.err
