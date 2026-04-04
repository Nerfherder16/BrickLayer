"""Training data collector — computes EMA of strategy success rates from telemetry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALPHA: float = 0.3
COLD_START: float = 0.688


def compute_ema(telemetry_path: Any, output_path: Any) -> dict[str, dict[str, float]]:
    """
    Read telemetry JSONL, compute EMA per (task_type, strategy), write JSON.

    Records missing task_type, strategy, or success fields are skipped.
    Records are processed in chronological order by timestamp.
    Returns the computed EMA dict (task_type → strategy → float).
    """
    tel_path = Path(telemetry_path)
    if not tel_path.exists():
        return {}

    records: list[dict[str, Any]] = []
    try:
        for line in tel_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return {}

    # Filter and sort
    valid = [
        r for r in records
        if "task_type" in r and "strategy" in r and "success" in r
    ]
    valid.sort(key=lambda r: r.get("timestamp", ""))

    ema: dict[str, dict[str, float]] = {}
    for r in valid:
        tt = r["task_type"]
        st = r["strategy"]
        val = 1.0 if r["success"] else 0.0
        current = ema.setdefault(tt, {}).get(st, COLD_START)
        ema[tt][st] = ALPHA * val + (1 - ALPHA) * current

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ema, indent=2), encoding="utf-8")

    return ema
