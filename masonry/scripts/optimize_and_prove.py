"""masonry/scripts/optimize_and_prove.py

Gated optimization pipeline: evaluate → snapshot → optimize → evaluate → deploy or rollback.

Only deploys the optimized prompt if it beats the baseline by at least min_delta
AND meets the absolute min_score floor. Otherwise rolls back.

Usage:
    python masonry/scripts/optimize_and_prove.py karen --signature karen
    python masonry/scripts/optimize_and_prove.py research-analyst --min-delta 0.02
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run_script(script_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Run a Python script as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        ["python", str(script_path)] + args,
        capture_output=True,
        text=True,
    )


def _read_eval_score(base_dir: Path, agent_name: str) -> float:
    """Read the score from eval_latest.json written by eval_agent.py.

    eval_agent.py writes to base_dir/masonry/agent_snapshots/{agent}/eval_latest.json.
    Falls back to base_dir/agent_snapshots/{agent}/eval_latest.json for test compatibility.
    """
    primary = base_dir / "masonry" / "agent_snapshots" / agent_name / "eval_latest.json"
    fallback = base_dir / "agent_snapshots" / agent_name / "eval_latest.json"
    eval_path = primary if primary.exists() else fallback
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    return data["score"]


def run_optimize_and_prove(
    agent_name: str,
    base_dir: Path,
    signature: str = "research",
    eval_size: int = 20,
    min_delta: float = 0.01,
    min_score: float = 0.70,
) -> dict:
    """Gated optimization: only deploy if proven better.

    Returns: {"deployed": bool, "score_before": float, "score_after": float, "delta": float}
    """
    scripts_dir = base_dir / "masonry" / "scripts"
    eval_script = scripts_dir / "eval_agent.py"
    snapshot_script = scripts_dir / "snapshot_agent.py"
    optimize_script = scripts_dir / "optimize_claude.py"

    base_dir_str = str(base_dir)

    # Step 1: eval before optimization
    _run_script(eval_script, [
        agent_name,
        "--signature", signature,
        "--eval-size", str(eval_size),
        "--base-dir", base_dir_str,
    ])
    score_before = _read_eval_score(base_dir, agent_name)

    # Step 2: snapshot current prompt with score_before
    _run_script(snapshot_script, [
        agent_name,
        "--score", str(score_before),
        "--eval-size", str(eval_size),
        "--base-dir", base_dir_str,
    ])

    # Step 3: optimize
    _run_script(optimize_script, [
        agent_name,
        "--signature", signature,
        "--base-dir", base_dir_str,
    ])

    # Step 4: eval after optimization
    _run_script(eval_script, [
        agent_name,
        "--signature", signature,
        "--eval-size", str(eval_size),
        "--base-dir", base_dir_str,
    ])
    score_after = _read_eval_score(base_dir, agent_name)

    delta = score_after - score_before

    # Step 5: deploy or rollback
    if score_after >= score_before + min_delta and score_after >= min_score:
        _run_script(snapshot_script, [
            agent_name,
            "--score", str(score_after),
            "--base-dir", base_dir_str,
        ])
        print(
            f"DEPLOYED: {agent_name}: {score_before:.3f} -> {score_after:.3f}"
            f" (+{delta:.3f})"
        )
        return {
            "deployed": True,
            "score_before": score_before,
            "score_after": score_after,
            "delta": delta,
        }
    else:
        _run_script(snapshot_script, [
            agent_name,
            "--rollback",
            "--base-dir", base_dir_str,
        ])
        print(
            f"REJECTED: {agent_name}: candidate {score_after:.3f}"
            f" < baseline {score_before:.3f} — reverted"
        )
        return {
            "deployed": False,
            "score_before": score_before,
            "score_after": score_after,
            "delta": delta,
        }


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Gated optimization: evaluate → snapshot → optimize → evaluate → "
            "deploy if better, rollback if not."
        )
    )
    parser.add_argument("agent_name", help="Name of the agent to optimize")
    parser.add_argument(
        "--signature",
        default="research",
        choices=["research", "karen"],
        help='Metric signature: "research" (default) or "karen"',
    )
    parser.add_argument(
        "--eval-size",
        type=int,
        default=20,
        help="Number of held-out examples to evaluate (default: 20)",
    )
    parser.add_argument(
        "--min-delta",
        type=float,
        default=0.01,
        help="Minimum score improvement required to deploy (default: 0.01)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.70,
        help="Minimum absolute score required to deploy (default: 0.70)",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="BrickLayer root directory (default: cwd)",
    )
    args = parser.parse_args()
    result = run_optimize_and_prove(
        agent_name=args.agent_name,
        base_dir=args.base_dir.resolve(),
        signature=args.signature,
        eval_size=args.eval_size,
        min_delta=args.min_delta,
        min_score=args.min_score,
    )
    sys.exit(0 if result["deployed"] else 1)


if __name__ == "__main__":
    _main()
