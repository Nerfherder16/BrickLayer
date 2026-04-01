"""Layer 1: Static analysis of agent .md files for structural quality.

Scores agent files across four dimensions (10 pts each, 40 total):
  - frontmatter_complete
  - has_output_contract
  - has_examples
  - rule_density
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from a markdown string.

    Returns a dict of key→value pairs. Returns empty dict if no frontmatter.
    """
    content = content.strip()
    if not content.startswith("---"):
        return {}

    # Find the closing ---
    end_match = re.search(r"\n---", content[3:])
    if end_match is None:
        return {}

    raw_yaml = content[3 : end_match.start() + 3]
    result: dict[str, Any] = {}
    for line in raw_yaml.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key:
                result[key] = value if value else None
    return result


def check_has_output_contract(content: str) -> bool:
    """Return True if the content has an ## Output section or 'Return:' line."""
    if re.search(r"^##\s+Output", content, re.MULTILINE | re.IGNORECASE):
        return True
    if re.search(r"^Return:", content, re.MULTILINE):
        return True
    return False


def check_has_examples(content: str) -> bool:
    """Return True if the content has code blocks or 'Example:' sections."""
    # Code block (fenced)
    if re.search(r"```", content):
        return True
    # Narrative example
    if re.search(r"^Example:", content, re.MULTILINE | re.IGNORECASE):
        return True
    return False


def count_rules(content: str) -> int:
    """Count lines matching '- Never', '- Always', or '- Must'."""
    matches = re.findall(r"^\s*-\s+(Never|Always|Must)\b", content, re.MULTILINE)
    return len(matches)


def _score_frontmatter(fm: dict[str, Any]) -> int:
    """10 if name+description+model all present, 5 if partial, 0 if empty."""
    if not fm:
        return 0
    required = {"name", "description", "model"}
    present = {k for k in required if fm.get(k)}
    if len(present) == 3:
        return 10
    if len(present) >= 1:
        return 5
    return 0


def _score_rule_density(count: int) -> int:
    """10 for 3–15 rules, 5 for 1–2 or 16–20, 0 for 0 or >20."""
    if 3 <= count <= 15:
        return 10
    if 1 <= count <= 2 or 16 <= count <= 20:
        return 5
    return 0


def score_agent_file(filepath: str | Path) -> dict[str, int]:
    """Score an agent .md file across four structural dimensions.

    Returns dict with keys:
      frontmatter_complete, has_output_contract, has_examples,
      rule_density, total
    """
    content = Path(filepath).read_text(encoding="utf-8")

    fm = parse_frontmatter(content)
    frontmatter_score = _score_frontmatter(fm)
    output_score = 10 if check_has_output_contract(content) else 0
    examples_score = 10 if check_has_examples(content) else 0
    rule_score = _score_rule_density(count_rules(content))

    return {
        "frontmatter_complete": frontmatter_score,
        "has_output_contract": output_score,
        "has_examples": examples_score,
        "rule_density": rule_score,
        "total": frontmatter_score + output_score + examples_score + rule_score,
    }
