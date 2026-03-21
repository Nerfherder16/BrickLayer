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
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — allow `bl.*` imports from any cwd
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _tool_masonry_status(args: dict) -> dict:
    """Return current campaign status for a project directory."""
    project_dir = Path(args.get("project_dir", os.getcwd()))
    state_file = project_dir / "masonry-state.json"
    questions_file = project_dir / "questions.md"

    result: dict[str, Any] = {
        "project_dir": str(project_dir),
        "has_campaign": state_file.exists(),
    }

    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            result["state"] = state
        except Exception:
            result["state"] = {}

    if questions_file.exists():
        text = questions_file.read_text(errors="replace")
        lines = text.splitlines()
        q_total = sum(1 for ln in lines if ln.startswith("### Q"))
        waves = sum(1 for ln in lines if ln.lower().startswith("## wave"))
        pending = text.count("**Status:** PENDING")
        done = text.count("**Status:** DONE")
        result["questions"] = {
            "total": q_total,
            "waves": waves,
            "pending": pending,
            "done": done,
        }

    return result


def _tool_masonry_questions(args: dict) -> dict:
    """List questions from questions.md, optionally filtered by status."""
    project_dir = Path(args.get("project_dir", os.getcwd()))
    status_filter = args.get("status")  # PENDING | DONE | INCONCLUSIVE | etc.
    limit = int(args.get("limit", 20))

    questions_file = project_dir / "questions.md"
    if not questions_file.exists():
        return {"error": "questions.md not found", "project_dir": str(project_dir)}

    from bl.questions import load_questions  # noqa: PLC0415

    try:
        qs = load_questions(str(questions_file))
        if status_filter:
            qs = [q for q in qs if q.get("status", "").upper() == status_filter.upper()]
        qs = qs[:limit]
        return {"questions": qs, "count": len(qs)}
    except Exception as e:
        return {"error": str(e)}


def _tool_masonry_nl_generate(args: dict) -> dict:
    """Generate research questions from a natural language description."""
    description = args.get("description", "")
    project_dir = args.get("project_dir")
    append = bool(args.get("append", False))

    if not description:
        return {"error": "description is required"}

    from bl.nl_entry import generate_from_description, format_preview, quick_campaign  # noqa: PLC0415

    if append and project_dir:
        result = quick_campaign(description, project_dir=project_dir)
        return result
    else:
        questions = generate_from_description(description)
        return {
            "questions": questions,
            "preview": format_preview(questions),
            "count": len(questions),
        }


def _tool_masonry_weights(args: dict) -> dict:
    """Show question weight report for a project."""
    project_dir = args.get("project_dir", os.getcwd())

    from bl.question_weights import weight_report  # noqa: PLC0415

    try:
        report = weight_report(project_dir)
        return {"report": report}
    except Exception as e:
        return {"error": str(e)}


def _tool_masonry_git_hypothesis(args: dict) -> dict:
    """Generate hypotheses from recent git diff."""
    project_dir = args.get("project_dir", os.getcwd())
    commits = int(args.get("commits", 5))
    max_questions = int(args.get("max_questions", 10))
    dry_run = bool(args.get("dry_run", True))

    from bl.git_hypothesis import (
        get_recent_diff,
        parse_diff_files,
        match_patterns,
        generate_questions,
        append_to_questions_md,
    )  # noqa: PLC0415

    diff = get_recent_diff(commits=commits, cwd=project_dir)
    if not diff:
        return {"error": "No diff found or not a git repository", "questions": []}

    files = parse_diff_files(diff)
    matches = match_patterns(diff, files)
    questions = generate_questions(matches)[:max_questions]

    if not dry_run:
        questions_md = Path(project_dir) / "questions.md"
        if questions_md.exists():
            appended = append_to_questions_md(questions, str(questions_md))
            return {
                "questions": questions,
                "appended": appended,
                "count": len(questions),
            }

    return {
        "questions": questions,
        "count": len(questions),
        "dry_run": dry_run,
        "files_analyzed": files,
        "patterns_matched": [m["pattern"] for m in matches],
    }


def _tool_masonry_run_question(args: dict) -> dict:
    """Run a single BL question by ID and return the verdict envelope."""
    project_dir = args.get("project_dir", os.getcwd())
    question_id = args.get("question_id", "")

    if not question_id:
        return {"error": "question_id is required"}

    from bl.questions import load_questions  # noqa: PLC0415
    from bl.runners import get_runner  # noqa: PLC0415

    questions_file = Path(project_dir) / "questions.md"
    if not questions_file.exists():
        return {"error": "questions.md not found"}

    qs = load_questions(str(questions_file))
    q = next((q for q in qs if q.get("id") == question_id), None)
    if q is None:
        return {"error": f"Question {question_id!r} not found"}

    mode = q.get("mode", "correctness")
    runner = get_runner(mode)
    if runner is None:
        return {"error": f"No runner for mode {mode!r}"}

    try:
        result = runner(q)
        return {"question_id": question_id, "result": result}
    except Exception as e:
        return {"error": str(e), "question_id": question_id}


def _tool_masonry_fleet(args: dict) -> dict:
    """List fleet agents and their scores from registry.json / agent_db.json."""
    project_dir = args.get("project_dir", os.getcwd())
    limit = int(args.get("limit", 30))

    registry_file = Path(project_dir) / "registry.json"
    agent_db_file = Path(project_dir) / "agent_db.json"

    agents = []

    if registry_file.exists():
        try:
            registry = json.loads(registry_file.read_text())
            agents = (
                registry.get("agents", registry)
                if isinstance(registry, dict)
                else registry
            )
        except Exception:
            pass

    scores: dict = {}
    if agent_db_file.exists():
        try:
            db = json.loads(agent_db_file.read_text())
            for name, data in db.items():
                scores[name] = data.get("score", data.get("avg_score", 0))
        except Exception:
            pass

    # Merge scores into agents
    for a in agents:
        name = a.get("name", "")
        if name in scores:
            a["score"] = scores[name]

    # Sort by score descending
    agents_sorted = sorted(agents, key=lambda a: a.get("score", 0), reverse=True)[
        :limit
    ]

    return {
        "agents": agents_sorted,
        "count": len(agents_sorted),
        "has_scores": bool(scores),
    }


def _tool_masonry_recall_search(args: dict) -> dict:
    """Search Recall for memories relevant to a query."""
    query = args.get("query", "")
    limit = int(args.get("limit", 10))
    domain = args.get("domain")

    if not query:
        return {"error": "query is required"}

    from bl.recall_bridge import search_prior_findings  # noqa: PLC0415

    try:
        results = search_prior_findings(query, domain=domain, limit=limit)
        return {
            "results": results,
            "count": len(results) if isinstance(results, list) else 0,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# New tool implementations — routing, optimization, onboarding, drift, registry
# ---------------------------------------------------------------------------


def _tool_masonry_route(args: dict) -> dict:
    """Route a request to the appropriate Masonry agent using the four-layer router."""
    request_text = args.get("request_text", "")
    project_dir = Path(args.get("project_dir", os.getcwd()))

    if not request_text:
        return {"error": "request_text is required"}

    try:
        from masonry.src.routing.router import route  # noqa: PLC0415

        decision = route(request_text, project_dir)
        return decision.model_dump()
    except Exception as exc:
        return {
            "error": str(exc),
            "target_agent": "user",
            "layer": "fallback",
            "confidence": 0.0,
            "reason": f"Router import failed: {str(exc)[:80]}",
            "fallback_agents": [],
            "fallback_reason": "multi_failure",
        }


def _tool_masonry_optimization_status(args: dict) -> dict:
    """Return DSPy optimization scores for all agents in the optimized_prompts directory."""
    optimized_dir = Path(
        args.get("optimized_dir", str(_REPO_ROOT / "masonry" / "optimized_prompts"))
    )

    agents: list[dict] = []

    if not optimized_dir.is_dir():
        return {"agents": [], "count": 0}

    for json_file in sorted(optimized_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if "agent" in data:
                agents.append(
                    {
                        "agent": data["agent"],
                        "score": data.get("score", 0.0),
                        "optimized_at": data.get("optimized_at"),
                    }
                )
        except Exception:
            pass

    return {"agents": agents, "count": len(agents)}


def _tool_masonry_optimize_agent(args: dict) -> dict:
    """Trigger MIPROv2 prompt optimization for a single agent."""
    agent_name = args.get("agent_name", "")
    if not agent_name:
        return {"error": "agent_name is required"}

    projects_dir = Path(args.get("projects_dir", str(_REPO_ROOT)))
    agent_db_path = Path(
        args.get("agent_db_path", str(_REPO_ROOT / "agent_db.json"))
    )
    questions_md_path_str = args.get("questions_md_path")
    questions_md_path = Path(questions_md_path_str) if questions_md_path_str else None
    output_dir = Path(
        args.get("output_dir", str(_REPO_ROOT / "masonry" / "optimized_prompts"))
    )
    model = args.get("model", "claude-sonnet-4-6")

    try:
        from masonry.src.dspy_pipeline.training_extractor import build_dataset  # noqa: PLC0415
        from masonry.src.dspy_pipeline.optimizer import configure_dspy, optimize_agent  # noqa: PLC0415
        from masonry.src.dspy_pipeline.signatures import ResearchAgentSig  # noqa: PLC0415
    except ImportError as exc:
        return {"error": f"DSPy pipeline import failed: {exc}"}

    datasets = build_dataset(projects_dir, agent_db_path, questions_md_path=questions_md_path)
    agent_dataset = datasets.get(agent_name, [])

    if len(agent_dataset) < 5:
        return {
            "error": f"Insufficient training data for {agent_name}: {len(agent_dataset)} examples (need >= 5)",
            "example_count": len(agent_dataset),
        }

    try:
        configure_dspy(model=model)
    except Exception as exc:
        return {"error": f"DSPy configuration failed: {exc}"}

    try:
        result = optimize_agent(agent_name, ResearchAgentSig, agent_dataset, output_dir)
        result["example_count"] = len(agent_dataset)
        return result
    except Exception as exc:
        return {"error": f"Optimization failed: {exc}", "agent": agent_name}


def _tool_masonry_onboard(args: dict) -> dict:
    """Detect and register new agent .md files not yet in the registry."""
    agents_dirs_raw = args.get("agents_dirs", [])
    registry_path_str = args.get(
        "registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml")
    )
    dspy_output_dir_str = args.get(
        "dspy_output_dir",
        str(_REPO_ROOT / "masonry" / "src" / "dspy_pipeline" / "generated"),
    )

    if isinstance(agents_dirs_raw, str):
        agents_dirs_raw = [agents_dirs_raw]

    agents_dirs = [Path(d) for d in agents_dirs_raw] if agents_dirs_raw else [
        Path.home() / ".claude" / "agents",
        Path("agents"),
    ]
    registry_path = Path(registry_path_str)
    dspy_output_dir = Path(dspy_output_dir_str)

    try:
        from masonry.scripts.onboard_agent import onboard  # noqa: PLC0415

        result = onboard(agents_dirs, registry_path, dspy_output_dir)
        # Return names of newly-added agents under the "onboarded" key for
        # backwards compatibility with callers that expect a list of names.
        names = result.get("names", [])
        return {
            "onboarded": names,
            "count": result.get("added", len(names)),
            "updated": result.get("updated", 0),
            "stale": result.get("stale", 0),
            "warnings": result.get("warnings", []),
        }
    except Exception as exc:
        return {"error": str(exc), "onboarded": [], "count": 0}


def _tool_masonry_drift_check(args: dict) -> dict:
    """Run drift detection for all registry agents that have verdict history."""
    agent_db_path_str = args.get(
        "agent_db_path", str(_REPO_ROOT / "agent_db.json")
    )
    registry_path_str = args.get(
        "registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml")
    )

    agent_db_path = Path(agent_db_path_str)
    registry_path = Path(registry_path_str)

    try:
        from masonry.src.dspy_pipeline.drift_detector import run_drift_check  # noqa: PLC0415
        from masonry.src.schemas.registry_loader import load_registry  # noqa: PLC0415

        registry = load_registry(registry_path)
        reports = run_drift_check(agent_db_path, registry)
        return {
            "reports": [r.model_dump() for r in reports],
            "count": len(reports),
        }
    except Exception as exc:
        return {"error": str(exc), "reports": []}


def _tool_masonry_registry_list(args: dict) -> dict:
    """List agents from the Masonry agent registry YAML."""
    registry_path = Path(
        args.get("registry_path", str(_REPO_ROOT / "masonry" / "agent_registry.yml"))
    )
    tier_filter = args.get("tier")
    mode_filter = args.get("mode")

    try:
        from masonry.src.schemas.registry_loader import (  # noqa: PLC0415
            load_registry,
            get_agents_for_mode,
        )

        registry = load_registry(registry_path)
        agents = registry

        if mode_filter:
            agents = get_agents_for_mode(agents, mode_filter)

        if tier_filter:
            agents = [a for a in agents if a.tier == tier_filter]

        return {
            "agents": [a.model_dump(exclude_none=True) for a in agents],
            "count": len(agents),
        }
    except Exception as exc:
        return {"error": str(exc), "agents": [], "count": 0}


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
    "masonry_optimization_status": {
        "fn": _tool_masonry_optimization_status,
        "description": (
            "Return DSPy prompt optimization scores for all agents. "
            "Reads from the optimized_prompts directory (JSON files saved by MIPROv2)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "optimized_dir": {
                    "type": "string",
                    "description": "Directory containing optimized agent JSON files. "
                    "Defaults to masonry/optimized_prompts/.",
                },
            },
        },
    },
    "masonry_optimize_agent": {
        "fn": _tool_masonry_optimize_agent,
        "description": (
            "Trigger MIPROv2 prompt optimization for a specific agent using campaign findings as training data. "
            "Requires ANTHROPIC_API_KEY. Saves optimized module to masonry/optimized_prompts/{agent}.json."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["agent_name"],
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent to optimize, e.g. 'research-analyst'.",
                },
                "projects_dir": {
                    "type": "string",
                    "description": "Root directory to scan for findings. Defaults to repository root.",
                },
                "agent_db_path": {
                    "type": "string",
                    "description": "Path to agent_db.json. Defaults to agent_db.json at repository root.",
                },
                "questions_md_path": {
                    "type": "string",
                    "description": "Path to questions.md for agent attribution. Auto-discovered if omitted.",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save optimized prompt JSON. Defaults to masonry/optimized_prompts/.",
                },
                "model": {
                    "type": "string",
                    "description": "Anthropic model for optimization. Defaults to claude-sonnet-4-6.",
                    "default": "claude-sonnet-4-6",
                },
            },
        },
    },
    "masonry_onboard": {
        "fn": _tool_masonry_onboard,
        "description": (
            "Detect new agent .md files not yet in the registry and onboard them: "
            "register in agent_registry.yml and generate DSPy signature stubs."
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
                "dspy_output_dir": {
                    "type": "string",
                    "description": "Output dir for DSPy stubs. Defaults to masonry/src/dspy_pipeline/generated/.",
                },
            },
        },
    },
    "masonry_drift_check": {
        "fn": _tool_masonry_drift_check,
        "description": (
            "Run drift detection for all registry agents with verdict history. "
            "Returns DriftReport per agent with alert_level (ok/warning/critical) and recommendation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_db_path": {
                    "type": "string",
                    "description": "Path to agent_db.json containing verdict history. Defaults to agent_db.json at repository root.",
                },
                "registry_path": {
                    "type": "string",
                    "description": "Path to agent_registry.yml. Defaults to masonry/agent_registry.yml.",
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
                "registry_path": {
                    "type": "string",
                    "description": "Path to agent_registry.yml. Defaults to masonry/agent_registry.yml.",
                },
                "tier": {
                    "type": "string",
                    "enum": ["draft", "candidate", "trusted", "retired"],
                    "description": "Filter by agent tier.",
                },
                "mode": {
                    "type": "string",
                    "description": "Filter agents that support this mode (e.g. 'simulate', 'fix').",
                },
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
        result = []
        for name, spec in TOOLS.items():
            result.append(
                mcp_types.Tool(
                    name=name,
                    description=spec["description"],
                    inputSchema=spec["inputSchema"],
                )
            )
        return result

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
        line = json.dumps(obj)
        stdout.write(line + "\n")
        stdout.flush()

    # Send initialize notification on startup
    # (Clients may send initialize request first; we handle it below)

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
            send(
                {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "masonry", "version": "1.0.0"},
                    },
                }
            )

        elif method == "tools/list":
            tools_list = []
            for name, spec in TOOLS.items():
                tools_list.append(
                    {
                        "name": name,
                        "description": spec["description"],
                        "inputSchema": spec["inputSchema"],
                    }
                )
            send({"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": tools_list}})

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            spec = TOOLS.get(tool_name)
            if spec is None:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}",
                        },
                    }
                )
            else:
                try:
                    output = spec["fn"](arguments)
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(output, indent=2),
                                    }
                                ],
                            },
                        }
                    )
                except Exception as e:
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {"code": -32603, "message": str(e)},
                        }
                    )

        elif method == "notifications/initialized":
            # No response needed for notifications
            pass

        elif rpc_id is not None:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            )


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
