"""Tests for backfill_frontmatter.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def agents_dir(tmp_path: Path) -> Path:
    d = tmp_path / "agents"
    d.mkdir()
    return d


class TestBackfillFrontmatter:
    """Test the backfill_frontmatter script."""

    def test_adds_frontmatter_to_empty_file(self, agents_dir: Path) -> None:
        agent = agents_dir / "my-agent.md"
        agent.write_text("", encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        changed = backfill_file(agent)
        assert changed is True
        content = agent.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        fm = yaml.safe_load(content.split("---", 2)[1])
        assert fm["name"] == "my-agent"
        assert fm["model"] == "sonnet"
        assert fm["tier"] == "draft"

    def test_adds_frontmatter_to_stub_file(self, agents_dir: Path) -> None:
        agent = agents_dir / "test-bot.md"
        agent.write_text("STUB", encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        changed = backfill_file(agent)
        assert changed is True
        content = agent.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        # Body preserved after frontmatter
        assert content.endswith("STUB\n") or content.endswith("STUB")

    def test_skips_file_with_existing_frontmatter(self, agents_dir: Path) -> None:
        agent = agents_dir / "existing.md"
        original = textwrap.dedent("""\
            ---
            name: existing
            model: opus
            ---
            # Existing Agent
            Body content here.
        """)
        agent.write_text(original, encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        changed = backfill_file(agent)
        assert changed is False
        assert agent.read_text(encoding="utf-8") == original

    def test_preserves_body_content(self, agents_dir: Path) -> None:
        agent = agents_dir / "with-body.md"
        body = "# My Agent\n\nThis agent does things.\n\n## Process\n1. Step one\n"
        agent.write_text(body, encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        changed = backfill_file(agent)
        assert changed is True
        content = agent.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        assert len(parts) == 3
        # Body after frontmatter preserved
        assert parts[2].strip() == body.strip()

    def test_extracts_description_from_first_paragraph(self, agents_dir: Path) -> None:
        agent = agents_dir / "descriptive.md"
        agent.write_text(
            "# Descriptive Agent\n\nThis agent analyzes complex data patterns.\n\n## More\n",
            encoding="utf-8",
        )

        from masonry.scripts.backfill_frontmatter import backfill_file

        backfill_file(agent)
        content = agent.read_text(encoding="utf-8")
        fm = yaml.safe_load(content.split("---", 2)[1])
        assert len(fm["description"]) >= 20

    def test_idempotent_double_run(self, agents_dir: Path) -> None:
        agent = agents_dir / "idempotent.md"
        agent.write_text("", encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        backfill_file(agent)
        content_after_first = agent.read_text(encoding="utf-8")
        changed = backfill_file(agent)
        assert changed is False
        assert agent.read_text(encoding="utf-8") == content_after_first

    def test_valid_yaml_output(self, agents_dir: Path) -> None:
        agent = agents_dir / "yaml-check.md"
        agent.write_text("", encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import backfill_file

        backfill_file(agent)
        content = agent.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        # Should not raise
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict)
        assert "name" in fm
        assert "model" in fm
        assert "tier" in fm
        assert isinstance(fm.get("modes"), list)
        assert isinstance(fm.get("capabilities"), list)
        assert isinstance(fm.get("tools"), list)

    def test_skips_non_agent_files(self, agents_dir: Path) -> None:
        meta = agents_dir / "AGENTS.md"
        meta.write_text("# Agent listing\nNot an agent file.", encoding="utf-8")

        from masonry.scripts.backfill_frontmatter import should_backfill

        assert should_backfill(meta) is False
