"""Layer 1 — Deterministic routing.

Handles 60%+ of routing decisions with zero LLM calls using:
1. Slash command pattern matching
2. Autopilot state file inspection
3. Campaign state file inspection
4. UI compose/review state inspection
5. Question **Mode**: field extraction

Returns RoutingDecision with confidence=1.0 on any match, or None to fall through.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision
from masonry.src.schemas.registry_loader import get_agents_for_mode

# ── Slash command table ────────────────────────────────────────────────────

_SLASH_COMMANDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"/plan\b"), "spec-writer"),
    (re.compile(r"/build\b"), "build-workflow"),
    (re.compile(r"/fix\b"), "fix-workflow"),
    (re.compile(r"/verify\b"), "verify-workflow"),
    (re.compile(r"/bl-run\b"), "campaign-conductor"),
    (re.compile(r"/masonry-run\b"), "campaign-conductor"),
]

# ── Mode field regex ───────────────────────────────────────────────────────

_MODE_FIELD_RE = re.compile(r"\*\*Mode\*\*:\s*(\w+)")


def _read_file(path: Path) -> str | None:
    """Read a text file, returning None on any error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, FileNotFoundError, PermissionError):
        return None


def _read_json(path: Path) -> dict | None:
    """Read a JSON file, returning None on any error."""
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw)
    except (OSError, FileNotFoundError, ValueError):
        return None


def _decision(target_agent: str, reason: str) -> RoutingDecision:
    return RoutingDecision(
        target_agent=target_agent,
        layer="deterministic",
        confidence=1.0,
        reason=reason[:100],
    )


def route_deterministic(
    request_text: str,
    project_dir: Path,
    registry: list[AgentRegistryEntry],
) -> RoutingDecision | None:
    """Try to route deterministically. Returns None if no rule matches."""

    # 1. Slash commands
    for pattern, target in _SLASH_COMMANDS:
        if pattern.search(request_text):
            return _decision(target, f"Slash command matched: {pattern.pattern}")

    # 2. Autopilot state
    autopilot_mode = _read_file(project_dir / ".autopilot" / "mode")
    if autopilot_mode:
        if autopilot_mode == "build":
            return _decision("build-workflow", "Autopilot mode=build")
        if autopilot_mode == "fix":
            return _decision("fix-workflow", "Autopilot mode=fix")
        if autopilot_mode == "verify":
            return _decision("verify-workflow", "Autopilot mode=verify")

    # 3. Campaign state
    campaign_data = _read_json(project_dir / "masonry-state.json")
    if campaign_data:
        if campaign_data.get("mode") == "campaign" and campaign_data.get("active_agent"):
            active = campaign_data["active_agent"]
            return _decision(active, f"Campaign active_agent={active}")

    # 4. UI state
    ui_mode = _read_file(project_dir / ".ui" / "mode")
    if ui_mode:
        if ui_mode == "compose":
            return _decision("ui-compose-workflow", "UI mode=compose")
        if ui_mode == "review":
            return _decision("ui-review-workflow", "UI mode=review")

    # 5. Question **Mode**: field
    m = _MODE_FIELD_RE.search(request_text)
    if m:
        mode_value = m.group(1).strip()
        agents = get_agents_for_mode(registry, mode_value)
        if agents:
            return _decision(agents[0].name, f"Mode field: {mode_value}")

    return None
