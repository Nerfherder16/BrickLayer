"""
Tests for .gitignore — verify **/.mas/ pattern is present and ordered correctly.

Run with: python -m pytest tests/test_gitignore_mas.py --capture=no -q
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GITIGNORE = REPO_ROOT / ".gitignore"


def read_gitignore() -> str:
    return GITIGNORE.read_text(encoding="utf-8")


def test_mas_pattern_present():
    """**/.mas/ must be in .gitignore."""
    content = read_gitignore()
    lines = content.splitlines()
    assert "**/.mas/" in lines, "**/.mas/ should be a standalone line in .gitignore"


def test_omc_pattern_still_present():
    """**/.omc/ must still be in .gitignore (legacy dirs may exist on old clones)."""
    content = read_gitignore()
    lines = content.splitlines()
    assert "**/.omc/" in lines, "**/.omc/ should still be present in .gitignore"


def test_mas_before_omc():
    """**/.mas/ must appear before **/.omc/ in .gitignore."""
    content = read_gitignore()
    lines = content.splitlines()
    mas_idx = next((i for i, l in enumerate(lines) if l == "**/.mas/"), None)
    omc_idx = next((i for i, l in enumerate(lines) if l == "**/.omc/"), None)
    assert mas_idx is not None, "**/.mas/ not found"
    assert omc_idx is not None, "**/.omc/ not found"
    assert mas_idx < omc_idx, f"**/.mas/ (line {mas_idx}) must come before **/.omc/ (line {omc_idx})"
