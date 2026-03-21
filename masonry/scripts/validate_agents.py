"""Validate Masonry agent .md files against the canonical frontmatter schema.

Checks each agent file for required fields, correct values, and naming
consistency. Reports violations; does NOT modify files.

CLI usage:
    python masonry/scripts/validate_agents.py [--agents-dir PATH ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SKIP_STEMS = frozenset({"SCHEMA", "AGENTS", "README", "INDEX", "AUDIT_REPORT"})

VALID_MODELS = frozenset({"haiku", "sonnet", "opus"})

VALID_MODES = frozenset({
    "simulate", "diagnose", "fix", "audit", "research",
    "benchmark", "validate", "evolve", "monitor", "predict",
    "frontier", "agent",
})

VALID_TIERS = frozenset({"draft", "candidate", "trusted", "retired"})

_MIN_DESCRIPTION_LENGTH = 30

_DEFAULT_AGENTS_DIRS: list[Path] = [
    Path.home() / ".claude" / "agents",
    Path(".claude") / "agents",
]


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a .md file.

    Args:
        path: Path to the .md file.

    Returns:
        Dict of frontmatter fields, or empty dict if none found or parse error.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        fm = yaml.safe_load(parts[1]) or {}
        return fm if isinstance(fm, dict) else {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


def _validate_file(md_path: Path) -> list[dict[str, str]]:
    """Validate a single agent .md file.

    Args:
        md_path: Path to the agent file.

    Returns:
        List of violation dicts, each with 'filename', 'field', 'reason'.
        Empty list means the file is valid.
    """
    filename = md_path.name
    fm = _parse_frontmatter(md_path)
    violations: list[dict[str, str]] = []

    def _add(field: str, reason: str) -> None:
        violations.append({"filename": filename, "field": field, "reason": reason})

    # ── name ────────────────────────────────────────────────────────────────
    name = fm.get("name")
    if not name:
        _add("name", "field is missing or empty")
    elif str(name) != md_path.stem:
        _add(
            "name",
            f"value '{name}' does not match filename stem '{md_path.stem}'",
        )

    # ── model ────────────────────────────────────────────────────────────────
    model = fm.get("model")
    if not model:
        _add("model", "field is missing or empty")
    elif str(model) not in VALID_MODELS:
        _add("model", f"'{model}' is not one of: {sorted(VALID_MODELS)}")

    # ── description ──────────────────────────────────────────────────────────
    description = fm.get("description")
    if not description:
        _add("description", "field is missing or empty")
    elif len(str(description)) < _MIN_DESCRIPTION_LENGTH:
        _add(
            "description",
            f"too short ({len(str(description))} chars); minimum is {_MIN_DESCRIPTION_LENGTH}",
        )

    # ── modes ────────────────────────────────────────────────────────────────
    modes = fm.get("modes")
    if modes is None:
        _add("modes", "field is missing")
    elif not isinstance(modes, list):
        _add("modes", "must be a list")
    else:
        invalid = [m for m in modes if str(m) not in VALID_MODES]
        if invalid:
            _add(
                "modes",
                f"invalid values {invalid}; must be subset of {sorted(VALID_MODES)}",
            )

    # ── capabilities ─────────────────────────────────────────────────────────
    capabilities = fm.get("capabilities")
    if capabilities is None:
        _add("capabilities", "field is missing")
    elif not isinstance(capabilities, list):
        _add("capabilities", "must be a list")
    elif len(capabilities) < 2:
        _add("capabilities", f"must have at least 2 items; found {len(capabilities)}")

    # ── input_schema ─────────────────────────────────────────────────────────
    if not fm.get("input_schema"):
        _add("input_schema", "field is missing or empty")

    # ── output_schema ────────────────────────────────────────────────────────
    if not fm.get("output_schema"):
        _add("output_schema", "field is missing or empty")

    # ── tier ─────────────────────────────────────────────────────────────────
    tier = fm.get("tier")
    if not tier:
        _add("tier", "field is missing or empty")
    elif str(tier) not in VALID_TIERS:
        _add("tier", f"'{tier}' is not one of: {sorted(VALID_TIERS)}")

    return violations


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------


def validate_agents_dir(agents_dirs: list[Path]) -> list[dict[str, str]]:
    """Validate all agent .md files across the given directories.

    Skips files whose stem (uppercased) matches _SKIP_STEMS.

    Args:
        agents_dirs: Directories to scan.

    Returns:
        List of all violation dicts from all files.
    """
    all_violations: list[dict[str, str]] = []

    for agents_dir in agents_dirs:
        if not agents_dir.is_dir():
            continue
        for md_file in sorted(agents_dir.glob("*.md")):
            if md_file.stem.upper() in _SKIP_STEMS:
                continue
            file_violations = _validate_file(md_file)
            all_violations.extend(file_violations)

    return all_violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Masonry agent .md files against the canonical schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agents-dir",
        action="append",
        dest="agents_dirs",
        metavar="PATH",
        help="Directory to scan for agent .md files (repeatable). "
        f"Defaults: {[str(d) for d in _DEFAULT_AGENTS_DIRS]}",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    agents_dirs: list[Path] = (
        [Path(d) for d in args.agents_dirs]
        if args.agents_dirs
        else _DEFAULT_AGENTS_DIRS
    )

    violations = validate_agents_dir(agents_dirs)

    # Tally unique files checked
    checked_files: set[str] = set()
    for agents_dir in agents_dirs:
        if not agents_dir.is_dir():
            continue
        for md_file in agents_dir.glob("*.md"):
            if md_file.stem.upper() not in _SKIP_STEMS:
                checked_files.add(md_file.name)

    for v in violations:
        print(f"FAIL: {v['filename']}: {v['field']} — {v['reason']}")

    print(f"\n{len(checked_files)} files checked, {len(violations)} violations found")

    sys.exit(0 if not violations else 1)


if __name__ == "__main__":
    main()
