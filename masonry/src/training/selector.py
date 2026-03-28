"""
Strategy selector: reads ema_history.json and returns the strategy with the
highest blended score for a given task_type.

Blended score = 0.7 * EMA + 0.3 * avg_pattern_confidence

Falls back to "balanced" when no history exists.

Callable standalone:
    python selector.py build           ->  tdd
    python selector.py build --debug   ->  (blend details on stderr) tdd
"""

import json
import sys
import argparse
from pathlib import Path

_EMA_HISTORY_PATH = Path(__file__).resolve().parent / "ema_history.json"
_DEFAULT_CONFIDENCE_PATH = Path(".autopilot/pattern-confidence.json")
_FALLBACK = "balanced"
_COLD_START = 0.5  # neutral EMA score when no history for a strategy

_EMA_WEIGHT = 0.7
_CONF_WEIGHT = 0.3
_CONF_NEUTRAL = 0.7  # used when no confidence data maps to a strategy


def load_confidence(confidence_path: Path) -> dict[str, float]:
    """Load pattern-confidence.json and return {pattern_id: confidence_float}.

    Accepts both the compact form ``{key: float}`` and the rich form written
    by masonry-post-task.js: ``{key: {confidence: float, ...}}``.

    Returns an empty dict if the file is missing, unreadable, or malformed.
    """
    try:
        raw = json.loads(confidence_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}

    if not isinstance(raw, dict):
        return {}

    result: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, (int, float)):
            result[key] = float(value)
        elif isinstance(value, dict):
            conf = value.get("confidence")
            if isinstance(conf, (int, float)):
                result[key] = float(conf)
        # skip malformed entries silently

    return result


def avg_confidence_for_strategy(
    strategy: str,
    confidence_data: dict[str, float],
) -> float:
    """Return average confidence for patterns associated with *strategy*.

    The pattern-confidence store is keyed by agent/task-type names.  A
    strategy name may match one or more keys directly (exact) or as a
    prefix substring.  If no match is found, return the neutral value 0.7.

    Matching logic (in priority order):
    1. Exact key match: ``confidence_data[strategy]``
    2. Keys that contain the strategy name as a substring (broadened match)
    3. Fallback: 0.7
    """
    if not confidence_data:
        return _CONF_NEUTRAL

    # 1. Exact match
    if strategy in confidence_data:
        return confidence_data[strategy]

    # 2. Substring match — collect all keys that contain the strategy name
    matched = [v for k, v in confidence_data.items() if strategy in k or k in strategy]
    if matched:
        return sum(matched) / len(matched)

    return _CONF_NEUTRAL


def select_strategy(
    task_type: str,
    *,
    confidence_path: Path = _DEFAULT_CONFIDENCE_PATH,
    debug: bool = False,
) -> str:
    """Return the strategy with the highest blended score for *task_type*.

    Blended score = 0.7 * EMA_score + 0.3 * avg_pattern_confidence

    Falls back to "balanced" when:
    - ema_history.json does not exist
    - ema_history.json is not valid JSON
    - task_type has no recorded history
    - the strategy dict is empty

    If pattern-confidence.json is missing or malformed, confidence
    contribution is neutral (0.7) and the result is EMA-driven only.
    """
    try:
        data = json.loads(_EMA_HISTORY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        if debug:
            print(
                f"[selector] ema_history.json not found or malformed — returning {_FALLBACK!r}",
                file=sys.stderr,
            )
        return _FALLBACK

    strategies: dict[str, float] = data.get(task_type)
    if not strategies:
        if debug:
            print(
                f"[selector] no history for task_type={task_type!r} — returning {_FALLBACK!r}",
                file=sys.stderr,
            )
        return _FALLBACK

    confidence_data = load_confidence(confidence_path)

    best_strategy = _FALLBACK
    best_score = -1.0

    if debug:
        print(f"[selector] task_type={task_type!r}", file=sys.stderr)
        print(
            f"[selector] confidence_path={confidence_path} "
            f"({'loaded' if confidence_data else 'empty/missing'})",
            file=sys.stderr,
        )

    for strategy, ema_score in strategies.items():
        conf_score = avg_confidence_for_strategy(strategy, confidence_data)
        final_score = _EMA_WEIGHT * ema_score + _CONF_WEIGHT * conf_score

        if debug:
            print(
                f"[selector]   {strategy}: "
                f"EMA={ema_score:.4f} * {_EMA_WEIGHT} + "
                f"conf={conf_score:.4f} * {_CONF_WEIGHT} = "
                f"final={final_score:.4f}",
                file=sys.stderr,
            )

        if final_score > best_score:
            best_score = final_score
            best_strategy = strategy

    if debug:
        print(f"[selector] selected={best_strategy!r} (score={best_score:.4f})", file=sys.stderr)

    return best_strategy


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Select the best strategy for a given task type by blending "
            "EMA history (70%%) and pattern confidence (30%%)."
        )
    )
    parser.add_argument(
        "task_type",
        nargs="?",
        default="general",
        help="Task type to look up in ema_history.json (default: general).",
    )
    parser.add_argument(
        "--confidence-path",
        type=Path,
        default=_DEFAULT_CONFIDENCE_PATH,
        metavar="PATH",
        help=(
            "Path to pattern-confidence.json "
            f"(default: {_DEFAULT_CONFIDENCE_PATH})."
        ),
    )
    parser.add_argument(
        "--ema-path",
        type=Path,
        default=_EMA_HISTORY_PATH,
        metavar="PATH",
        help=(
            "Path to ema_history.json "
            f"(default: {_EMA_HISTORY_PATH})."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print blend calculation details to stderr.",
    )
    return parser


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()
    # Allow --ema-path to override the module-level constant at runtime
    if args.ema_path != _EMA_HISTORY_PATH:
        import src.training.selector as _self  # noqa: PLC0415
        _self._EMA_HISTORY_PATH = args.ema_path
    result = select_strategy(
        args.task_type,
        confidence_path=args.confidence_path,
        debug=args.debug,
    )
    print(result)
