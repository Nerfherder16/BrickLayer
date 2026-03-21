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

# Windows cold-starts for cmd.exe + claude subprocess average 4-6s (vs ~2s on Linux).
# 20s gives sufficient headroom without exceeding Claude Code's hook timeout threshold.
_LLM_TIMEOUT = 20 if platform.system() == "Windows" else 10
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

    # On Windows, claude is a .cmd file which is not directly executable.
    # Wrap in ["cmd", "/c", "claude", ...] so cmd.exe resolves the .cmd extension
    # while still passing arguments as a list (avoids shlex.quote POSIX escaping
    # that cmd.exe does not understand, and eliminates shell=True injection risk).
    if platform.system() == "Windows":
        cmd = ["cmd", "/c", "claude", "--model", _LLM_MODEL, "--print", "-p", full_prompt]
    else:
        cmd = ["claude", "--model", _LLM_MODEL, "--print", "-p", full_prompt]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_LLM_TIMEOUT,
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

    # Validate against registry — reject hallucinated agent names
    registry_names = {a.name for a in registry}
    if target not in registry_names:
        print(f"[llm_router] LLM returned unknown agent '{target}' not in registry.", file=sys.stderr)
        return None

    reason = parsed.get("reason", "LLM routing")[:100]

    return RoutingDecision(
        target_agent=target,
        layer="llm",
        confidence=_LLM_CONFIDENCE,
        reason=reason,
    )
