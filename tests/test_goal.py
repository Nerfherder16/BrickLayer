"""Tests for bl/goal.py — goal-directed campaign question generation."""

import textwrap

import pytest

from bl.goal import (
    _build_prompt,
    _get_next_wave_index,
    _parse_goal,
    _parse_goal_questions,
)


# ---------------------------------------------------------------------------
# _parse_goal
# ---------------------------------------------------------------------------


def test_parse_goal_basic():
    text = textwrap.dedent("""
        # Research Goal
        **Goal**: Find memory leaks in the session layer
        **Target**: http://localhost:8200
        **Focus**: D5, D6
        **Max questions**: 8
        **Context**: Focus on Redis and Qdrant interactions
    """)
    result = _parse_goal(text)
    assert result["goal"] == "Find memory leaks in the session layer"
    assert result["target"] == "http://localhost:8200"
    assert result["focus"] == ["D5", "D6"]
    assert result["max_questions"] == 8
    assert "Redis" in result["context"]


def test_parse_goal_minimal():
    text = "**Goal**: Check API latency"
    result = _parse_goal(text)
    assert result["goal"] == "Check API latency"
    assert result["max_questions"] == 6  # default
    assert result["focus"] == []


def test_parse_goal_missing_goal_raises():
    with pytest.raises(ValueError, match="missing required \\*\\*Goal\\*\\*"):
        _parse_goal("**Target**: http://localhost:8200")


def test_parse_goal_invalid_max_questions_uses_default():
    text = "**Goal**: Test\n**Max questions**: not-a-number"
    result = _parse_goal(text)
    assert result["max_questions"] == 6


# ---------------------------------------------------------------------------
# _get_next_wave_index
# ---------------------------------------------------------------------------


def test_next_wave_index_empty():
    assert _get_next_wave_index("") == 1


def test_next_wave_index_after_qg_waves():
    text = "## QG1.1 ...\n## QG1.2 ...\n## QG2.1 ..."
    assert _get_next_wave_index(text) == 3


def test_next_wave_index_after_bl2_waves():
    text = "## D7.1 ...\n## D8.1 ..."
    assert _get_next_wave_index(text) == 9


def test_next_wave_index_mixed():
    text = "## QG3.1\n## D5.1"
    assert _get_next_wave_index(text) == 6  # max(3, 5) + 1


# ---------------------------------------------------------------------------
# _parse_goal_questions
# ---------------------------------------------------------------------------


def _make_block(n: int) -> str:
    return textwrap.dedent(f"""
        ## QG1.{n} [DIAGNOSE] Test question {n}
        **Operational Mode**: diagnose
        **Mode**: agent
        **Status**: PENDING
        **Hypothesis**: Something is wrong with {n}.
        **Test**: Run check_{n}()
        **Verdict threshold**:
        - FAILURE: check_{n} returns error
        - WARNING: check_{n} is slow
        - HEALTHY: check_{n} passes
        **Goal**: Tests goal aspect {n}
    """).strip()


def test_parse_goal_questions_valid():
    raw = "\n---\n".join([_make_block(1), _make_block(2), _make_block(3)])
    blocks = _parse_goal_questions(raw)
    assert len(blocks) == 3


def test_parse_goal_questions_skips_no_status():
    block_no_status = "## QG1.1 [DIAGNOSE] Title\n**Mode**: agent"
    block_valid = _make_block(1)
    raw = f"\n---\n{block_no_status}\n---\n{block_valid}"
    blocks = _parse_goal_questions(raw)
    assert len(blocks) == 1


def test_parse_goal_questions_skips_no_qg_header():
    block_no_header = "**Status**: PENDING\n**Mode**: agent\n**Hypothesis**: x"
    block_valid = _make_block(1)
    raw = f"{block_no_header}\n---\n{block_valid}"
    blocks = _parse_goal_questions(raw)
    assert len(blocks) == 1


def test_parse_goal_questions_empty_raw():
    assert _parse_goal_questions("") == []


# ---------------------------------------------------------------------------
# _build_prompt — runner context injection
# ---------------------------------------------------------------------------


def test_build_prompt_includes_runner_context():
    goal = {
        "goal": "Find latency regressions",
        "target": "http://localhost:8200",
        "focus": ["D1"],
        "max_questions": 3,
        "context": "",
    }
    runner_ctx = "- `http`: HTTP runner\n- `agent`: LLM agent runner"
    prompt = _build_prompt(
        goal, sim_context="", runner_context=runner_ctx, campaign_plan=""
    )
    assert "http" in prompt
    assert "LLM agent runner" in prompt


def test_build_prompt_includes_campaign_plan():
    goal = {
        "goal": "Test",
        "target": "",
        "focus": [],
        "max_questions": 2,
        "context": "",
    }
    plan = "## Targeting Brief\nPrioritize D1 and D5."
    prompt = _build_prompt(goal, sim_context="", runner_context="", campaign_plan=plan)
    assert "Targeting Brief" in prompt
    assert "Prioritize D1" in prompt


def test_build_prompt_works_without_runner_context():
    goal = {
        "goal": "Test",
        "target": "",
        "focus": [],
        "max_questions": 2,
        "context": "",
    }
    prompt = _build_prompt(goal, sim_context="")
    assert "QG1.1" in prompt  # example block still present
