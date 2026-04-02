"""Tests for Python linting and formatting configuration."""

import tomllib
from pathlib import Path


PYPROJECT_PATH = Path(__file__).parent.parent.parent / "backend" / "pyproject.toml"


def _load_pyproject() -> dict:
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)


def test_ruff_section_exists():
    config = _load_pyproject()
    assert "tool" in config
    assert "ruff" in config["tool"], "[tool.ruff] section missing from pyproject.toml"


def test_ruff_line_length_is_100():
    config = _load_pyproject()
    ruff = config["tool"]["ruff"]
    assert ruff.get("line-length") == 100, f"Expected line-length=100, got {ruff.get('line-length')}"


def test_ruff_target_version_is_py312():
    config = _load_pyproject()
    ruff = config["tool"]["ruff"]
    assert ruff.get("target-version") == "py312", (
        f"Expected target-version='py312', got {ruff.get('target-version')}"
    )


def test_ruff_lint_section_exists():
    config = _load_pyproject()
    ruff = config["tool"]["ruff"]
    assert "lint" in ruff, "[tool.ruff.lint] section missing from pyproject.toml"


def test_mypy_section_exists():
    config = _load_pyproject()
    assert "mypy" in config["tool"], "[tool.mypy] section missing from pyproject.toml"


def test_mypy_strict_is_true():
    config = _load_pyproject()
    mypy = config["tool"]["mypy"]
    assert mypy.get("strict") is True, f"Expected mypy strict=true, got {mypy.get('strict')}"
