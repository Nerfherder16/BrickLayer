#!/usr/bin/env python3
"""
masonry/mcp_server/server.py — Masonry MCP server.

Exposes BrickLayer 2.0 campaign and fleet operations via the Model Context
Protocol. Any MCP client (Claude Code, Kiln, CI tooling) can query campaign
status, generate questions, inspect agent weights, and run questions without
knowing the file layout.

Transport:
    Primary:  MCP Python SDK (stdio transport)  — if `mcp` is installed
    Fallback: Raw JSON-RPC 2.0 over stdio       — always available, no deps

Usage:
    python -m masonry.mcp_server.server          # stdio transport
    python masonry/mcp_server/server.py          # same

Register in ~/.claude.json:
    "masonry": {
        "command": "python",
        "args": ["-m", "masonry.mcp_server.server"],
        "cwd": "C:/Users/trg16/Dev/Bricklayer2.0"
    }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allow `bl.*` imports from any cwd
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Tool implementations (split into focused modules)
# ---------------------------------------------------------------------------

from masonry.mcp_server.tools.campaign import (  # noqa: E402
    _tool_masonry_status,
    _tool_masonry_questions,
    _tool_masonry_nl_generate,
    _tool_masonry_weights,
    _tool_masonry_git_hypothesis,
    _tool_masonry_run_question,
)
from masonry.mcp_server.tools.fleet import (  # noqa: E402
    _tool_masonry_fleet,
    _tool_masonry_recall_search,
    _tool_masonry_optimization_status,
    _tool_masonry_drift_check,
)
from masonry.mcp_server.tools.routing import (  # noqa: E402
    _tool_masonry_route,
    _tool_masonry_onboard,
    _tool_masonry_registry_list,
)

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS = {
    "masonry_status": {
        "fn": _tool_masonry_status,
        "description": "Get current campaign status (state, question counts, wave) for a project directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Path to the project directory. Defaults to cwd.",
                },
            },
        },
    },
    "masonry_questions": {
        "fn": _tool_masonry_questions,
        "description": "List questions from questions.md, optionally filtered by status (PENDING, DONE, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
                "status": {
                    "type": "string",
                    "description": "Filter by status: PENDING, DONE, INCONCLUSIVE, FAILURE, WARNING, HEALTHY",
                },
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    "masonry_nl_generate": {
        "fn": _tool_masonry_nl_generate,
        "description": "Generate BrickLayer research questions from a plain English description of what changed.",
        "inputSchema": {
            "type": "object",
            "required": ["description"],
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Natural language description, e.g. 'I just added concurrent Neo4j writes'",
                },
                "project_dir": {
                    "type": "string",
                    "description": "If set with append=true, appends questions to questions.md",
                },
                "append": {"type": "boolean", "default": False},
            },
        },
    },
    "masonry_weights": {
        "fn": _tool_masonry_weights,
        "description": "Show question weight report — which questions are high priority, prunable, or flagged for retry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
            },
        },
    },
    "masonry_git_hypothesis": {
        "fn": _tool_masonry_git_hypothesis,
        "description": "Analyze recent git diffs and generate targeted research questions for changed code paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
                "commits": {
                    "type": "integer",
                    "default": 5,
                    "description": "How many recent commits to analyze",
                },
                "max_questions": {"type": "integer", "default": 10},
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "If false, appends to questions.md",
                },
            },
        },
    },
    "masonry_run_question": {
        "fn": _tool_masonry_run_question,
        "description": "Run a single BL question by ID and return the verdict envelope {verdict, summary, data}.",
        "inputSchema": {
            "type": "object",
            "required": ["question_id"],
            "properties": {
                "project_dir": {"type": "string"},
                "question_id": {
                    "type": "string",
                    "description": "Question ID, e.g. 'Q1' or 'R1.1'",
                },
            },
        },
    },
    "masonry_fleet": {
        "fn": _tool_masonry_fleet,
        "description": "List fleet agents and their performance scores from registry.json and agent_db.json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
                "limit": {"type": "integer", "default": 30},
            },
        },
    },
    "masonry_recall_search": {
        "fn": _tool_masonry_recall_search,
        "description": "Search Recall for memories relevant to a query (campaign findings, prior knowledge).",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "domain": {"type": "string", "description": "Optional domain filter"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    "masonry_optimization_status": {
        "fn": _tool_masonry_optimization_status,
        "description": (
            "Return optimization scores for all agents that have completed the improve_agent loop. "
            "Reads *.json files from the optimized_prompts directory, each containing {score, ...}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "optimized_dir": {
                    "type": "string",
                    "description": "Path to the optimized_prompts directory. Defaults to masonry/optimized_prompts/.",
                },
            },
        },
    },
    "masonry_route": {
        "fn": _tool_masonry_route,
        "description": (
            "Route a request to the appropriate Masonry agent using the four-layer routing engine "
            "(deterministic → semantic → LLM → fallback). Returns a RoutingDecision with "
            "target_agent, layer, confidence, and reasoning."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["request_text"],
            "properties": {
                "request_text": {
                    "type": "string",
                    "description": "The user request text to route.",
                },
                "project_dir": {
                    "type": "string",
                    "description": "Project directory for context. Defaults to cwd.",
                },
            },
        },
    },
    "masonry_onboard": {
        "fn": _tool_masonry_onboard,
        "description": (
            "Detect new agent .md files not yet in the registry and onboard them: "
            "register in agent_registry.yml."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agents_dirs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Directories to scan for agent .md files.",
                },
                "registry_path": {
                    "type": "string",
                    "description": "Path to agent_registry.yml. Defaults to masonry/agent_registry.yml.",
                },
            },
        },
    },
    "masonry_drift_check": {
        "fn": _tool_masonry_drift_check,
        "description": (
            "Run drift detection for all registry agents with verdict history. "
            "Returns DriftReport per agent with alert_level (ok/warning/critical) and recommendation. "
            "Set auto_trigger=true to automatically spawn improve_agent.py for drifted agents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_db_path": {"type": "string"},
                "registry_path": {"type": "string"},
                "auto_trigger": {"type": "boolean"},
                "trigger_level": {
                    "type": "string",
                    "enum": ["critical", "warning"],
                },
            },
        },
    },
    "masonry_registry_list": {
        "fn": _tool_masonry_registry_list,
        "description": (
            "List agents from the Masonry agent registry YAML, "
            "optionally filtered by tier (draft/candidate/trusted/retired) or mode."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "registry_path": {"type": "string"},
                "tier": {
                    "type": "string",
                    "enum": ["draft", "candidate", "trusted", "retired"],
                },
                "mode": {"type": "string"},
            },
        },
    },
}


# ---------------------------------------------------------------------------
# MCP SDK transport (primary)
# ---------------------------------------------------------------------------


def _run_sdk_server() -> None:
    from mcp.server import Server  # type: ignore
    from mcp.server.stdio import stdio_server  # type: ignore
    from mcp import types as mcp_types  # type: ignore
    import asyncio

    server = Server("masonry")

    @server.list_tools()
    async def list_tools():
        return [
            mcp_types.Tool(
                name=name,
                description=spec["description"],
                inputSchema=spec["inputSchema"],
            )
            for name, spec in TOOLS.items()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        spec = TOOLS.get(name)
        if spec is None:
            raise ValueError(f"Unknown tool: {name}")
        output = spec["fn"](arguments or {})
        return [mcp_types.TextContent(type="text", text=json.dumps(output, indent=2))]

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    asyncio.run(_main())


# ---------------------------------------------------------------------------
# Raw JSON-RPC 2.0 fallback transport
# ---------------------------------------------------------------------------


def _run_raw_server() -> None:
    """Minimal JSON-RPC 2.0 over stdin/stdout — no mcp SDK required."""
    import io

    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

    def send(obj: dict) -> None:
        stdout.write(json.dumps(obj) + "\n")
        stdout.flush()

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        rpc_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "masonry", "version": "1.0.0"},
                },
            })

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tools": [
                        {"name": n, "description": s["description"], "inputSchema": s["inputSchema"]}
                        for n, s in TOOLS.items()
                    ]
                },
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            spec = TOOLS.get(tool_name)
            if spec is None:
                send({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}})
            else:
                try:
                    output = spec["fn"](arguments)
                    send({"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(output, indent=2)}]}})
                except Exception as e:
                    send({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32603, "message": str(e)}})

        elif method == "notifications/initialized":
            pass

        elif rpc_id is not None:
            send({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        import mcp  # noqa: F401
        _run_sdk_server()
    except ImportError:
        _run_raw_server()


if __name__ == "__main__":
    main()
