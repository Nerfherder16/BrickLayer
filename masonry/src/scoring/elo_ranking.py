"""Elo ranking — load, update, and rank agents from agent_db.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import fcntl as _fcntl
except ImportError:
    _fcntl = None  # type: ignore[assignment]

_DEFAULT_ELO = 1200
_DB_RELATIVE = Path("masonry") / "agent_db.json"


def _db_path(base_dir: Path) -> Path:
    return Path(base_dir) / _DB_RELATIVE


def load_agent_db(base_dir: Any) -> dict[str, dict]:
    """Load agent_db.json from base_dir/masonry/. Returns {} if missing."""
    path = _db_path(base_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def get_leaderboard(base_dir: Any) -> list[tuple[str, dict]]:
    """Return agents sorted by Elo descending."""
    db = load_agent_db(base_dir)
    return sorted(db.items(), key=lambda kv: kv[1].get("elo", _DEFAULT_ELO), reverse=True)


def update_elo(agent_name: str, delta: float, base_dir: Any) -> None:
    """Add delta to agent's Elo score. Creates agent at default Elo if absent.

    Uses an exclusive file lock (POSIX) + atomic rename to prevent lost-update
    races when multiple processes update the same agent_db.json concurrently.
    """
    path = _db_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")

    with open(lock_path, "a") as lock_fh:
        if _fcntl is not None:
            _fcntl.flock(lock_fh, _fcntl.LOCK_EX)
        try:
            db = load_agent_db(base_dir)
            entry = db.get(agent_name, {"elo": _DEFAULT_ELO, "runs": 0})
            entry["elo"] = entry.get("elo", _DEFAULT_ELO) + delta
            db[agent_name] = entry
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(db, indent=2), encoding="utf-8")
            tmp.replace(path)
        finally:
            if _fcntl is not None:
                _fcntl.flock(lock_fh, _fcntl.LOCK_UN)
