#!/usr/bin/env python3
"""
simulate_server.py — Persistent stdio JSON wrapper around simulate.run_simulation().

Protocol:
  stdin:  one JSON object per line  e.g. {"months": 36, "churn_rate": 0.05}
  stdout: one JSON object per line  e.g. {"records": [...], "failure_reason": null, "verdict": "HEALTHY"}
  stderr: error messages only

Usage:
  python simulate_server.py

Start once per session, reuse for many calls. Exits on EOF or SIGTERM.
Agents should communicate via masonry_run_simulation MCP tool, which manages
the subprocess lifecycle. Direct use is for debugging only.
"""

import sys
import json

# Enforce UTF-8 I/O regardless of terminal/console code page (Windows cp1252 fix)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from simulate import run_simulation, evaluate  # noqa: E402


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            params = json.loads(line)
            records, failure_reason = run_simulation(**params)
            result = evaluate(records, failure_reason)
            result["records"] = records
            print(json.dumps(result), flush=True)  # noqa: mcp-stdout
        except Exception as e:
            print(  # noqa: mcp-stdout
                json.dumps(
                    {
                        "error": str(e),
                        "records": [],
                        "verdict": "FAILURE",
                        "failure_reason": str(e),
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
