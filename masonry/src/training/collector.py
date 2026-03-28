"""
Training data collector: reads masonry/telemetry.jsonl, computes per-strategy
EMA success rates per task_type, and writes results to ema_history.json.

Supports two telemetry schemas:
  Legacy: {task_type, strategy, success: bool, timestamp}
  Current: {agent, strategy, verdict, timestamp, ...}
"""

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ALPHA = 0.3
COLD_START = 0.688

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_TELEMETRY = _REPO_ROOT / "masonry" / "telemetry.jsonl"
_DEFAULT_OUTPUT = Path(__file__).resolve().parent / "ema_history.json"

# Verdicts that count as success in the current schema
_SUCCESS_VERDICTS = {"HEALTHY", "IMPROVEMENT", "FIX_COMPLETE"}


def _record_to_success(record: dict) -> bool | None:
    """Return True/False for success, or None to skip.

    Handles both legacy {success: bool} and current {verdict: str} schemas.
    """
    # Legacy schema
    if "success" in record:
        val = record["success"]
        if isinstance(val, bool):
            return val
        return None

    # Current schema
    verdict = record.get("verdict")
    if verdict is None:
        return None
    return verdict in _SUCCESS_VERDICTS


def compute_ema(telemetry_path=None, output_path=None):
    """Read telemetry, compute EMA success rates, write ema_history.json.

    Supports legacy schema (task_type / strategy / success) for backward
    compatibility with existing tests.

    Args:
        telemetry_path: Path to telemetry.jsonl (default: masonry/telemetry.jsonl)
        output_path: Path to write ema_history.json (default: src/training/ema_history.json)

    Returns:
        dict: task_type -> strategy -> ema_score
    """
    telemetry_path = Path(telemetry_path) if telemetry_path else _DEFAULT_TELEMETRY
    output_path = Path(output_path) if output_path else _DEFAULT_OUTPUT

    records = []
    if telemetry_path.exists():
        with open(telemetry_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Sort chronologically before computing EMA
    records.sort(key=lambda r: r.get("timestamp", ""))

    # ema_scores[task_type][strategy] = current ema value
    ema_scores: dict[str, dict[str, float]] = {}

    for record in records:
        task_type = record.get("task_type")
        strategy = record.get("strategy")
        success = record.get("success")

        if not task_type or not strategy or success is None:
            continue

        success_value = 1.0 if success else 0.0

        if task_type not in ema_scores:
            ema_scores[task_type] = {}

        old_ema = ema_scores[task_type].get(strategy, COLD_START)
        new_ema = ALPHA * success_value + (1 - ALPHA) * old_ema
        ema_scores[task_type][strategy] = new_ema

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(ema_scores, fh, indent=2)

    return ema_scores


def collect_agent_ema(telemetry_path: Path, output_path: Path) -> tuple[int, int]:
    """Read agent-schema telemetry, update ema_history.json atomically.

    Uses current schema: {agent, strategy, verdict, timestamp, ...}
    Key format: "agent:strategy"
    Output format: {"agent:strategy": {"ema": float, "count": int, "last_updated": str}}

    Returns:
        (pairs_updated, entries_processed)
    """
    records: list[dict] = []
    if telemetry_path.exists():
        with open(telemetry_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Sort chronologically
    records.sort(key=lambda r: r.get("timestamp", ""))

    # Load existing EMA history
    existing: dict[str, dict] = {}
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    processed = 0
    for record in records:
        agent = record.get("agent")
        strategy = record.get("strategy")
        success = _record_to_success(record)

        if not agent or not strategy or success is None:
            continue

        key = f"{agent}:{strategy}"
        entry = existing.get(key, {"ema": COLD_START, "count": 0})
        old_ema = entry.get("ema", COLD_START)
        count = entry.get("count", 0)

        success_value = 1.0 if success else 0.0
        new_ema = ALPHA * success_value + (1 - ALPHA) * old_ema

        existing[key] = {
            "ema": new_ema,
            "count": count + 1,
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        processed += 1

    # Atomic write: write to temp then rename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=output_path.parent, suffix=".tmp", prefix="ema_history_"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2)
        os.replace(tmp_name, output_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return len(existing), processed


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "EMA training collector: reads telemetry.jsonl and updates "
            "ema_history.json with per-agent per-strategy EMA scores."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=_DEFAULT_TELEMETRY,
        metavar="PATH",
        help=f"Path to telemetry.jsonl (default: {_DEFAULT_TELEMETRY})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        metavar="PATH",
        help=f"Path to write ema_history.json (default: {_DEFAULT_OUTPUT})",
    )
    return parser


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    pairs_updated, entries_processed = collect_agent_ema(args.input, args.output)
    print(f"Updated {pairs_updated} agent/strategy pairs from {entries_processed} telemetry entries")
