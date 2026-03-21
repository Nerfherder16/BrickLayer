"""Sync finding verdicts to agent_db.json for drift detection.

Reads all finding files via extract_training_data(), groups verdicts
by agent (using questions.md attribution), and writes the verdict lists
back to agent_db.json using an atomic rename.

This populates the previously-empty ``verdicts`` field in agent_db.json,
enabling masonry_drift_check to function correctly (D7.1 fix).

Usage:
    python masonry/scripts/sync_verdicts_to_agent_db.py [--base-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def sync_verdicts(
    projects_dir: Path,
    agent_db_path: Path,
    questions_md_path: Path | None = None,
) -> dict[str, int]:
    """Populate agent_db.json ``verdicts`` from campaign findings.

    Args:
        projects_dir: Root directory to scan for findings (rglob for findings/).
        agent_db_path: Path to agent_db.json to update.
        questions_md_path: Optional override for questions.md path.

    Returns:
        Dict mapping agent_name -> number of verdicts written.
    """
    # Import here to allow running from repo root without install
    sys.path.insert(0, str(agent_db_path.parent.parent))
    from masonry.src.dspy_pipeline.training_extractor import extract_training_data  # noqa: PLC0415

    # Load current agent_db
    agent_db: dict = {}
    try:
        agent_db = json.loads(agent_db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Cannot read {agent_db_path}: {exc}", file=sys.stderr)
        return {}

    # Extract all attributed findings
    findings = extract_training_data(projects_dir, questions_md_path=questions_md_path)

    # Group verdicts by agent
    verdicts_by_agent: dict[str, list[str]] = defaultdict(list)
    for finding in findings:
        agent = finding.get("agent")
        verdict = finding.get("verdict", "")
        if agent and verdict:
            verdicts_by_agent[agent].append(verdict)

    # Valid agent names: lowercase letters, digits, and hyphens only, start with lowercase letter.
    import re as _re
    _valid_agent_name = _re.compile(r"^[a-z][a-z0-9-]*$")

    # Remove any garbage keys that were accidentally written by previous runs.
    for k in [k for k in list(agent_db.keys()) if not _valid_agent_name.match(k)]:
        del agent_db[k]

    # Update agent_db with new verdicts — only for valid known agents
    written: dict[str, int] = {}
    for agent_name, verdicts in verdicts_by_agent.items():
        if _valid_agent_name.match(agent_name) and agent_name in agent_db:
            agent_db[agent_name]["verdicts"] = verdicts
            written[agent_name] = len(verdicts)

    # Atomic write
    tmp_path = agent_db_path.with_suffix(f".json.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(json.dumps(agent_db, indent=2), encoding="utf-8")
        tmp_path.replace(agent_db_path)
    except Exception as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        print(f"ERROR: Failed to write {agent_db_path}: {exc}", file=sys.stderr)
        return {}

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="Repository root directory (default: 3 levels up from this script)",
    )
    parser.add_argument(
        "--questions-md",
        type=Path,
        default=None,
        help="Explicit path to questions.md (default: auto-discover per project)",
    )
    args = parser.parse_args()

    base_dir = args.base_dir.resolve()
    agent_db_path = base_dir / "agent_db.json"

    if not agent_db_path.exists():
        print(f"ERROR: {agent_db_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Syncing verdicts from {base_dir} to {agent_db_path}...")
    result = sync_verdicts(base_dir, agent_db_path, questions_md_path=args.questions_md)

    if not result:
        print("No verdicts found or write failed.", file=sys.stderr)
        sys.exit(1)

    total = sum(result.values())
    print(f"Wrote {total} verdicts across {len(result)} agents:")
    for agent, count in sorted(result.items()):
        print(f"  {agent}: {count} verdicts")


if __name__ == "__main__":
    main()
