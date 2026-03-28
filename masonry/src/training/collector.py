"""
Training data collector: reads masonry/telemetry.jsonl, computes per-strategy
EMA success rates per task_type, and writes results to ema_history.json.
"""

import json
from pathlib import Path

ALPHA = 0.3
COLD_START = 0.688

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_TELEMETRY = _REPO_ROOT / "masonry" / "telemetry.jsonl"
_DEFAULT_OUTPUT = Path(__file__).resolve().parent / "ema_history.json"


def compute_ema(telemetry_path=None, output_path=None):
    """Read telemetry, compute EMA success rates, write ema_history.json.

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


if __name__ == "__main__":
    result = compute_ema()
    print(f"EMA history written. Task types: {list(result.keys())}")
