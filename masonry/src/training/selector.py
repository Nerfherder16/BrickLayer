"""
Strategy selector: reads ema_history.json and returns the strategy with the
highest EMA score for a given task_type. Falls back to "balanced" when no
history exists.

Callable standalone:
    python selector.py build   ->  tdd
"""

import json
import sys
from pathlib import Path

_EMA_HISTORY_PATH = Path(__file__).resolve().parent / "ema_history.json"
_FALLBACK = "balanced"


def select_strategy(task_type: str) -> str:
    """Return the strategy with the highest EMA score for task_type.

    Falls back to "balanced" when:
    - ema_history.json does not exist
    - ema_history.json is not valid JSON
    - task_type has no recorded history
    - the strategy dict is empty
    """
    try:
        data = json.loads(_EMA_HISTORY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _FALLBACK

    strategies = data.get(task_type)
    if not strategies:
        return _FALLBACK

    return max(strategies, key=lambda k: strategies[k])


if __name__ == "__main__":
    task_type = sys.argv[1] if len(sys.argv) > 1 else "general"
    print(select_strategy(task_type))
