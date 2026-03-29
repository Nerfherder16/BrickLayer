"""
Tests for backfill_routing_keywords.py

Covers:
- Frontmatter parsing (valid, malformed, missing)
- Keyword extraction strategies (quoted, capabilities, body sections)
- Deduplication and length capping
- --dry-run: exits 0, writes nothing
"""
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Make the scripts directory importable
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from backfill_routing_keywords import (
    load_frontmatter,
    write_frontmatter,
    extract_keywords,
    run,
)
from backfill_keywords_extractor import (
    strategy_quoted,
    strategy_capabilities,
    strategy_body_sections,
)


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def test_load_frontmatter_valid():
    raw = "---\nname: test-agent\ndescription: A test agent\n---\nBody text here."
    fm, body = load_frontmatter(raw)
    assert fm["name"] == "test-agent"
    assert "Body text here." in body


def test_load_frontmatter_no_leading_dashes_raises():
    raw = "name: test-agent\n---\nbody"
    with pytest.raises(ValueError, match="No leading"):
        load_frontmatter(raw)


def test_load_frontmatter_single_delimiter_raises():
    raw = "---\nname: test\n"
    with pytest.raises(ValueError):
        load_frontmatter(raw)


def test_write_frontmatter_roundtrip():
    original = "---\nname: test-agent\ndescription: hello\n---\nsome body"
    fm, body = load_frontmatter(original)
    fm["routing_keywords"] = ["kw1", "kw2"]
    result = write_frontmatter(fm, body)
    fm2, body2 = load_frontmatter(result)
    assert fm2["routing_keywords"] == ["kw1", "kw2"]
    assert "some body" in body2


# ---------------------------------------------------------------------------
# Strategy 1: quoted phrases
# ---------------------------------------------------------------------------

def test_strategy_quoted_extracts_phrases():
    desc = "Use this agent for 'failure cascade analysis' and 'blast radius' estimation."
    kws = strategy_quoted(desc)
    assert "failure cascade analysis" in kws
    assert "blast radius" in kws


def test_strategy_quoted_rejects_short():
    # less than 5 chars in quotes
    desc = "Use 'ab' to do stuff."
    kws = strategy_quoted(desc)
    assert kws == []


def test_strategy_quoted_rejects_too_long():
    desc = f"'{'x' * 51}'"
    kws = strategy_quoted(desc)
    assert kws == []


# ---------------------------------------------------------------------------
# Strategy 2: capabilities
# ---------------------------------------------------------------------------

def test_strategy_capabilities_list():
    caps = ["benchmark analysis", "latency measurement", "throughput testing"]
    kws = strategy_capabilities(caps)
    assert "benchmark analysis" in kws
    assert "latency measurement" in kws


def test_strategy_capabilities_non_list_returns_empty():
    assert strategy_capabilities("not a list") == []
    assert strategy_capabilities(None) == []


# ---------------------------------------------------------------------------
# Strategy 3: body sections
# ---------------------------------------------------------------------------

def test_strategy_body_sections_when_to_invoke():
    body = "\n## When to invoke\nActivate when you need failure cascade mapping.\n## Other section\nOther content."
    kws = strategy_body_sections(body)
    assert len(kws) >= 1
    assert any("failure cascade" in kw.lower() for kw in kws)


def test_strategy_body_sections_activate_when():
    body = "\n## Activate when\nUser wants to measure latency. More text."
    kws = strategy_body_sections(body)
    assert len(kws) >= 1


def test_strategy_body_sections_no_heading_returns_empty():
    body = "No relevant heading here. Just regular content."
    kws = strategy_body_sections(body)
    assert kws == []


# ---------------------------------------------------------------------------
# extract_keywords: deduplication and cap
# ---------------------------------------------------------------------------

def test_extract_keywords_caps_at_eight():
    fm = {
        "description": "'kw one' 'kw two' 'kw three' 'kw four' 'kw five'",
        "capabilities": ["cap six", "cap seven", "cap eight", "cap nine", "cap ten"],
    }
    kws, _ = extract_keywords(fm, "")
    assert len(kws) <= 8


def test_extract_keywords_deduplicates():
    fm = {
        "description": "'duplicate phrase'",
        "capabilities": ["duplicate phrase", "unique phrase"],
    }
    kws, _ = extract_keywords(fm, "")
    # "duplicate phrase" should appear only once
    assert kws.count("duplicate phrase") == 1


def test_extract_keywords_sorts_by_length():
    fm = {
        "capabilities": ["longer capability phrase", "short", "medium len"],
    }
    kws, _ = extract_keywords(fm, "")
    lengths = [len(k) for k in kws]
    assert lengths == sorted(lengths)


def test_extract_keywords_empty_fm_returns_empty():
    kws, source = extract_keywords({}, "")
    assert kws == []
    assert source == "none"


# ---------------------------------------------------------------------------
# Integration: run() with --dry-run
# ---------------------------------------------------------------------------

def _make_agent_md(tmp_dir: Path, name: str, routing_keywords=None) -> Path:
    fm: dict = {"name": name, "description": "An agent for 'test routing' and 'dry run'."}
    if routing_keywords is not None:
        fm["routing_keywords"] = routing_keywords
    fm_yaml = yaml.safe_dump(fm, default_flow_style=False)
    content = f"---\n{fm_yaml}---\n\n## When to invoke\nUse this for dry run testing."
    p = tmp_dir / f"{name}.md"
    p.write_text(content, encoding="utf-8")
    return p


def _make_registry(tmp_dir: Path, agents: list) -> Path:
    p = tmp_dir / "agent_registry.yml"
    p.write_text(yaml.dump(agents, default_flow_style=False), encoding="utf-8")
    return p


def test_run_dry_run_nothing_written(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    _make_agent_md(agents_dir, "test-agent-a")

    registry = _make_registry(
        tmp_path,
        [{"name": "test-agent-a", "routing_keywords": []}],
    )

    registry_mtime_before = registry.stat().st_mtime

    result = run(agents_dir, registry, dry_run=True)
    assert result == 0

    # Registry must not be modified
    registry_mtime_after = registry.stat().st_mtime
    assert registry_mtime_before == registry_mtime_after


def test_run_dry_run_already_populated(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    registry = _make_registry(
        tmp_path,
        [{"name": "test-agent-b", "routing_keywords": ["already", "populated"]}],
    )

    result = run(agents_dir, registry, dry_run=True)
    assert result == 0  # "nothing to do" path also returns 0


def test_run_live_writes_keywords(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    _make_agent_md(agents_dir, "test-agent-c")

    registry = _make_registry(
        tmp_path,
        [{"name": "test-agent-c", "routing_keywords": []}],
    )

    result = run(agents_dir, registry, dry_run=False)
    assert result == 0

    # Registry should now have keywords
    updated = yaml.safe_load(registry.read_text(encoding="utf-8"))
    agent = next(a for a in updated if a["name"] == "test-agent-c")
    assert isinstance(agent["routing_keywords"], list)
    assert len(agent["routing_keywords"]) > 0
