# BrickLayer 2.0 — Session Context

## What BrickLayer Is

BrickLayer is a **full project lifecycle system** — from first idea to running production code to ongoing maintenance. It is NOT just a research or investigation tool. The name is literal: **it lays every brick**.

BrickLayer orchestrates the entire build through its engine (`bl/`), agent fleet, mode system, and inter-agent communication layer. Claude Code is the execution runtime; BrickLayer drives what gets built, how it's verified, and how it evolves.

**If you think BrickLayer is "just research" — you're wrong. Read this section again.**

## The Lifecycle (Build Is a First-Class Phase)

```
CONCEPTION     Frontier mode — structured hypothesis generation
VALIDATION     Research mode — evidence-based stress testing
PRE-BUILD      Validate + Benchmark — design verification + baselines
BUILD          Agent orchestration, swarm runners, code generation, inter-agent
               coordination via Recall — BrickLayer drives the build
POST-BUILD     Audit + Diagnose — compliance and fault detection
REPAIR         Fix mode + heal loop — automated diagnose→fix→verify cycles
ONGOING        Evolve + Predict + Monitor — continuous improvement
```

Every phase is BrickLayer. There is no handoff to an external system.

## Engine & Structure

Engine: `bl/` (Python + tmux). Key dirs: `bl/runners/` (15 runner types), `bl/tmux/` (agent orchestration), `bl/healloop.py` (diagnose→fix→verify), `bl/crucible.py` (agent benchmarking). Projects under `projects/`. Campaigns under named subdirs. Module details: see `bl/` source directly.

9 modes (each has its own `program.md` + verdict vocabulary): Frontier · Research · Validate · Benchmark · Diagnose · Fix · Audit · Evolve · Predict · Monitor.

## Code Retrieval — jCodeMunch First

**Use `jcodemunch-mcp` for all symbol-level code access in this repo.**

BrickLayer agent swarms run up to 8 workers in parallel — each worker reading entire files redundantly burns context fast. jCodeMunch indexes once and lets every agent retrieve only the symbols they need.

- `search_symbols` — find functions/classes by name before reading anything
- `get_symbol_source` — fetch exact implementation instead of `Read` on whole file
- `get_file_outline` — understand a file's structure without reading its body
- `get_blast_radius` — check impact before any refactor in `bl/`
- `get_call_hierarchy` — trace callers/callees across the engine without grep

**Only use `Read` when you genuinely need the full file** (e.g., file-level restructuring). For everything else, jCodeMunch first.

---

## MANDATORY: Agent Delegation via BrickLayer tmux Dispatch

**You are an orchestrator. You do NOT work alone.**

All agent dispatch goes through BrickLayer's tmux layer (`bl/tmux/core.py`). This spawns agents in visible tmux panes with `stream-json` output piped through `stream_format.py` — the user watches agents work in real time. When not in tmux, it falls back to subprocess.

**NEVER use Claude Code's built-in `Task` tool for agent work.** It spawns invisible child processes with no tmux panes, no signal files, no lifecycle hooks, and no masonry tracking.

### How to Spawn Agents

```python
from bl.tmux.core import spawn_agent, wait_for_agent

handle = spawn_agent(
    "rough-in",
    "Task: <user request>\nProject root: /path/to/project",
    cwd="/path/to/project",
    dangerously_skip_permissions=True,
)
result = wait_for_agent(handle)
```

For parallel dispatch (multiple agents at once), use `bl/tmux/wave.py:spawn_wave()`.

### Delegation Rules

| Task type | Spawn directly |
|-----------|---------------|
| **Dev tasks** (build, fix, refactor, feature, implement) | `rough-in` |
| **Campaigns / research** (investigate, frontier, audit, BL run) | `mortar` (hands off to Trowel) |
| **Documentation only** (changelog, docs, roadmap) | `karen` |
| **All other tasks** (UI, security, git, architecture, etc.) | Named specialist directly |

Do NOT route dev tasks through Mortar — it adds an unnecessary hop. You do NOT spawn sub-specialists directly; rough-in and Mortar's coordinators handle that.

### Self-Invoke: Direct Agent Bypass

**Tim can bypass routing entirely with the `@agent-name:` prefix:**

```
@rough-in: build the new auth endpoint
@karen: update the changelog for this release
@diagnose-analyst: why is the session lock failing
```

When a prompt starts with `@<agent-name>:`, skip all routing logic and spawn that agent directly.

### When You May Work Directly (Exceptions)

- Simple questions (< 1 paragraph, no code changes)
- Reading files to understand context before delegating
- Read-only git operations (status, log, diff)
- Trivial one-line fixes the user explicitly dictates verbatim

### Agent Hierarchy

```
rough-in (dev tasks — direct entry point)
├── Queen Coordinator → parallel dispatch: developer, test-writer, code-reviewer, security, etc.
├── diagnose-analyst → fix-implementer (fix cycles)
└── git-nerd (on completion)

mortar (campaigns/research — entry point for BL loops)
└── trowel (campaign conductor)

karen (documentation — direct entry point)
```

**Authoritative agent source:** `masonry/agent_registry.yml` (100+ agents). Routing: 4-layer system (keywords → embeddings → LLM → fallback). Use `@agent-name:` to bypass.

## What NOT to Assume

- BrickLayer is NOT just research — it orchestrates builds, fixes, and maintenance
- Modes are NOT sequential requirements — projects skip, reorder, and loop back
- The agent fleet is NOT static — agents are benchmarked, promoted, and retired by crucible
- Inter-agent communication happens through Recall — agents share memory and context
- The build phase is NOT external — BrickLayer drives it through runners and agent orchestration
