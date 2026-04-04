"""Canonical scoring rubrics per agent category.

These are hardcoded invariants — they define what makes a good agent output
for each category. Never change without human review.
"""

from __future__ import annotations
from typing import TypedDict


class Rubric(TypedDict):
    dimensions: dict[str, int]   # dimension_name -> max_points
    min_training_score: int       # minimum score to include in training data


# Agent category assignments — map agent name → category
AGENT_CATEGORIES: dict[str, str] = {
    # findings category
    "quantitative-analyst": "findings",
    "regulatory-researcher": "findings",
    "competitive-analyst": "findings",
    "research-analyst": "findings",
    "benchmark-engineer": "findings",
    "diagnose-analyst": "findings",
    "hypothesis-generator-bl2": "findings",
    "synthesizer": "findings",
    "synthesizer-bl2": "findings",
    "peer-reviewer": "findings",
    "design-reviewer": "findings",
    "code-reviewer": "findings",
    "compliance-auditor": "findings",
    "cascade-analyst": "findings",
    "frontier-analyst": "findings",
    "health-monitor": "findings",
    "evolve-optimizer": "findings",
    "question-designer-bl2": "findings",
    "planner": "findings",
    "pointer": "findings",
    "retrospective": "findings",
    "spec-writer": "findings",
    # code category
    "developer": "code",
    "test-writer": "code",
    "fix-implementer": "code",
    "refactorer": "code",
    # ops category
    "git-nerd": "ops",
    "karen": "ops",
    "forge-check": "ops",
    "overseer": "ops",
    "agent-auditor": "ops",
    "skill-forge": "ops",
    "mcp-advisor": "ops",
    # routing category
    "mortar": "routing",
    "trowel": "routing",
    # general category (catch-all for multi-purpose subagents)
    "general-purpose": "findings",
}

RUBRICS: dict[str, Rubric] = {
    "findings": {
        "dimensions": {
            "confidence_calibration": 40,
            "evidence_quality": 40,
            "verdict_clarity": 20,
        },
        "min_training_score": 60,
    },
    "code": {
        "dimensions": {
            "tests_pass": 50,
            "lint_clean": 20,
            "no_regression": 30,
        },
        "min_training_score": 70,
    },
    "ops": {
        "dimensions": {
            "operation_succeeded": 60,
            "human_accepted": 40,
        },
        "min_training_score": 60,
    },
    "routing": {
        "dimensions": {
            "correct_agent_dispatched": 70,
            "downstream_success": 30,
        },
        "min_training_score": 65,
    },
}


def get_category(agent_name: str) -> str:
    """Return the category for a given agent name, defaulting to 'findings'."""
    return AGENT_CATEGORIES.get(agent_name.lower().strip(), "findings")


def get_rubric(agent_name: str) -> Rubric:
    """Return the scoring rubric for a given agent name."""
    category = get_category(agent_name)
    return RUBRICS[category]


def max_score(agent_name: str) -> int:
    """Return the maximum possible score for a given agent's category."""
    rubric = get_rubric(agent_name)
    return sum(rubric["dimensions"].values())


def min_training_score(agent_name: str) -> int:
    """Return the minimum score required for training data inclusion."""
    return get_rubric(agent_name)["min_training_score"]
