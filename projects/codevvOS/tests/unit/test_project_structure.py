"""
Task 0.1 — Monorepo Directory Structure
Tests that the required directory and file structure exists.
These tests are written BEFORE the structure is created — they will fail until
the developer implements the production layout.
"""

import json
import os
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Required directories
# ---------------------------------------------------------------------------

REQUIRED_DIRS = [
    "backend",
    "backend/app",
    "frontend",
    "shared",
    "migrations",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "tests/migrations",
    "tests/workers",
    "docker",
    ".github/workflows",
]


@pytest.mark.parametrize("rel_path", REQUIRED_DIRS)
def test_required_directory_exists(rel_path):
    full_path = PROJECT_ROOT / rel_path
    assert full_path.is_dir(), f"Required directory missing: {full_path}"


# ---------------------------------------------------------------------------
# Required files
# ---------------------------------------------------------------------------

REQUIRED_FILES = [
    "backend/app/__init__.py",
    "backend/pyproject.toml",
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "shared/auth.py",
    "shared/auth.js",
    "migrations/env.py",
    "migrations/alembic.ini",
    ".gitignore",
]


@pytest.mark.parametrize("rel_path", REQUIRED_FILES)
def test_required_file_exists(rel_path):
    full_path = PROJECT_ROOT / rel_path
    assert full_path.is_file(), f"Required file missing: {full_path}"


# ---------------------------------------------------------------------------
# File content validations
# ---------------------------------------------------------------------------


def test_backend_pyproject_toml_parses():
    toml_path = PROJECT_ROOT / "backend" / "pyproject.toml"
    assert toml_path.is_file(), f"File missing: {toml_path}"
    content = toml_path.read_bytes()
    # tomllib.loads requires str; tomllib.load requires binary file
    try:
        parsed = tomllib.loads(content.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        pytest.fail(f"backend/pyproject.toml is not valid TOML: {exc}")
    assert isinstance(parsed, dict), "pyproject.toml did not parse to a dict"


def test_frontend_package_json_parses():
    json_path = PROJECT_ROOT / "frontend" / "package.json"
    assert json_path.is_file(), f"File missing: {json_path}"
    content = json_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        pytest.fail(f"frontend/package.json is not valid JSON: {exc}")
    assert isinstance(parsed, dict), "package.json did not parse to a dict"


def test_gitignore_contains_node_modules():
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.is_file(), f"File missing: {gitignore_path}"
    content = gitignore_path.read_text(encoding="utf-8")
    assert "node_modules" in content, ".gitignore must contain 'node_modules'"


def test_gitignore_contains_pycache():
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.is_file(), f"File missing: {gitignore_path}"
    content = gitignore_path.read_text(encoding="utf-8")
    assert "__pycache__" in content, ".gitignore must contain '__pycache__'"
