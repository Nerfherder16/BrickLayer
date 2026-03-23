"""masonry/scripts/snapshot_agent.py

Versioned snapshot system for Masonry agent prompts.

Captures agent .md content at a given evaluation score, tracks baselines,
and supports rollback to the previous snapshot version.

Usage:
    python masonry/scripts/snapshot_agent.py karen --score 0.84 --eval-size 20
    python masonry/scripts/snapshot_agent.py karen --rollback
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent.parent  # blRoot
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))


# ── Agent .md discovery (mirrors optimize_claude.py pattern) ─────────────────


def _find_agent_md_files(base_dir: Path, agent_name: str) -> list[Path]:
    candidates = [
        base_dir / ".claude" / "agents" / f"{agent_name}.md",
        Path.home() / ".claude" / "agents" / f"{agent_name}.md",
    ]
    for child in base_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            p = child / ".claude" / "agents" / f"{agent_name}.md"
            if p.exists():
                candidates.append(p)

    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        resolved = c.resolve() if c.exists() else c
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)
    return [p for p in unique if p.exists()]


# ── Snapshot directory helpers ────────────────────────────────────────────────


def _snapshots_dir(base_dir: Path, agent_name: str) -> Path:
    return base_dir / "masonry" / "agent_snapshots" / agent_name


def _baseline_path(base_dir: Path, agent_name: str) -> Path:
    return _snapshots_dir(base_dir, agent_name) / "baseline.json"


def _next_version_number(snap_dir: Path) -> int:
    """Return the next integer version number by scanning existing v*.md files."""
    existing = list(snap_dir.glob("v*.md"))
    if not existing:
        return 1
    numbers: list[int] = []
    for p in existing:
        match = re.match(r"^v(\d+)_", p.name)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1


def _build_version_string(n: int, score: float) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"v{n}_{date_str}_s{score:.2f}"


# ── Public API ────────────────────────────────────────────────────────────────


def snapshot_agent(
    agent_name: str,
    base_dir: Path,
    score: float,
    eval_size: int = 20,
) -> Path:
    """Create a versioned snapshot of the agent prompt at current score.

    Returns the path to the created snapshot file.
    """
    snap_dir = _snapshots_dir(base_dir, agent_name)
    snap_dir.mkdir(parents=True, exist_ok=True)

    # Read current prompt from the first found agent .md file
    md_files = _find_agent_md_files(base_dir, agent_name)
    if not md_files:
        raise FileNotFoundError(
            f"No agent .md file found for '{agent_name}' under {base_dir}"
        )
    current_content = md_files[0].read_text(encoding="utf-8")

    # Determine version
    n = _next_version_number(snap_dir)
    version = _build_version_string(n, score)

    # Write snapshot file
    snapshot_file = snap_dir / f"{version}.md"
    snapshot_file.write_text(current_content, encoding="utf-8")

    # Write baseline.json
    recorded_at = datetime.now(timezone.utc).isoformat()
    baseline = {
        "agent": agent_name,
        "current_version": version,
        "score": score,
        "eval_size": eval_size,
        "snapshot_file": str(snapshot_file),
        "recorded_at": recorded_at,
    }
    _baseline_path(base_dir, agent_name).write_text(
        json.dumps(baseline, indent=2), encoding="utf-8"
    )

    return snapshot_file


def rollback_agent(
    agent_name: str,
    base_dir: Path,
) -> str:
    """Roll back agent prompt to the previous snapshot version.

    Returns the version string rolled back to (e.g. 'v1_20260323_s0.84').
    Raises ValueError if no previous version exists.
    """
    snap_dir = _snapshots_dir(base_dir, agent_name)
    baseline_file = _baseline_path(base_dir, agent_name)

    if not baseline_file.exists():
        raise ValueError(
            f"No previous version to roll back to for agent {agent_name}: "
            "baseline.json not found"
        )

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    current_version = baseline["current_version"]

    # Parse current version number
    match = re.match(r"^v(\d+)_", current_version)
    if not match:
        raise ValueError(
            f"Cannot parse version number from current_version={current_version!r}"
        )
    current_n = int(match.group(1))

    if current_n <= 1:
        raise ValueError(
            f"No previous version to roll back to for agent {agent_name}"
        )

    # Find the snapshot with version number current_n - 1
    previous_n = current_n - 1
    candidates = list(snap_dir.glob(f"v{previous_n}_*.md"))
    if not candidates:
        raise ValueError(
            f"No previous version to roll back to for agent {agent_name}: "
            f"v{previous_n} snapshot file not found"
        )
    previous_snapshot = candidates[0]
    previous_version = previous_snapshot.stem

    # Restore content to all agent .md locations
    previous_content = previous_snapshot.read_text(encoding="utf-8")
    md_files = _find_agent_md_files(base_dir, agent_name)
    for md_path in md_files:
        md_path.write_text(previous_content, encoding="utf-8")

    # Update baseline.json to point to the previous version
    baseline["current_version"] = previous_version
    baseline["snapshot_file"] = str(previous_snapshot)
    baseline_file.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    return previous_version


# ── CLI ───────────────────────────────────────────────────────────────────────


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or roll back versioned snapshots of agent prompts."
    )
    parser.add_argument("agent_name", help="Name of the agent to snapshot or roll back")
    parser.add_argument(
        "--score",
        type=float,
        help="Evaluation score to record with the snapshot",
    )
    parser.add_argument(
        "--eval-size",
        type=int,
        default=20,
        help="Number of eval examples used to produce the score (default: 20)",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Roll back to the previous snapshot instead of creating a new one",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="BrickLayer root directory (default: cwd)",
    )
    args = parser.parse_args()
    base_dir = args.base_dir.resolve()

    if args.rollback:
        try:
            version = rollback_agent(agent_name=args.agent_name, base_dir=base_dir)
            print(f"[rollback] Rolled back {args.agent_name} to {version}")
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        if args.score is None:
            parser.error("--score is required when not using --rollback")
        snap_path = snapshot_agent(
            agent_name=args.agent_name,
            base_dir=base_dir,
            score=args.score,
            eval_size=args.eval_size,
        )
        print(f"[snapshot] Created {snap_path}")


if __name__ == "__main__":
    _main()
