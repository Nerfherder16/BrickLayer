"""Tests for masonry/scripts/backfill_registry.py and masonry/scripts/validate_agents.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_agent(path: Path, frontmatter: str, body: str = "") -> None:
    """Write an agent .md file with given frontmatter and optional body."""
    path.write_text(
        f"---\n{frontmatter.strip()}\n---\n\n{body}",
        encoding="utf-8",
    )


def _write_valid_agent(path: Path, name: str | None = None) -> None:
    """Write a fully valid agent file."""
    stem = name or path.stem
    _write_agent(
        path,
        frontmatter=textwrap.dedent(f"""\
            name: {stem}
            model: sonnet
            description: "This agent does something useful and meaningful for the system."
            modes:
              - simulate
              - research
            capabilities:
              - capability-one
              - capability-two
            input_schema: QuestionPayload
            output_schema: FindingPayload
            tier: draft
        """),
        body="# Agent body\n\nDoes useful research work.",
    )


def _write_registry(path: Path, agents: list[str]) -> None:
    """Write a minimal registry YAML with the given agent names."""
    data = {
        "version": 1,
        "agents": [
            {"name": a, "file": f"agents/{a}.md", "tier": "draft"} for a in agents
        ],
    }
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def _load_registry(path: Path) -> list[dict]:
    """Load registry YAML and return list of agent dicts."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("agents", [])


# ---------------------------------------------------------------------------
# backfill_registry tests
# ---------------------------------------------------------------------------


class TestBackfillRegistry:
    """Tests for masonry/scripts/backfill_registry.py."""

    def test_adds_missing_agent(self, tmp_path: Path) -> None:
        """backfill adds an agent that exists on disk but not in registry."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        # One agent on disk, none in registry
        _write_valid_agent(agents_dir / "my-agent.md", name="my-agent")
        _write_registry(registry_path, agents=[])

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        assert added == 1
        assert removed == 0
        entries = _load_registry(registry_path)
        names = [e["name"] for e in entries]
        assert "my-agent" in names

    def test_adds_multiple_missing_agents(self, tmp_path: Path) -> None:
        """backfill adds all unregistered agents from a directory."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        for stem in ("alpha", "beta", "gamma"):
            _write_valid_agent(agents_dir / f"{stem}.md", name=stem)
        _write_registry(registry_path, ["alpha"])  # beta and gamma missing

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        assert added == 2
        assert removed == 0
        entries = _load_registry(registry_path)
        names = [e["name"] for e in entries]
        assert "alpha" in names
        assert "beta" in names
        assert "gamma" in names

    def test_skips_already_registered_agent(self, tmp_path: Path) -> None:
        """backfill does not duplicate an agent already in the registry."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(agents_dir / "existing.md", name="existing")
        _write_registry(registry_path, ["existing"])

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        assert added == 0
        assert removed == 0
        entries = _load_registry(registry_path)
        assert sum(1 for e in entries if e["name"] == "existing") == 1

    def test_removes_phantom_entry(self, tmp_path: Path) -> None:
        """backfill removes registry entries whose .md file no longer exists."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        # Registry has "ghost" but no .md file exists for it
        _write_registry(registry_path, ["ghost"])

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        assert added == 0
        assert removed == 1
        entries = _load_registry(registry_path)
        names = [e["name"] for e in entries]
        assert "ghost" not in names

    def test_sets_dspy_defaults_on_new_entry(self, tmp_path: Path) -> None:
        """New entries get dspy_status, drift_status, last_score, runs_since_optimization."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(agents_dir / "new-agent.md", name="new-agent")
        _write_registry(registry_path, [])

        backfill(agents_dirs=[agents_dir], registry_path=registry_path)

        entries = _load_registry(registry_path)
        entry = next(e for e in entries if e["name"] == "new-agent")
        assert entry.get("dspy_status") == "not_optimized"
        assert entry.get("drift_status") == "ok"
        assert entry.get("last_score") is None
        assert entry.get("runs_since_optimization") == 0

    def test_sets_registry_source_frontmatter(self, tmp_path: Path) -> None:
        """New entries have registrySource set to 'frontmatter'."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(agents_dir / "sourced.md", name="sourced")
        _write_registry(registry_path, [])

        backfill(agents_dirs=[agents_dir], registry_path=registry_path)

        entries = _load_registry(registry_path)
        entry = next(e for e in entries if e["name"] == "sourced")
        assert entry.get("registrySource") == "frontmatter"

    def test_handles_multiple_agent_dirs(self, tmp_path: Path) -> None:
        """backfill reads agents from multiple directories."""
        from masonry.scripts.backfill_registry import backfill

        dir_a = tmp_path / "global_agents"
        dir_b = tmp_path / "project_agents"
        dir_a.mkdir()
        dir_b.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(dir_a / "global-one.md", name="global-one")
        _write_valid_agent(dir_b / "project-one.md", name="project-one")
        _write_registry(registry_path, [])

        added, removed = backfill(
            agents_dirs=[dir_a, dir_b],
            registry_path=registry_path,
        )

        assert added == 2
        entries = _load_registry(registry_path)
        names = [e["name"] for e in entries]
        assert "global-one" in names
        assert "project-one" in names

    def test_both_add_and_remove_in_one_call(self, tmp_path: Path) -> None:
        """backfill can add new agents and remove phantoms in the same run."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(agents_dir / "real-agent.md", name="real-agent")
        _write_registry(registry_path, ["phantom-agent"])  # phantom, no file

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        assert added == 1
        assert removed == 1
        entries = _load_registry(registry_path)
        names = [e["name"] for e in entries]
        assert "real-agent" in names
        assert "phantom-agent" not in names

    def test_returns_correct_total_count(self, tmp_path: Path) -> None:
        """Registry final total includes existing + added - removed."""
        from masonry.scripts.backfill_registry import backfill

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        registry_path = tmp_path / "registry.yml"

        _write_valid_agent(agents_dir / "keeper.md", name="keeper")
        _write_valid_agent(agents_dir / "newcomer.md", name="newcomer")
        _write_registry(registry_path, ["keeper", "phantom"])

        added, removed = backfill(
            agents_dirs=[agents_dir],
            registry_path=registry_path,
        )

        entries = _load_registry(registry_path)
        # keeper + newcomer = 2; phantom removed
        assert len(entries) == 2
        assert added == 1
        assert removed == 1


# ---------------------------------------------------------------------------
# validate_agents tests
# ---------------------------------------------------------------------------


class TestValidateAgents:
    """Tests for masonry/scripts/validate_agents.py."""

    def test_valid_agent_no_violations(self, tmp_path: Path) -> None:
        """A fully valid agent file produces no violations."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_valid_agent(agents_dir / "good-agent.md", name="good-agent")

        violations = validate_agents_dir([agents_dir])
        assert violations == []

    def test_missing_name_field(self, tmp_path: Path) -> None:
        """Missing 'name' field is flagged as a violation."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "no-name.md",
            frontmatter=textwrap.dedent("""\
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "name" in fields

    def test_name_mismatch_with_filename(self, tmp_path: Path) -> None:
        """'name' field that doesn't match filename stem is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "my-agent.md",
            frontmatter=textwrap.dedent("""\
                name: wrong-name
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "name" in fields

    def test_invalid_model_value(self, tmp_path: Path) -> None:
        """'model' with invalid value (not haiku/sonnet/opus) is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "bad-model.md",
            frontmatter=textwrap.dedent("""\
                name: bad-model
                model: gpt4
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "model" in fields

    def test_description_too_short(self, tmp_path: Path) -> None:
        """description shorter than 30 characters is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "short-desc.md",
            frontmatter=textwrap.dedent("""\
                name: short-desc
                model: sonnet
                description: "Too short"
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "description" in fields

    def test_invalid_mode_value(self, tmp_path: Path) -> None:
        """modes list with an invalid value is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "bad-mode.md",
            frontmatter=textwrap.dedent("""\
                name: bad-mode
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - invalid-mode-value
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "modes" in fields

    def test_missing_modes_field(self, tmp_path: Path) -> None:
        """Missing 'modes' field entirely is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "no-modes.md",
            frontmatter=textwrap.dedent("""\
                name: no-modes
                model: sonnet
                description: "A valid description that is long enough to pass."
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "modes" in fields

    def test_capabilities_fewer_than_two(self, tmp_path: Path) -> None:
        """capabilities list with only one item is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "one-cap.md",
            frontmatter=textwrap.dedent("""\
                name: one-cap
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - only-one
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "capabilities" in fields

    def test_missing_input_schema(self, tmp_path: Path) -> None:
        """Missing 'input_schema' field is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "no-input.md",
            frontmatter=textwrap.dedent("""\
                name: no-input
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "input_schema" in fields

    def test_missing_output_schema(self, tmp_path: Path) -> None:
        """Missing 'output_schema' field is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "no-output.md",
            frontmatter=textwrap.dedent("""\
                name: no-output
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "output_schema" in fields

    def test_invalid_tier_value(self, tmp_path: Path) -> None:
        """'tier' with value not in draft/candidate/trusted/retired is flagged."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "bad-tier.md",
            frontmatter=textwrap.dedent("""\
                name: bad-tier
                model: sonnet
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: unknown-tier
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        assert "tier" in fields

    def test_multiple_violations_in_one_file(self, tmp_path: Path) -> None:
        """Multiple invalid fields in one file produce multiple violations."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "broken.md",
            frontmatter=textwrap.dedent("""\
                name: broken
                model: bad-model
                description: "Short"
                modes:
                  - bad-mode
                capabilities:
                  - only-one
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: broken-tier
            """),
        )

        violations = validate_agents_dir([agents_dir])
        fields = [v["field"] for v in violations]
        # model, description, modes, capabilities, tier all bad
        assert len(violations) >= 3

    def test_violation_report_format(self, tmp_path: Path) -> None:
        """Each violation dict has 'filename', 'field', and 'reason' keys."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(
            agents_dir / "check-format.md",
            frontmatter=textwrap.dedent("""\
                name: check-format
                model: bad-model
                description: "A valid description that is long enough to pass."
                modes:
                  - research
                capabilities:
                  - cap-one
                  - cap-two
                input_schema: QuestionPayload
                output_schema: FindingPayload
                tier: draft
            """),
        )

        violations = validate_agents_dir([agents_dir])
        assert len(violations) >= 1
        v = violations[0]
        assert "filename" in v
        assert "field" in v
        assert "reason" in v

    def test_valid_all_model_values(self, tmp_path: Path) -> None:
        """haiku, sonnet, and opus are all accepted model values."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        for model in ("haiku", "sonnet", "opus"):
            stem = f"agent-{model}"
            _write_agent(
                agents_dir / f"{stem}.md",
                frontmatter=textwrap.dedent(f"""\
                    name: {stem}
                    model: {model}
                    description: "A valid description that is long enough to pass."
                    modes:
                      - research
                    capabilities:
                      - cap-one
                      - cap-two
                    input_schema: QuestionPayload
                    output_schema: FindingPayload
                    tier: draft
                """),
            )

        violations = validate_agents_dir([agents_dir])
        model_violations = [v for v in violations if v["field"] == "model"]
        assert model_violations == []

    def test_valid_all_tier_values(self, tmp_path: Path) -> None:
        """draft, candidate, trusted, retired are all accepted tier values."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        for tier in ("draft", "candidate", "trusted", "retired"):
            stem = f"agent-{tier}"
            _write_agent(
                agents_dir / f"{stem}.md",
                frontmatter=textwrap.dedent(f"""\
                    name: {stem}
                    model: sonnet
                    description: "A valid description that is long enough to pass."
                    modes:
                      - research
                    capabilities:
                      - cap-one
                      - cap-two
                    input_schema: QuestionPayload
                    output_schema: FindingPayload
                    tier: {tier}
                """),
            )

        violations = validate_agents_dir([agents_dir])
        tier_violations = [v for v in violations if v["field"] == "tier"]
        assert tier_violations == []

    def test_valid_all_mode_values(self, tmp_path: Path) -> None:
        """All valid mode values are accepted without violations."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        valid_modes = [
            "simulate",
            "diagnose",
            "fix",
            "audit",
            "research",
            "benchmark",
            "validate",
            "evolve",
            "monitor",
            "predict",
            "frontier",
            "agent",
        ]
        _write_agent(
            agents_dir / "all-modes.md",
            frontmatter="name: all-modes\nmodel: sonnet\n"
            'description: "A valid description that is long enough to pass."\n'
            "modes:\n"
            + "".join(f"  - {m}\n" for m in valid_modes)
            + "capabilities:\n  - cap-one\n  - cap-two\n"
            "input_schema: QuestionPayload\noutput_schema: FindingPayload\ntier: draft",
        )

        violations = validate_agents_dir([agents_dir])
        mode_violations = [v for v in violations if v["field"] == "modes"]
        assert mode_violations == []

    def test_skips_non_agent_markdown_files(self, tmp_path: Path) -> None:
        """Files like AGENTS.md, README.md, AUDIT_REPORT.md are skipped."""
        from masonry.scripts.validate_agents import validate_agents_dir

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        # Write files that should be skipped (no frontmatter, would produce violations)
        for skip_name in ("AGENTS.md", "README.md", "AUDIT_REPORT.md"):
            (agents_dir / skip_name).write_text(
                "# Skip me\n\nNo frontmatter here.", encoding="utf-8"
            )

        violations = validate_agents_dir([agents_dir])
        # These files should be skipped, not flagged
        assert violations == []
