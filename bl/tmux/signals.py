"""bl/tmux/signals.py — Hook lifecycle signal files for masonry integration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from bl.tmux.helpers import resolve_model

if TYPE_CHECKING:
    from bl.tmux.core import AgentResult

SIGNAL_DIR = Path("/tmp")


def _write_signal(path: Path, data: dict[str, object]) -> None:
    try:
        _ = path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def write_start_signal(
    agent_id: str,
    agent_name: str,
    cwd: str,
    model: str | None,
    pane_id: str | None,
) -> None:
    """Write start signal file for masonry hooks to detect."""
    _write_signal(
        SIGNAL_DIR / f"bl-agent-start-{agent_id}.json",
        {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "model": resolve_model(model) or "",
            "cwd": cwd,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pane_id": pane_id,
            "tmux": pane_id is not None,
        },
    )


def write_stop_signal(
    agent_id: str,
    agent_name: str,
    result: AgentResult,
) -> None:
    """Write stop signal file for masonry hooks to detect."""
    _write_signal(
        SIGNAL_DIR / f"bl-agent-stop-{agent_id}.json",
        {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "session_id": result.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
