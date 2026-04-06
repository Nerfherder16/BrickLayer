"""masonry/mcp_server/js_engine.py — Subprocess bridge to Node.js CLI wrappers.

Provides _call_js_engine() for calling masonry/src/engine/cli/*.js tools
from the Python MCP server. Falls back gracefully on any error — callers
never need to guard the return value beyond `if result is not None`.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

# Repository root: server.py → mcp_server/ → masonry/ → project root
_MASONRY_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _MASONRY_DIR.parent
_CLI_DIR = _MASONRY_DIR / "src" / "engine" / "cli"


def _call_js_engine(cli_script: str, args: list[str], timeout: int = 10) -> dict | None:
    """Call a Node.js CLI wrapper in masonry/src/engine/cli/ via subprocess.

    Returns parsed JSON dict on success, None on any failure (triggers Python fallback).
    Logs a WARNING on failure — never raises.
    """
    cli_path = _CLI_DIR / cli_script
    try:
        result = subprocess.run(
            ["node", str(cli_path)] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        logging.warning("[js-engine] %s exit %d: %s", cli_script, result.returncode, result.stderr[:200])
        return None
    except subprocess.TimeoutExpired:
        logging.warning("[js-engine] %s timed out after %ds", cli_script, timeout)
        return None
    except FileNotFoundError:
        logging.warning("[js-engine] node not found or %s missing", cli_path)
        return None
    except json.JSONDecodeError as e:
        logging.warning("[js-engine] %s returned invalid JSON: %s", cli_script, e)
        return None
    except Exception as e:  # noqa: BLE001
        logging.warning("[js-engine] %s unexpected error: %s", cli_script, e)
        return None
