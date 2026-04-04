"""bl/tmux/helpers.py — Detection, model resolution, env building, CLI args."""

import json
import os
import subprocess

# Short model name -> full model ID (canonical source, imported by agent.py)
MODEL_MAP: dict[str, str] = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}


def _tmux_socket_active() -> bool:
    """Check if tmux is reachable via its socket (fallback when $TMUX is stripped)."""
    try:
        _ = subprocess.run(
            ["tmux", "display-message", "-p", ""],
            capture_output=True,
            timeout=3,
            check=True,
        )
        return True
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return False


def in_tmux() -> bool:
    """Return True if running inside a tmux session."""
    return bool(os.environ.get("TMUX")) or _tmux_socket_active()


def resolve_model(model: str | None) -> str | None:
    """Map short model name to full ID. Pass-through if already full or None."""
    if not model:
        return None
    return MODEL_MAP.get(model, model) or None


def build_env(env_overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Build child env excluding CLAUDECODE, with optional overrides."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if env_overrides:
        for k, v in env_overrides.items():
            if v == "":
                _ = env.pop(k, None)
            else:
                env[k] = v
    return env


def build_claude_args(
    *,
    model: str | None = None,
    allowed_tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    dangerously_skip_permissions: bool = False,
    output_format: str | None = "json",
    session_id: str | None = None,
) -> list[str]:
    """Build claude CLI arguments (excludes the binary path itself)."""
    args = ["-p", "-"]
    if output_format:
        args.extend(["--output-format", output_format])
    resolved = resolve_model(model)
    if resolved:
        args.extend(["--model", resolved])
    if allowed_tools:
        args.extend(["--allowedTools", ",".join(allowed_tools)])
    if disallowed_tools:
        args.extend(["--disallowedTools", ",".join(disallowed_tools)])
    if dangerously_skip_permissions:
        args.append("--dangerously-skip-permissions")
    if session_id:
        args.extend(["--resume", session_id])
    return args


def extract_session_id(raw: str) -> str | None:
    """Extract session_id from claude --output-format json output."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data.get("session_id")
    except (json.JSONDecodeError, TypeError):
        pass
    return None
