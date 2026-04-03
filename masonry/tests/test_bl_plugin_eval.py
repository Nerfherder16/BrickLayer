"""Tests for the 3-layer BL-PluginEval scoring infrastructure.

Covers:
- Layer 1: Static analyzer (static_analyzer.py)
- Layer 3: Monte Carlo (monte_carlo.py)
- Elo ranking (elo_ranking.py)

Run with:
    python -m pytest masonry/tests/test_bl_plugin_eval.py -q
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


# Ensure repo root on path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from masonry.src.scoring.static_analyzer import (
    check_has_examples,
    check_has_output_contract,
    count_rules,
    parse_frontmatter,
    score_agent_file,
)
from masonry.src.scoring.monte_carlo import (
    MonteCarloResult,
    compute_elo_delta,
    run_monte_carlo,
)
from masonry.src.scoring.elo_ranking import (
    get_leaderboard,
    load_agent_db,
    update_elo,
)


# ---------------------------------------------------------------------------
# Static Analyzer — frontmatter tests
# ---------------------------------------------------------------------------

FULL_FRONTMATTER = """\
---
name: test-agent
description: A test agent for unit testing
model: sonnet
tools: bash, read
triggers: on-test
tier: trusted
---

## Output

Return JSON with verdict field.
"""

PARTIAL_FRONTMATTER = """\
---
name: partial-agent
description: Only name and description
---
"""

NO_FRONTMATTER = """\
# Agent without frontmatter

Some content here.
"""


def test_parse_frontmatter_complete():
    result = parse_frontmatter(FULL_FRONTMATTER)
    assert result["name"] == "test-agent"
    assert result["description"] == "A test agent for unit testing"
    assert result["model"] == "sonnet"


def test_parse_frontmatter_partial():
    result = parse_frontmatter(PARTIAL_FRONTMATTER)
    assert result["name"] == "partial-agent"
    assert result.get("model") is None


def test_parse_frontmatter_missing():
    result = parse_frontmatter(NO_FRONTMATTER)
    assert result == {} or result.get("name") is None


# ---------------------------------------------------------------------------
# Static Analyzer — output contract tests
# ---------------------------------------------------------------------------

def test_check_has_output_contract_found():
    content = "Some intro\n\n## Output\n\nReturn JSON.\n"
    assert check_has_output_contract(content) is True


def test_check_has_output_contract_return_keyword():
    content = "Do the thing.\n\nReturn: a dict with keys foo and bar.\n"
    assert check_has_output_contract(content) is True


def test_check_has_output_contract_missing():
    content = "Just a description with no output section.\n"
    assert check_has_output_contract(content) is False


# ---------------------------------------------------------------------------
# Static Analyzer — examples tests
# ---------------------------------------------------------------------------

def test_check_has_examples_code_block():
    content = "Intro text.\n\n```python\nprint('hello')\n```\n"
    assert check_has_examples(content) is True


def test_check_has_examples_narrative():
    content = "Intro.\n\nExample: run the script with --dry-run flag.\n"
    assert check_has_examples(content) is True


def test_check_has_examples_none():
    content = "No code blocks or examples here, just plain text.\n"
    assert check_has_examples(content) is False


# ---------------------------------------------------------------------------
# Static Analyzer — rule density tests
# ---------------------------------------------------------------------------

def test_count_rules_sweet_spot():
    lines = [f"- {'Never' if i % 3 == 0 else 'Always' if i % 3 == 1 else 'Must'} do thing {i}" for i in range(7)]
    content = "\n".join(lines)
    count = count_rules(content)
    assert count == 7


def test_count_rules_too_many():
    lines = [f"- Never do thing {i}" for i in range(25)]
    content = "\n".join(lines)
    assert count_rules(content) == 25


def test_count_rules_none():
    content = "No rules in this content at all.\n"
    assert count_rules(content) == 0


# ---------------------------------------------------------------------------
# Static Analyzer — score_agent_file
# ---------------------------------------------------------------------------

def test_score_agent_file_max_score():
    """A perfectly structured agent file should score 40."""
    content = (
        "---\nname: perfect-agent\ndescription: A great agent\nmodel: opus\n---\n\n"
        "## Output\n\nReturn JSON verdict.\n\n"
        "```python\nprint('example')\n```\n\n"
        "- Never skip validation\n"
        "- Always include evidence\n"
        "- Must cite sources\n"
        "- Never hallucinate\n"
        "- Always be concise\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name

    result = score_agent_file(tmp_path)
    assert result["total"] == 40
    assert result["frontmatter_complete"] == 10
    assert result["has_output_contract"] == 10
    assert result["has_examples"] == 10
    assert result["rule_density"] == 10


def test_score_agent_file_zero_score():
    """A bare file should score 0."""
    content = "# Just a title\n\nNo structure here.\n"
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name

    result = score_agent_file(tmp_path)
    assert result["total"] == 0


# ---------------------------------------------------------------------------
# Monte Carlo — accuracy and CI
# ---------------------------------------------------------------------------

def test_monte_carlo_accuracy():
    """All-pass test cases should yield accuracy = 1.0."""
    test_cases = [{"input": "q", "expected": "pass"} for _ in range(10)]

    def always_pass(agent_name: str, task: dict, base_dir: object) -> bool:
        return True

    result = run_monte_carlo(
        "test-agent",
        test_cases,
        n=20,
        base_dir=None,
        _run_fn=always_pass,
    )
    assert result.accuracy == 1.0
    assert result.n_trials == 20
    assert result.n_pass == 20


def test_monte_carlo_all_fail():
    """All-fail test cases should yield accuracy = 0.0."""
    test_cases = [{"input": "q", "expected": "pass"} for _ in range(10)]

    def always_fail(agent_name: str, task: dict, base_dir: object) -> bool:
        return False

    result = run_monte_carlo(
        "test-agent",
        test_cases,
        n=20,
        base_dir=None,
        _run_fn=always_fail,
    )
    assert result.accuracy == 0.0
    assert result.n_pass == 0


def test_monte_carlo_wilson_ci_within_bounds():
    """Wilson CI should be within [0, 1] and low <= accuracy <= high."""
    test_cases = [{"input": "q"} for _ in range(10)]
    call_count = [0]

    def half_pass(agent_name: str, task: dict, base_dir: object) -> bool:
        call_count[0] += 1
        return call_count[0] % 2 == 0

    result = run_monte_carlo("test-agent", test_cases, n=100, base_dir=None, _run_fn=half_pass)
    assert 0.0 <= result.wilson_ci_low <= result.accuracy
    assert result.accuracy <= result.wilson_ci_high <= 1.0


def test_monte_carlo_result_dataclass():
    """MonteCarloResult dataclass has required fields."""
    r = MonteCarloResult(
        n_trials=50,
        n_pass=30,
        accuracy=0.6,
        wilson_ci_low=0.46,
        wilson_ci_high=0.73,
        elo_delta=5.2,
    )
    assert r.n_trials == 50
    assert r.n_pass == 30
    assert abs(r.accuracy - 0.6) < 1e-9


# ---------------------------------------------------------------------------
# Monte Carlo — Elo delta
# ---------------------------------------------------------------------------

def test_compute_elo_delta_all_wins():
    """All wins against a 1200 opponent should give positive Elo delta."""
    delta = compute_elo_delta(wins=10, losses=0)
    assert delta > 0


def test_compute_elo_delta_all_losses():
    """All losses should give negative Elo delta."""
    delta = compute_elo_delta(wins=0, losses=10)
    assert delta < 0


def test_compute_elo_delta_equal():
    """Equal wins/losses against even opponent should be near zero."""
    delta = compute_elo_delta(wins=10, losses=10)
    assert abs(delta) < 5.0  # small delta near equilibrium


# ---------------------------------------------------------------------------
# Elo Ranking — load, update, leaderboard
# ---------------------------------------------------------------------------

def _make_temp_db(data: dict) -> Path:
    tmp = tempfile.mkdtemp()
    masonry_dir = Path(tmp) / "masonry"
    masonry_dir.mkdir()
    db_path = masonry_dir / "agent_db.json"
    db_path.write_text(json.dumps(data), encoding="utf-8")
    return Path(tmp)


def test_load_agent_db():
    data = {"agent-a": {"elo": 1200, "runs": 10}, "agent-b": {"elo": 1150, "runs": 5}}
    base = _make_temp_db(data)
    db = load_agent_db(base)
    assert "agent-a" in db
    assert db["agent-a"]["elo"] == 1200


def test_get_leaderboard_sorted():
    data = {
        "agent-a": {"elo": 1250},
        "agent-b": {"elo": 1100},
        "agent-c": {"elo": 1400},
    }
    base = _make_temp_db(data)
    board = get_leaderboard(base)
    names = [name for name, _ in board]
    assert names[0] == "agent-c"
    assert names[-1] == "agent-b"


def test_update_elo_writes_to_db():
    data = {"agent-x": {"elo": 1200, "runs": 5}}
    base = _make_temp_db(data)
    update_elo("agent-x", delta=32.0, base_dir=base)
    db = load_agent_db(base)
    assert db["agent-x"]["elo"] == 1232.0


def test_update_elo_creates_new_agent():
    data = {}
    base = _make_temp_db(data)
    update_elo("new-agent", delta=16.0, base_dir=base)
    db = load_agent_db(base)
    assert "new-agent" in db
    assert db["new-agent"]["elo"] == 1216.0  # 1200 base + 16
