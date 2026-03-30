"""Frontmatter validation for Masonry agent .md files.

Validates YAML frontmatter completeness for semantic routing quality.
Returns warnings only — does NOT block onboarding.

Usage:
    from masonry.scripts.validate_frontmatter import validate_frontmatter
    warnings = validate_frontmatter(meta_dict)
"""

from __future__ import annotations

from typing import Any

_VALID_MODELS = {"opus", "sonnet", "haiku"}
_VALID_TIERS = {"production", "candidate", "draft"}


def validate_frontmatter(meta: dict[str, Any]) -> list[str]:
    """Validate frontmatter completeness for semantic routing.

    Returns a list of warning strings (empty = valid). Does NOT block
    onboarding — warnings only.
    """
    warnings: list[str] = []

    name = meta.get("name", "")
    if not name or not str(name).strip():
        warnings.append("name: missing or empty")

    description = str(meta.get("description", "") or "")
    if not description.strip():
        warnings.append("description: missing or empty (needed for semantic routing)")
    elif len(description.strip()) < 20:
        warnings.append(
            f"description: too short ({len(description.strip())} chars, need >= 20 for semantic routing)"
        )

    model = str(meta.get("model", "") or "")
    if model and model not in _VALID_MODELS:
        warnings.append(f"model: '{model}' not in {sorted(_VALID_MODELS)}")

    tier = str(meta.get("tier", "") or "")
    if tier and tier not in _VALID_TIERS:
        warnings.append(f"tier: '{tier}' not in {sorted(_VALID_TIERS)}")

    modes = meta.get("modes")
    if modes is not None and not isinstance(modes, list):
        warnings.append(f"modes: expected list, got {type(modes).__name__}")

    capabilities = meta.get("capabilities")
    if capabilities is not None and not isinstance(capabilities, list):
        warnings.append(
            f"capabilities: expected list, got {type(capabilities).__name__}"
        )

    return warnings
