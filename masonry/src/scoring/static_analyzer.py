"""Layer 1 static analysis — scores agent .md files on structure quality."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_OUTPUT_CONTRACT_RE = re.compile(r"(^#{1,3}\s*Output\b|Return\s*:)", re.MULTILINE | re.IGNORECASE)
_EXAMPLE_RE = re.compile(r"(```|\bExample\s*:)", re.IGNORECASE)
_RULE_LINE_RE = re.compile(r"^\s*[-*]\s+.*(Never|Always|Must)\b", re.MULTILINE | re.IGNORECASE)
_RULE_SWEET_MIN = 3
_RULE_SWEET_MAX = 20
_REQUIRED_FRONTMATTER = {"name", "description", "model"}


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract and parse YAML frontmatter between --- delimiters."""
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def check_has_output_contract(content: str) -> bool:
    """True if the file has an Output section or Return: keyword."""
    return bool(_OUTPUT_CONTRACT_RE.search(content))


def check_has_examples(content: str) -> bool:
    """True if the file has a code block or Example: reference."""
    return bool(_EXAMPLE_RE.search(content))


def count_rules(content: str) -> int:
    """Count bullet lines containing Never/Always/Must."""
    return len(_RULE_LINE_RE.findall(content))


def score_agent_file(path: str) -> dict[str, int]:
    """Score an agent .md file across four dimensions, max 40 total."""
    content = Path(path).read_text(encoding="utf-8")

    fm = parse_frontmatter(content)
    frontmatter_complete = 10 if _REQUIRED_FRONTMATTER.issubset(fm.keys()) else 0
    has_output_contract = 10 if check_has_output_contract(content) else 0
    has_examples = 10 if check_has_examples(content) else 0
    n_rules = count_rules(content)
    rule_density = 10 if _RULE_SWEET_MIN <= n_rules <= _RULE_SWEET_MAX else 0

    return {
        "frontmatter_complete": frontmatter_complete,
        "has_output_contract": has_output_contract,
        "has_examples": has_examples,
        "rule_density": rule_density,
        "total": frontmatter_complete + has_output_contract + has_examples + rule_density,
    }
