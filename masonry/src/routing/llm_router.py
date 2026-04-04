"""Layer 2 — LLM-based routing.

Falls through from deterministic layer when no rule matches.
Calls the claude CLI to pick an agent from the registry.
Returns RoutingDecision with confidence=0.6, or None on any failure.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Optional

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision

_LLM_MODEL: str = os.environ.get("MASONRY_LLM_MODEL", "claude-haiku-4-5-20251001")
_LLM_TIMEOUT: int = 20
_LLM_RETRY_DELAY: int = 2
_MAX_REQUEST_LEN: int = 500
_claude_checked: bool = False

_CLAUDE_CMD = ["claude.cmd" if platform.system() == "Windows" else "claude"]

_PROMPT_TEMPLATE = """\
You are a routing assistant. Given the user request below, pick the single best agent
from the registry list to handle it. Reply with ONLY a JSON object:
{{"target_agent": "<agent_name>", "reason": "<one sentence>"}}

Registry agents: {agent_names}

User request: {request_text}
"""


def _sanitize(text: str) -> str:
    """Collapse whitespace and truncate to prevent prompt injection."""
    return " ".join(text.split())[:_MAX_REQUEST_LEN]


def route_llm(
    request_text: str,
    registry: list[AgentRegistryEntry],
) -> Optional[RoutingDecision]:
    """Try LLM-based routing. Returns None on any failure."""
    global _claude_checked

    if not _claude_checked:
        _claude_checked = True
        if shutil.which(_CLAUDE_CMD[0]) is None:
            sys.stderr.write(
                f"[llm_router] '{_CLAUDE_CMD[0]}' not found on PATH — LLM routing disabled\n"
            )
            return None

    agent_names = [entry.name for entry in registry]
    prompt = _PROMPT_TEMPLATE.format(
        agent_names=", ".join(agent_names),
        request_text=_sanitize(request_text),
    )

    cmd = _CLAUDE_CMD + [
        "--model", _LLM_MODEL,
        "--print",
        "--no-session-persistence",
        "--setting-sources", "",
        prompt,
    ]

    for attempt in range(2):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_LLM_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            if attempt == 0:
                time.sleep(_LLM_RETRY_DELAY)
                continue
            return None
        except Exception:
            return None

        if result.returncode != 0:
            return None

        try:
            raw = result.stdout.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            target = data.get("target_agent", "")
            reason = data.get("reason", "")
        except (json.JSONDecodeError, AttributeError):
            return None

        if target not in agent_names:
            return None

        return RoutingDecision(
            target_agent=target,
            layer="llm",
            confidence=0.6,
            reason=reason[:100],
        )

    return None
