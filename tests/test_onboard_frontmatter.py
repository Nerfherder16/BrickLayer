"""Tests for triggers and tools frontmatter fields in onboard_agent.py."""

from __future__ import annotations

import textwrap
from pathlib import Path


from masonry.scripts.onboard_agent import extract_agent_metadata, generate_registry_entry
from masonry.src.schemas import AgentRegistryEntry


# ── helpers ───────────────────────────────────────────────────────────────────


def _write_agent_file(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test-agent.md"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ── extract_agent_metadata: triggers and tools ────────────────────────────────


def test_extract_triggers_and_tools(tmp_path: Path) -> None:
    """onboard_agent.py correctly extracts triggers and tools from frontmatter."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        ---
        name: my-agent
        model: sonnet
        triggers:
          - messy project state
          - update CHANGELOG
        tools:
          - Read
          - Write
          - Bash
        ---
        # My Agent
        Body text here.
        """,
    )
    meta = extract_agent_metadata(agent_file)
    assert meta["triggers"] == ["messy project state", "update CHANGELOG"]
    assert meta["tools"] == ["Read", "Write", "Bash"]


def test_missing_triggers_defaults_to_empty(tmp_path: Path) -> None:
    """Missing triggers field returns [] not None."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        ---
        name: no-triggers-agent
        model: sonnet
        tools:
          - Read
        ---
        # Agent without triggers
        """,
    )
    meta = extract_agent_metadata(agent_file)
    assert meta["triggers"] == []
    assert isinstance(meta["triggers"], list)


def test_missing_tools_defaults_to_empty(tmp_path: Path) -> None:
    """Missing tools field returns [] not None."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        ---
        name: no-tools-agent
        model: sonnet
        triggers:
          - some trigger
        ---
        # Agent without tools
        """,
    )
    meta = extract_agent_metadata(agent_file)
    assert meta["tools"] == []
    assert isinstance(meta["tools"], list)


def test_no_frontmatter_triggers_and_tools_empty(tmp_path: Path) -> None:
    """Agent file with no frontmatter at all returns [] for triggers and tools."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        # Plain Agent
        No frontmatter here.
        """,
    )
    meta = extract_agent_metadata(agent_file)
    assert meta["triggers"] == []
    assert meta["tools"] == []


# ── generate_registry_entry: triggers and tools flow through ──────────────────


def test_generate_registry_entry_carries_triggers_and_tools(tmp_path: Path) -> None:
    """generate_registry_entry passes triggers and tools into the AgentRegistryEntry."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        ---
        name: full-agent
        model: sonnet
        triggers:
          - campaign complete
          - post-campaign review
        tools:
          - Read
          - Grep
          - Glob
        ---
        # Full Agent
        """,
    )
    meta = extract_agent_metadata(agent_file)
    entry = generate_registry_entry(meta)
    assert isinstance(entry, AgentRegistryEntry)
    assert entry.triggers == ["campaign complete", "post-campaign review"]
    assert entry.tools == ["Read", "Grep", "Glob"]


def test_generate_registry_entry_defaults_triggers_tools_empty(tmp_path: Path) -> None:
    """generate_registry_entry sets triggers=[] and tools=[] when absent."""
    agent_file = _write_agent_file(
        tmp_path,
        """\
        ---
        name: bare-agent
        model: haiku
        ---
        # Bare Agent
        """,
    )
    meta = extract_agent_metadata(agent_file)
    entry = generate_registry_entry(meta)
    assert entry.triggers == []
    assert entry.tools == []


# ── AgentRegistryEntry schema: new fields ────────────────────────────────────


def test_agent_registry_entry_accepts_triggers_and_tools() -> None:
    """AgentRegistryEntry model accepts triggers and tools as list[str]."""
    entry = AgentRegistryEntry(
        name="test-agent",
        file="agents/test-agent.md",
        triggers=["trigger one", "trigger two"],
        tools=["Read", "Write"],
    )
    assert entry.triggers == ["trigger one", "trigger two"]
    assert entry.tools == ["Read", "Write"]


def test_agent_registry_entry_triggers_tools_default_empty() -> None:
    """AgentRegistryEntry defaults triggers and tools to [] when not provided."""
    entry = AgentRegistryEntry(name="x", file="x.md")
    assert entry.triggers == []
    assert entry.tools == []


def test_agent_registry_entry_round_trip_with_triggers_tools() -> None:
    """AgentRegistryEntry round-trips correctly with triggers and tools."""
    entry = AgentRegistryEntry(
        name="round-trip-agent",
        file="agents/round-trip.md",
        triggers=["messy project", "update docs"],
        tools=["Bash", "Glob"],
    )
    dumped = entry.model_dump()
    restored = AgentRegistryEntry.model_validate(dumped)
    assert restored.triggers == entry.triggers
    assert restored.tools == entry.tools
