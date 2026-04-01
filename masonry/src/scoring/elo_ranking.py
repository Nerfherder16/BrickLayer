"""Elo ranking utilities for agent_db.json.

Reads/writes masonry/agent_db.json relative to base_dir.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DB_RELATIVE = Path("masonry") / "agent_db.json"
_DEFAULT_ELO = 1200.0


def _db_path(base_dir: Any) -> Path:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
    return Path(base_dir) / _DB_RELATIVE


def load_agent_db(base_dir: Any = None) -> dict[str, Any]:
    """Load agent_db.json and return its content as a dict."""
    path = _db_path(base_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_agent_db(db: dict[str, Any], base_dir: Any) -> None:
    path = _db_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2), encoding="utf-8")


def update_elo(
    agent_name: str,
    delta: float,
    base_dir: Any = None,
) -> None:
    """Apply an Elo delta to the named agent in agent_db.json.

    Creates the agent entry with default Elo 1200 if it doesn't exist.
    """
    db = load_agent_db(base_dir)
    if agent_name not in db:
        db[agent_name] = {"elo": _DEFAULT_ELO}
    current = db[agent_name].get("elo", _DEFAULT_ELO)
    db[agent_name]["elo"] = current + delta
    _save_agent_db(db, base_dir)


def get_leaderboard(base_dir: Any = None) -> list[tuple[str, float]]:
    """Return list of (agent_name, elo) sorted descending by Elo score."""
    db = load_agent_db(base_dir)
    entries = [
        (name, float(data.get("elo", _DEFAULT_ELO)))
        for name, data in db.items()
    ]
    return sorted(entries, key=lambda x: x[1], reverse=True)
