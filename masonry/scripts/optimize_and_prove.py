"""masonry/scripts/optimize_and_prove.py

Automated prompt optimization pipeline: evaluate → snapshot → optimize →
re-evaluate → deploy or rollback.

Usage:
    python masonry/scripts/optimize_and_prove.py <agent_name> [options]

Options:
    --base-dir PATH        Root directory (default: repo root)
    --signature STR        DSPy signature name (default: same as agent_name)
    --eval-size INT        Number of eval examples (default: 20)
    --min-delta FLOAT      Minimum score improvement required (default: 0.02)
    --min-score FLOAT      Minimum absolute score required to deploy (default: 0.75)
    --dry-run              Print plan without running subprocesses
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _read_score(eval_json: Path) -> float:
    """Read the score field from an eval_latest.json file."""
    data = json.loads(eval_json.read_text(encoding="utf-8"))
    return float(data["score"])


def run_optimize_and_prove(
    agent_name: str,
    base_dir: Path | str | None = None,
    signature: str | None = None,
    eval_size: int = 20,
    min_delta: float = 0.02,
    min_score: float = 0.75,
    dry_run: bool = False,
) -> dict:
    """Run the full optimize-and-prove pipeline for an agent.

    Steps:
      1. eval_agent.py         → score_before
      2. snapshot_agent.py     → snapshot current prompt (with --score)
      3. optimize_claude.py    → generate candidate prompt
      4. eval_agent.py         → score_after
      5a. snapshot_agent.py    → deploy new prompt   (if both gates pass)
      5b. snapshot_agent.py --rollback               (if either gate fails)

    Returns:
        {"deployed": bool, "score_before": float, "score_after": float, "delta": float}
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
    base_dir = Path(base_dir)

    if signature is None:
        signature = agent_name

    snapshot_dir = base_dir / "agent_snapshots"
    eval_json = snapshot_dir / agent_name / "eval_latest.json"

    eval_script = _SCRIPTS_DIR / "eval_agent.py"
    snapshot_script = _SCRIPTS_DIR / "snapshot_agent.py"
    optimize_script = _SCRIPTS_DIR / "optimize_claude.py"

    def _run(cmd: list) -> subprocess.CompletedProcess:
        if dry_run:
            print(f"[dry-run] {' '.join(str(c) for c in cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.run(cmd, capture_output=False, text=True)

    # Step 1: evaluate current agent → score_before
    _run([
        sys.executable, str(eval_script),
        agent_name,
        "--base-dir", str(base_dir),
        "--eval-size", str(eval_size),
    ])
    score_before = _read_score(eval_json)

    # Step 2: snapshot current prompt
    _run([
        sys.executable, str(snapshot_script),
        agent_name,
        "--score", str(score_before),
        "--eval-size", str(eval_size),
        "--base-dir", str(base_dir),
    ])

    # Step 3: optimize prompt
    _run([
        sys.executable, str(optimize_script),
        agent_name,
        "--signature", signature,
        "--base-dir", str(base_dir),
    ])

    # Step 4: evaluate candidate prompt → score_after
    _run([
        sys.executable, str(eval_script),
        agent_name,
        "--base-dir", str(base_dir),
        "--eval-size", str(eval_size),
    ])
    score_after = _read_score(eval_json)

    delta = score_after - score_before
    deploy = score_after >= score_before + min_delta and score_after >= min_score

    if deploy:
        # Step 5a: deploy — snapshot the new prompt
        _run([
            sys.executable, str(snapshot_script),
            agent_name,
            "--score", str(score_after),
            "--eval-size", str(eval_size),
            "--base-dir", str(base_dir),
        ])
        print(f"DEPLOYED {agent_name}: {score_before:.4f} → {score_after:.4f} (delta={delta:.4f})")
    else:
        # Step 5b: reject — rollback to previous snapshot
        _run([
            sys.executable, str(snapshot_script),
            agent_name,
            "--rollback",
            "--base-dir", str(base_dir),
        ])
        print(
            f"REJECTED {agent_name}: {score_before:.4f} → {score_after:.4f} "
            f"(delta={delta:.4f}, min_delta={min_delta}, min_score={min_score})"
        )

    return {
        "deployed": deploy,
        "score_before": score_before,
        "score_after": score_after,
        "delta": delta,
    }


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Optimize and prove an agent prompt.")
    parser.add_argument("agent_name", help="Agent name")
    parser.add_argument("--base-dir", type=Path, default=None)
    parser.add_argument("--signature", default=None)
    parser.add_argument("--eval-size", type=int, default=20)
    parser.add_argument("--min-delta", type=float, default=0.02)
    parser.add_argument("--min-score", type=float, default=0.75)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_optimize_and_prove(
        agent_name=args.agent_name,
        base_dir=args.base_dir,
        signature=args.signature,
        eval_size=args.eval_size,
        min_delta=args.min_delta,
        min_score=args.min_score,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
