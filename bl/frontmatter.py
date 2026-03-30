"""bl/frontmatter.py — YAML frontmatter parsing utilities for agent files."""

from bl.tmux.helpers import MODEL_MAP


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from a markdown file."""
    if not text.startswith("---"):
        return text
    try:
        end = text.index("---", 3)
        return text[end + 3 :].strip()
    except ValueError:
        return text


def read_frontmatter_model(text: str) -> str | None:
    """Extract the `model:` field from YAML frontmatter, mapped to full model ID."""
    if not text.startswith("---"):
        return None
    try:
        end = text.index("---", 3)
        fm = text[3:end]
    except ValueError:
        return None
    for line in fm.splitlines():
        if line.strip().startswith("model:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            return MODEL_MAP.get(value, value) or None
    return None
