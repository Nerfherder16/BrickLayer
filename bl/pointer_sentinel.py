"""Sentinel helpers for firing the pointer agent at regular question intervals.

Utility library — trowel.md handles pointer firing inline via the wave sentinels section
(checks global_count % 8 == 0 directly). This module is available for external tooling
(e.g., masonry-mcp.js, CLI scripts) that needs the same logic without duplicating it.
"""

import re
from pathlib import Path


def should_fire_pointer(global_count: int, interval: int = 8) -> bool:
    """Return True if pointer should fire at this global question count.

    Fires at every multiple of interval: 8, 16, 24, 32...
    Does NOT fire at 0.
    """
    if global_count == 0:
        return False
    return global_count % interval == 0


def _checkpoint_sort_key(path: Path) -> tuple[int, int]:
    """Extract (wave, question) integers from wave{N}-q{K}.md for numeric sort."""
    match = re.search(r"wave(\d+)-q(\d+)", path.stem)
    if match:
        return int(match.group(1)), int(match.group(2))
    return (0, 0)


def get_latest_checkpoint(checkpoint_dir: Path) -> Path | None:
    """Return path to most recent checkpoint file by filename sort, or None.

    Returns None if checkpoint_dir does not exist or is empty.
    Checkpoint files named wave{N}-q{K}.md — sorted by wave then question number.
    """
    if not checkpoint_dir.exists():
        return None
    files = sorted(checkpoint_dir.iterdir(), key=_checkpoint_sort_key)
    if not files:
        return None
    return files[-1]
