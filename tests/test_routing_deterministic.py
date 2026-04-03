"""Tests for masonry/src/routing/deterministic.py — Layer 1 routing."""

from __future__ import annotations



from masonry.src.routing.deterministic import (
    _route_from_registry_keywords,
    route_deterministic,
)
from masonry.src.schemas import AgentRegistryEntry, RoutingDecision


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


def make_registry() -> list[AgentRegistryEntry]:
    """Minimal registry for testing routing rules."""
    return [
        AgentRegistryEntry(
            name="quantitative-analyst",
            file="agents/quantitative-analyst.md",
            modes=["simulate"],
            capabilities=["simulation"],
            tier="trusted",
        ),
        AgentRegistryEntry(
            name="regulatory-researcher",
            file="agents/regulatory-researcher.md",
            modes=["research"],
            capabilities=["regulatory-research"],
            tier="draft",
        ),
        AgentRegistryEntry(
            name="fix-agent",
            file="agents/fix-agent.md",
            modes=["fix"],
            capabilities=["code-fix"],
            tier="trusted",
        ),
    ]


# ──────────────────────────────────────────────────────────────────────────
# Slash command routing
# ──────────────────────────────────────────────────────────────────────────


class TestSlashCommandRouting:
    def test_plan_command(self, tmp_path):
        result = route_deterministic("/plan this feature", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "spec-writer"
        assert result.layer == "deterministic"
        assert result.confidence == 1.0

    def test_build_command(self, tmp_path):
        result = route_deterministic("/build", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "build-workflow"

    def test_fix_command(self, tmp_path):
        result = route_deterministic("/fix", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "fix-workflow"

    def test_verify_command(self, tmp_path):
        result = route_deterministic("/verify", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "verify-workflow"

    def test_bl_run_command(self, tmp_path):
        result = route_deterministic("/bl-run", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "campaign-conductor"

    def test_masonry_run_command(self, tmp_path):
        result = route_deterministic("/masonry-run", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "campaign-conductor"

    def test_plan_embedded_in_sentence(self, tmp_path):
        """'/plan' inside a sentence should still match."""
        result = route_deterministic(
            "can you /plan this feature please", tmp_path, make_registry()
        )
        assert result is not None
        assert result.target_agent == "spec-writer"

    def test_build_embedded_in_sentence(self, tmp_path):
        result = route_deterministic(
            "please /build the API endpoints", tmp_path, make_registry()
        )
        assert result is not None
        assert result.target_agent == "build-workflow"

    def test_result_is_routing_decision(self, tmp_path):
        result = route_deterministic("/plan", tmp_path, make_registry())
        assert isinstance(result, RoutingDecision)


# ──────────────────────────────────────────────────────────────────────────
# Autopilot state routing
# ──────────────────────────────────────────────────────────────────────────


class TestAutopilotStateRouting:
    def test_build_mode_from_file(self, tmp_path):
        autopilot_dir = tmp_path / ".autopilot"
        autopilot_dir.mkdir()
        (autopilot_dir / "mode").write_text("build", encoding="utf-8")
        result = route_deterministic("some request", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "build-workflow"

    def test_fix_mode_from_file(self, tmp_path):
        autopilot_dir = tmp_path / ".autopilot"
        autopilot_dir.mkdir()
        (autopilot_dir / "mode").write_text("fix", encoding="utf-8")
        result = route_deterministic("some request", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "fix-workflow"

    def test_verify_mode_from_file(self, tmp_path):
        autopilot_dir = tmp_path / ".autopilot"
        autopilot_dir.mkdir()
        (autopilot_dir / "mode").write_text("verify", encoding="utf-8")
        result = route_deterministic("some request", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "verify-workflow"

    def test_missing_autopilot_dir_does_not_crash(self, tmp_path):
        """No .autopilot dir → fall through, no crash."""
        result = route_deterministic("no signals here", tmp_path, make_registry())
        # Should return None (no match) or some other result, but not raise
        # (We don't assert None since slash commands or mode fields might match)


# ──────────────────────────────────────────────────────────────────────────
# UI state routing
# ──────────────────────────────────────────────────────────────────────────


class TestUIStateRouting:
    def test_compose_mode(self, tmp_path):
        ui_dir = tmp_path / ".ui"
        ui_dir.mkdir()
        (ui_dir / "mode").write_text("compose", encoding="utf-8")
        result = route_deterministic("some request", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "ui-compose-workflow"

    def test_review_mode(self, tmp_path):
        ui_dir = tmp_path / ".ui"
        ui_dir.mkdir()
        (ui_dir / "mode").write_text("review", encoding="utf-8")
        result = route_deterministic("some request", tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "ui-review-workflow"


# ──────────────────────────────────────────────────────────────────────────
# Question Mode field routing
# ──────────────────────────────────────────────────────────────────────────


class TestQuestionModeRouting:
    def test_mode_simulate_routes_to_quantitative_analyst(self, tmp_path):
        request = "Here is the question.\n\n**Mode**: simulate\n\nDetails follow."
        result = route_deterministic(request, tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "quantitative-analyst"

    def test_mode_research_routes_to_first_research_agent(self, tmp_path):
        request = "**Mode**: research"
        result = route_deterministic(request, tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "regulatory-researcher"

    def test_mode_fix_routes_to_fix_agent(self, tmp_path):
        request = "**Mode**: fix"
        result = route_deterministic(request, tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "fix-agent"

    def test_unknown_mode_in_request_returns_none(self, tmp_path):
        request = "**Mode**: unknown_mode_xyz"
        result = route_deterministic(request, tmp_path, make_registry())
        # No agent for this mode → None
        assert result is None

    def test_mode_field_with_extra_spaces(self, tmp_path):
        request = "**Mode**:   simulate"
        result = route_deterministic(request, tmp_path, make_registry())
        assert result is not None
        assert result.target_agent == "quantitative-analyst"


# ──────────────────────────────────────────────────────────────────────────
# No signal → return None
# ──────────────────────────────────────────────────────────────────────────


class TestNoSignal:
    def test_no_signal_returns_none(self, tmp_path):
        result = route_deterministic(
            "Hello, can you help me think about this?",
            tmp_path,
            make_registry(),
        )
        assert result is None

    def test_empty_string_returns_none(self, tmp_path):
        result = route_deterministic("", tmp_path, make_registry())
        assert result is None

    def test_missing_state_files_do_not_crash(self, tmp_path):
        """tmp_path has no state files — should silently return None."""
        result = route_deterministic(
            "A completely ambiguous request with no signals.",
            tmp_path,
            make_registry(),
        )
        assert result is None


# ──────────────────────────────────────────────────────────────────────────
# Confidence and layer fields
# ──────────────────────────────────────────────────────────────────────────


class TestRoutingDecisionFields:
    def test_confidence_is_1_for_deterministic(self, tmp_path):
        result = route_deterministic("/plan", tmp_path, make_registry())
        assert result is not None
        assert result.confidence == 1.0

    def test_layer_is_deterministic(self, tmp_path):
        result = route_deterministic("/build", tmp_path, make_registry())
        assert result is not None
        assert result.layer == "deterministic"

    def test_reason_is_nonempty_string(self, tmp_path):
        result = route_deterministic("/fix", tmp_path, make_registry())
        assert result is not None
        assert len(result.reason) > 0


# ──────────────────────────────────────────────────────────────────────────
# Registry keyword routing
# ──────────────────────────────────────────────────────────────────────────


def _registry_with_keywords(
    *entries: tuple[str, list[str]],
) -> list[AgentRegistryEntry]:
    """Build a registry with named agents and their routing_keywords."""
    return [
        AgentRegistryEntry(
            name=name,
            file=f"agents/{name}.md",
            routing_keywords=keywords,
            tier="candidate",
        )
        for name, keywords in entries
    ]


class TestRegistryKeywordRouting:
    def test_single_keyword_match(self):
        registry = _registry_with_keywords(("deploy-agent", ["deploy to casaos"]))
        result = _route_from_registry_keywords("please deploy to casaos now", registry)
        assert result is not None
        assert result.target_agent == "deploy-agent"
        assert result.layer == "deterministic"
        assert result.confidence == 1.0

    def test_first_matching_entry_wins(self):
        """When multiple entries match, the first one in registry order wins."""
        registry = _registry_with_keywords(
            ("agent-a", ["security audit"]),
            ("agent-b", ["security audit"]),
        )
        result = _route_from_registry_keywords("run a security audit", registry)
        assert result is not None
        assert result.target_agent == "agent-a"

    def test_no_match_returns_none(self):
        registry = _registry_with_keywords(("agent-a", ["deploy to casaos"]))
        result = _route_from_registry_keywords("write unit tests please", registry)
        assert result is None

    def test_empty_keywords_list_skipped(self):
        registry = _registry_with_keywords(
            ("agent-no-keywords", []),
            ("agent-with-keywords", ["refactor"]),
        )
        result = _route_from_registry_keywords("please refactor this module", registry)
        assert result is not None
        assert result.target_agent == "agent-with-keywords"

    def test_case_insensitive_match(self):
        registry = _registry_with_keywords(("agent-a", ["ROOT CAUSE"]))
        result = _route_from_registry_keywords("what is the root cause here?", registry)
        assert result is not None
        assert result.target_agent == "agent-a"

    def test_multiword_keyword_match(self):
        registry = _registry_with_keywords(("agent-a", ["pull request"]))
        result = _route_from_registry_keywords("open a pull request for this", registry)
        assert result is not None
        assert result.target_agent == "agent-a"

    def test_registry_keywords_take_precedence_over_hardcoded(self, tmp_path):
        """Registry keywords fire before hardcoded patterns in route_deterministic."""
        registry = _registry_with_keywords(("custom-git-agent", ["git commit"]))
        result = route_deterministic("git commit the changes", tmp_path, registry)
        assert result is not None
        assert result.target_agent == "custom-git-agent"

    def test_empty_registry_returns_none(self):
        result = _route_from_registry_keywords("git commit", [])
        assert result is None

    def test_registry_without_keywords_falls_through_to_hardcoded(self, tmp_path):
        """No routing_keywords in registry → hardcoded patterns still fire."""
        registry = [
            AgentRegistryEntry(
                name="some-agent",
                file="agents/some-agent.md",
                tier="candidate",
            )
        ]
        result = route_deterministic("git commit the changes", tmp_path, registry)
        assert result is not None
        assert result.target_agent == "git-nerd"
