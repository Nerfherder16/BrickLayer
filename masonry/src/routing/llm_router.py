"""Layer 3 — LLM-based routing.

Uses Claude (haiku) via subprocess to classify ambiguous requests.
Falls back to None on any failure so Layer 4 (fallback) can handle it.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision

_LLM_TIMEOUT = 8  # seconds — Layer 4 fallback is acceptable, don't wait long
_LLM_MODEL = "claude-haiku-4-5-20251001"
_LLM_CONFIDENCE = 0.6


def route_llm(
    request_text: str,
    registry: list[AgentRegistryEntry],
) -> RoutingDecision | None:
    """Route via Claude (haiku) LLM call.

    Returns RoutingDecision with confidence=0.6, or None on any failure.
    """
    agent_list = "\n".join(
        f"- {a.name}: {a.description or ', '.join(a.capabilities)}"
        for a in registry
    )

    system_prompt = (
        "You are a routing agent. Given the user request and the available agents list, "
        "select the best agent. Respond with ONLY a JSON object: "
        '{"target_agent": "agent-name", "reason": "brief reason"}. '
        f"Available agents:\n{agent_list}"
    )

    full_prompt = f"{system_prompt}\n\nUser request: {request_text}"

    # On Windows, claude is a .cmd file — requires shell=True to be found.
    # When shell=True, pass a single string (not list) to avoid argument corruption.
    _is_windows = platform.system() == "Windows"
    if _is_windows:
        import shlex
        cmd_str = f"claude --model {_LLM_MODEL} --print -p {shlex.quote(full_prompt)}"
    else:
        cmd_str = None  # unused on non-Windows

    try:
        result = subprocess.run(
            cmd_str if _is_windows else ["claude", "--model", _LLM_MODEL, "--print", "-p", full_prompt],
            capture_output=True,
            text=True,
            timeout=_LLM_TIMEOUT,
            shell=_is_windows,
        )
    except subprocess.TimeoutExpired:
        print("[llm_router] LLM routing timed out.", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[llm_router] Subprocess error: {exc}", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(
            f"[llm_router] Claude exited with code {result.returncode}",
            file=sys.stderr,
        )
        return None

    stdout = result.stdout.strip()

    # Try to parse JSON — may be embedded in text, try to extract it
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re
        match = re.search(r"\{[^}]+\}", stdout, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                print(f"[llm_router] Could not parse JSON from: {stdout[:200]}", file=sys.stderr)
                return None
        else:
            print(f"[llm_router] No JSON found in stdout: {stdout[:200]}", file=sys.stderr)
            return None

    target = parsed.get("target_agent")
    if not target:
        print("[llm_router] No target_agent in LLM response.", file=sys.stderr)
        return None

    reason = parsed.get("reason", "LLM routing")[:100]

    return RoutingDecision(
        target_agent=target,
        layer="llm",
        confidence=_LLM_CONFIDENCE,
        reason=reason,
    )
