"""Layer 3 — LLM-based routing.

Uses Claude (haiku) via subprocess to classify ambiguous requests.
Falls back to None on any failure so Layer 4 (fallback) can handle it.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision

# Windows cold-starts for cmd.exe + claude subprocess average 4-6s (vs ~2s on Linux).
# 20s gives sufficient headroom without exceeding Claude Code's hook timeout threshold.
_LLM_TIMEOUT = 20 if platform.system() == "Windows" else 10
_LLM_MODEL = os.environ.get("MASONRY_LLM_MODEL", "claude-haiku-4-5-20251001")
_LLM_CONFIDENCE = 0.6
_LLM_RETRY_DELAY = 2  # seconds between retries on timeout

# Pre-flight: warn once if claude CLI is not on PATH
_claude_checked = False


def _check_claude_available() -> bool:
    global _claude_checked
    if _claude_checked:
        return True
    available = shutil.which("claude") is not None
    if not available:
        print(
            "[llm_router] WARNING: 'claude' CLI not found on PATH. "
            "Layer 3 LLM routing will always fall back to Layer 4. "
            "Install claude CLI or set MASONRY_LLM_MODEL to suppress.",
            file=sys.stderr,
        )
    _claude_checked = True
    return available


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

    if not _check_claude_available():
        return None

    # On Windows, claude is a .cmd file which is not directly executable.
    # Wrap in ["cmd", "/c", "claude", ...] so cmd.exe resolves the .cmd extension
    # while still passing arguments as a list (avoids shlex.quote POSIX escaping
    # that cmd.exe does not understand, and eliminates shell=True injection risk).
    if platform.system() == "Windows":
        cmd = ["cmd", "/c", "claude", "--model", _LLM_MODEL, "--print", "-p", full_prompt]
    else:
        cmd = ["claude", "--model", _LLM_MODEL, "--print", "-p", full_prompt]

    result = None
    for attempt in range(2):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_LLM_TIMEOUT,
            )
            break
        except subprocess.TimeoutExpired:
            if attempt == 0:
                print(
                    f"[llm_router] LLM routing timed out (attempt 1), retrying in {_LLM_RETRY_DELAY}s...",
                    file=sys.stderr,
                )
                import time
                time.sleep(_LLM_RETRY_DELAY)
            else:
                print("[llm_router] LLM routing timed out after retry.", file=sys.stderr)
                return None
        except Exception as exc:
            print(f"[llm_router] Subprocess error: {exc}", file=sys.stderr)
            return None

    if result is None:
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
