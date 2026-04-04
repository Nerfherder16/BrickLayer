"""Strategy selector — picks highest-EMA strategy for a task type."""
from __future__ import annotations

import json
import os
from pathlib import Path

_EMA_HISTORY_PATH: Path = Path(
    os.environ.get("MASONRY_EMA_HISTORY", str(Path.cwd() / "ema_history.json"))
)

_FALLBACK = "balanced"


def select_strategy(task_type: str) -> str:
    """Return the strategy with the highest EMA for task_type.

    Falls back to 'balanced' if file missing, corrupt, or task_type unknown.
    """
    try:
        data = json.loads(Path(_EMA_HISTORY_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return _FALLBACK

    strategies = data.get(task_type, {})
    if not strategies:
        return _FALLBACK

    return max(strategies, key=lambda s: strategies[s])
