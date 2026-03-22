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

# ── Agent keyword patterns (deterministic, zero LLM calls) ────────────────

_GIT_PATTERN = re.compile(
    r"\b(git\s+\w+|commit|push|pull\s+request|open\s+a\s+pr|create\s+a?\s*pr|"
    r"branch\s+off|merge\s+branch|rebase|git\s+stash|"
    r"stage\s+(files?|changes?)|unstage|amend\s+commit|cherry.pick)\b",
    re.IGNORECASE,
)

_UI_PATTERN = re.compile(
    r"\b(figma|tailwind|css|component|dashboard|dark\s+mode|design\s+system|"
    r"ui\s+review|ui\s+fix|ui\s+init|ui\s+compose|frontend|design\s+brief|"
    r"tokens\.json|glassmorphi|bento\s+grid)\b",
    re.IGNORECASE,
)

_KAREN_PATTERN = re.compile(
    r"\b(changelog|roadmap|folder\s+audit|organize\s+(the\s+)?(docs|folder|project)|"
    r"docs\s+organization|readme|project\s+structure|tidy\s+up)\b",
    re.IGNORECASE,
)

_DIAGNOSE_PATTERN = re.compile(
    r"\b(root\s+cause|why\s+is\s+(it\s+)?(broken|failing|not\s+working)|"
    r"diagnose|trace\s+(the\s+)?error|something\s+is\s+broken|debug\s+this)\b",
    re.IGNORECASE,
)

_SECURITY_PATTERN = re.compile(
    r"\b(security\s+(audit|review)|owasp|vulnerability|xss|sql\s+injection|"
    r"csrf|injection\s+attack|penetration\s+test|pentest|hardening)\b",
    re.IGNORECASE,
)

_KILN_PATTERN = re.compile(
    r"\b(kiln|bricklayerhub|electron\s+app)\b",
    re.IGNORECASE,
)

_SOLANA_PATTERN = re.compile(
    r"\b(solana|anchor\s+program|spl\s+token|token.?2022|defi|adbp|"
    r"on.?chain|blockchain|wallet\s+integration)\b",
    re.IGNORECASE,
)

_REFACTOR_PATTERN = re.compile(
    r"\b(refactor|clean\s+up\s+(the\s+)?code|restructure|rename\s+(the\s+)?\w+|"
    r"extract\s+(a\s+)?(function|class|module)|code\s+smell)\b",
    re.IGNORECASE,
)

_ARCHITECT_PATTERN = re.compile(
    r"\b(system\s+design|architecture\s+(decision|review)|tech\s+stack|"
    r"scalab(le|ility)|trade.?off|design\s+pattern|microservice|monolith)\b",
    re.IGNORECASE,
)

_CAMPAIGN_PATTERN = re.compile(
    r"\b(start\s+(a\s+)?campaign|resume\s+(the\s+)?campaign|question\s+bank|"
    r"research\s+loop|wave\s+\d|bl.run|masonry.run)\b",
    re.IGNORECASE,
)

# ── Mode field regex ───────────────────────────────────────────────────────

_MODE_FIELD_RE = re.compile(r"\*\*(?:Operational\s+)?Mode\*\*:\s*(\w+)", re.IGNORECASE)


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

    # 1b. Deterministic agent keyword routing (zero LLM calls)
    if _GIT_PATTERN.search(request_text):
        return _decision("git-nerd", "Git operation keyword matched")
    if _SOLANA_PATTERN.search(request_text):
        return _decision("solana-specialist", "Solana/blockchain keyword matched")
    if _KILN_PATTERN.search(request_text):
        return _decision("kiln-engineer", "Kiln/Electron keyword matched")
    if _SECURITY_PATTERN.search(request_text):
        return _decision("security", "Security audit keyword matched")
    if _UI_PATTERN.search(request_text):
        return _decision("uiux-master", "UI/design keyword matched")
    if _KAREN_PATTERN.search(request_text):
        return _decision("karen", "Docs/changelog/organization keyword matched")
    if _DIAGNOSE_PATTERN.search(request_text):
        return _decision("diagnose-analyst", "Diagnosis keyword matched")
    if _REFACTOR_PATTERN.search(request_text):
        return _decision("refactorer", "Refactor keyword matched")
    if _ARCHITECT_PATTERN.search(request_text):
        return _decision("architect", "Architecture keyword matched")
    if _CAMPAIGN_PATTERN.search(request_text):
        return _decision("trowel", "Campaign keyword matched")

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
        mode_value = m.group(1).strip().lower()
        agents = get_agents_for_mode(registry, mode_value)
        if agents:
            return _decision(agents[0].name, f"Mode field: {mode_value}")

    return None
