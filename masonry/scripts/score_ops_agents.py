"""Score ops agents (git-nerd, karen, forge-check, overseer) from operational artifacts.

Signal sources:
- git-nerd: git log for commits with automated commit patterns
- karen: git log for CHANGELOG.md / ARCHITECTURE.md / ROADMAP.md modifications
- forge-check: FORGE_NEEDED.md creation + subsequent agent .md files
- overseer: AUDIT_REPORT.md creation + tier promotions in agent_registry.yml

Score dimensions: operation_succeeded (60pts), human_accepted (40pts proxy via no revert)
Min score 60.

Usage:
    python masonry/scripts/score_ops_agents.py [--base-dir DIR] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Import rubrics — graceful degradation
# ---------------------------------------------------------------------------

try:
    from masonry.src.scoring.rubrics import min_training_score
except ImportError:
    def min_training_score(agent_name: str) -> int:  # type: ignore[misc]
        return 60


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

_RE_AUTO_COMMIT = re.compile(
    r"(Co-Authored-By: Claude|Co-authored-by: Claude|🤖|automated commit|"
    r"chore: auto-|feat\(.*autopilot|fix\(.*autopilot|git-nerd)",
    re.IGNORECASE,
)

_RE_REVERT = re.compile(r'^Revert "', re.IGNORECASE)

_ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"


def _git_log(base_dir: Path, fmt: str, extra_args: list[str] | None = None) -> list[str]:
    """Run git log with the given format string and return non-empty lines."""
    cmd = ["git", "log", f"--format={fmt}"] + (extra_args or [])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(base_dir),
            timeout=15,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []


def _git_log_name_only(base_dir: Path) -> list[dict[str, Any]]:
    """Return commits with their changed files.

    Each entry: {hash, date_iso, subject, files: [str]}
    """
    try:
        result = subprocess.run(
            ["git", "log", "--name-only", "--format=COMMIT:%H %aI %s"],
            capture_output=True,
            text=True,
            cwd=str(base_dir),
            timeout=30,
        )
        if result.returncode != 0:
            return []
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return []

    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in result.stdout.splitlines():
        if line.startswith("COMMIT:"):
            if current is not None:
                commits.append(current)
            rest = line[len("COMMIT:"):].strip()
            parts = rest.split(" ", 2)
            current = {
                "hash": parts[0] if len(parts) > 0 else "",
                "date_iso": parts[1] if len(parts) > 1 else "",
                "subject": parts[2] if len(parts) > 2 else "",
                "files": [],
            }
        elif line.strip() and current is not None:
            current["files"].append(line.strip())

    if current is not None:
        commits.append(current)

    return commits


def _parse_iso(date_str: str) -> datetime | None:
    """Parse an ISO 8601 datetime string, return None on failure."""
    try:
        # Python 3.7+ fromisoformat doesn't handle all ISO variants
        # Replace Z with +00:00 for compatibility
        normalized = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, AttributeError):
        return None


def _was_reverted_within(
    commit_hash: str,
    commit_date: datetime,
    all_commits: list[dict[str, Any]],
    window_hours: int = 24,
) -> bool:
    """Return True if commit_hash was reverted within window_hours of commit_date."""
    cutoff = commit_date + timedelta(hours=window_hours)
    for commit in all_commits:
        if not _RE_REVERT.search(commit.get("subject", "")):
            continue
        revert_date = _parse_iso(commit.get("date_iso", ""))
        if revert_date is None:
            continue
        if commit_date <= revert_date <= cutoff:
            # Check if the revert subject references our commit
            if commit_hash[:7] in commit.get("subject", ""):
                return True
    return False


# ---------------------------------------------------------------------------
# Agent scorers
# ---------------------------------------------------------------------------


def _score_git_nerd(base_dir: Path, all_commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score git-nerd from auto-commit patterns in git log."""
    records: list[dict[str, Any]] = []

    for commit in all_commits:
        subject = commit.get("subject", "")
        if not _RE_AUTO_COMMIT.search(subject):
            continue

        commit_date = _parse_iso(commit.get("date_iso", ""))
        reverted = False
        if commit_date is not None:
            reverted = _was_reverted_within(commit["hash"], commit_date, all_commits)

        op_succeeded = 60  # commit exists
        human_accepted = 0 if reverted else 40
        total = op_succeeded + human_accepted

        if total >= min_training_score("git-nerd"):
            records.append({
                "agent": "git-nerd",
                "source": "git_log",
                "commit_hash": commit["hash"][:12],
                "score": total,
                "score_breakdown": {
                    "operation_succeeded": op_succeeded,
                    "human_accepted": human_accepted,
                },
                "input": {"commit_subject": subject[:200]},
                "output": {"committed": True, "reverted": reverted},
            })

    return records


_KAREN_FILES = frozenset({
    "CHANGELOG.md", "ARCHITECTURE.md", "ROADMAP.md",
    "changelog.md", "architecture.md", "roadmap.md",
})

_RE_KAREN_COMMIT = re.compile(
    r"(karen|chore:.*changelog|docs:.*roadmap|docs:.*architecture|update.*CHANGELOG)",
    re.IGNORECASE,
)


_RE_BOT_COMMIT = re.compile(r"^chore:\s+update\s+CHANGELOG\s+for\s+[0-9a-f]{7,}", re.IGNORECASE)


def _score_karen(base_dir: Path, all_commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score karen from CHANGELOG/ARCHITECTURE/ROADMAP file modifications.

    Training record structure (fixed):
    - input.commit_subject: the PARENT commit subject (the commit that triggered karen)
    - input.files_modified: the PARENT commit's non-doc source files
    - output.doc_files_written: how many doc files karen wrote in the current commit
    - output.reverted: whether the current commit was later reverted

    This gives karen the correct context: "given this source change, should you document it?"
    Previously the current commit's doc files were used, causing the model to infer
    "docs already written → skip" for all training examples.
    """
    records: list[dict[str, Any]] = []

    for idx, commit in enumerate(all_commits):
        files = commit.get("files", [])
        subject = commit.get("subject", "")

        # Match either by subject or by files touched
        karen_files = [f for f in files if Path(f).name in _KAREN_FILES]
        if not karen_files and not _RE_KAREN_COMMIT.search(subject):
            continue

        # Find parent commit (all_commits is newest-first, so parent = idx+1)
        parent = all_commits[idx + 1] if idx + 1 < len(all_commits) else None
        if parent is None:
            continue  # No parent — skip first commit in history

        # Use parent's non-doc source files as the trigger context for karen
        parent_subject = parent.get("subject", "")
        parent_files = parent.get("files", [])
        source_files = [f for f in parent_files if Path(f).name not in _KAREN_FILES]

        # Skip if parent is itself a bot commit — those don't represent real trigger context
        if _RE_BOT_COMMIT.search(parent_subject):
            continue

        commit_date = _parse_iso(commit.get("date_iso", ""))
        reverted = False
        if commit_date is not None:
            reverted = _was_reverted_within(commit["hash"], commit_date, all_commits)

        op_succeeded = 60
        human_accepted = 0 if reverted else 40
        total = op_succeeded + human_accepted

        if total >= min_training_score("karen"):
            records.append({
                "agent": "karen",
                "source": "git_log",
                "commit_hash": commit["hash"][:12],
                "score": total,
                "score_breakdown": {
                    "operation_succeeded": op_succeeded,
                    "human_accepted": human_accepted,
                },
                "input": {
                    "commit_subject": parent_subject[:200],
                    "files_modified": source_files,
                },
                "output": {"doc_files_written": len(karen_files), "reverted": reverted},
            })

    return records


def _score_forge_check(base_dir: Path) -> list[dict[str, Any]]:
    """Score forge-check from FORGE_NEEDED.md + subsequent agent .md creation."""
    forge_needed = base_dir / "FORGE_NEEDED.md"
    agents_dir = base_dir / "agents"
    masonry_agents = base_dir / "masonry" / "agents"

    if not forge_needed.exists():
        return []

    # Find .md files in agents directories created after FORGE_NEEDED.md
    forge_mtime = forge_needed.stat().st_mtime
    new_agents: list[str] = []

    for agents_parent in (agents_dir, masonry_agents):
        if not agents_parent.is_dir():
            continue
        for md_file in agents_parent.glob("*.md"):
            if md_file.stat().st_mtime > forge_mtime:
                new_agents.append(md_file.name)

    if not new_agents:
        return []

    op_succeeded = 60
    human_accepted = 40  # Presence of new agents = accepted
    total = op_succeeded + human_accepted

    if total >= min_training_score("forge-check"):
        return [{
            "agent": "forge-check",
            "source": "filesystem",
            "score": total,
            "score_breakdown": {
                "operation_succeeded": op_succeeded,
                "human_accepted": human_accepted,
            },
            "input": {"forge_needed_exists": True},
            "output": {"new_agents_created": new_agents},
        }]
    return []


def _score_overseer(base_dir: Path) -> list[dict[str, Any]]:
    """Score overseer from AUDIT_REPORT.md + tier promotions in agent_registry.yml."""
    audit_report = base_dir / "masonry" / "AUDIT_REPORT.md"
    registry_path = base_dir / "masonry" / "agent_registry.yml"

    if not audit_report.exists():
        return []

    # Check for tier promotions in agent_registry.yml
    promotions_found = False
    if registry_path.exists():
        try:
            registry_text = registry_path.read_text(encoding="utf-8")
            # Look for trusted or candidate tier entries
            if re.search(r"tier:\s*(trusted|candidate)", registry_text):
                promotions_found = True
        except OSError:
            pass

    op_succeeded = 60  # audit report exists
    human_accepted = 40 if promotions_found else 20
    total = op_succeeded + human_accepted

    if total >= min_training_score("overseer"):
        return [{
            "agent": "overseer",
            "source": "filesystem",
            "score": total,
            "score_breakdown": {
                "operation_succeeded": op_succeeded,
                "human_accepted": human_accepted,
            },
            "input": {"audit_report_exists": True},
            "output": {"tier_promotions_found": promotions_found},
        }]
    return []


# ---------------------------------------------------------------------------
# Main run function
# ---------------------------------------------------------------------------


def run(
    base_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Score ops agents from operational artifacts.

    Returns summary: {total_records, agents_covered, output_path}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_commits = _git_log_name_only(base_dir)

    all_records: list[dict[str, Any]] = []
    all_records.extend(_score_git_nerd(base_dir, all_commits))
    all_records.extend(_score_karen(base_dir, all_commits))
    all_records.extend(_score_forge_check(base_dir))
    all_records.extend(_score_overseer(base_dir))

    agents_covered: set[str] = {rec["agent"] for rec in all_records}

    with output_path.open("w", encoding="utf-8") as fh:
        for rec in all_records:
            fh.write(json.dumps(rec) + "\n")

    return {
        "total_records": len(all_records),
        "agents_covered": sorted(agents_covered),
        "output_path": str(output_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(description="Score ops agents from operational artifacts.")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("masonry/training_data/scored_ops_agents.jsonl"),
    )
    args = parser.parse_args()

    summary = run(base_dir=args.base_dir, output_path=args.output)
    print(f"Training records written: {summary['total_records']}")
    print(f"Agents covered: {', '.join(summary['agents_covered']) or 'none'}")
    print(f"Written to: {summary['output_path']}")


if __name__ == "__main__":
    _main()
