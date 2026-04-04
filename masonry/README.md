# Masonry

Orchestration platform for Claude Code — routes every request to the right specialist, enforces lifecycle guardrails, and drives the full software development and research campaign lifecycle.

> A mason works with the same raw material as a bricklayer but with greater precision, scope, and craft.

---

## What It Is

Masonry is the bridge layer between Claude Code and BrickLayer 2.0. It does not do work itself — it routes, guards, and connects.

- **Mortar router** — every request lands here first; dispatches in parallel to the right agents
- **32-hook lifecycle system** — session start/end, write guards, lint, TDD enforcement, session locking
- **22-tool MCP server** — Node.js JSON-RPC server exposing campaign, dev, fleet, and health tools
- **9 background daemon workers** — run between sessions: test gaps, optimization, consolidation, deep research, pattern learning, codebase mapping, documentation, refactoring candidates, benchmark regression
- **80-agent fleet** — registry-tracked, scored, and auto-onboarded
- **Four-layer routing engine** — deterministic → semantic → LLM → fallback
- **Self-improvement pipeline** — eval → optimize → compare loop; no API key or labeled dataset required
- **Recall-native memory** — all sessions and findings flow into System-Recall at `http://100.70.195.84:8200`

---

## Structure

```
masonry/
  bin/
    masonry-mcp.js          Node.js MCP server (22 tools, JSON-RPC over stdio)
    masonry-setup.js        Interactive installer (config, hooks, settings.json merge)
    masonry-init-wizard.js  /masonry-init project scaffold wizard
    masonry-fleet-cli.js    Fleet CLI: status / add / retire / regen
  src/
    core/
      config.js             Config loader (~/.masonry/config.json + env overrides)
      state.js              masonry-state.json read/write
      recall.js             Recall HTTP client (storeMemory, searchMemory, isAvailable)
      registry.js           Agent registry generator
      skill-surface.js      Recall skill retriever (project-scoped + global dedup)
      mas.js                Shared helpers (isResearchProject, findProjectRoot, etc.)
    hooks/                  32 Claude Code hook scripts (Node.js)
    daemon/
      daemon-manager.sh     Starts all 9 background workers
      worker-testgaps.js    Finds untested implementation files
      worker-optimize.js    Triggers agent optimization cycles
      worker-consolidate.js Deduplicates Recall build patterns
      worker-deepdive.js    Deep research on flagged questions
      worker-ultralearn.js  Stores new patterns from session findings
      worker-map.js         Codebase topology mapping
      worker-document.js    Docstring/JSDoc gap analysis
      worker-refactor.js    God file + deep nesting detection
      worker-benchmark.js   Test suite timing + regression detection
    routing/
      router.py             Four-layer orchestrating router
      deterministic.py      Layer 1 (0 LLM calls)
      semantic.py           Layer 2 (Ollama cosine similarity)
      llm_router.py         Layer 3 (1 Haiku call)
    schemas/
      payloads.py           Pydantic v2 payload contracts
      registry_loader.py    YAML registry parser
    scoring/
      rubrics.py            Heuristic scoring rubrics
  scripts/
    improve_agent.py        Eval → optimize → compare loop
    eval_agent.py           Held-out eval runner
    optimize_with_claude.py Instruction optimizer
    writeback.py            Inject optimized instructions into agent .md files
    onboard_agent.py        Agent auto-onboarding pipeline
    score_all_agents.py     Unified fleet scorer
  skills/                   /skill-name.md definitions (13 skills)
  agent_registry.yml        80-agent declarative registry (YAML, Pydantic-validated)
  hooks.json                Hook manifest (consumed by masonry-setup.js)
  package.json              Node.js package (masonry-mcp, no runtime deps)
  requirements.txt          Python dependencies (pydantic, httpx, PyYAML)
```

---

## Quick Start

Masonry is already installed and running. The MCP server starts automatically via Claude Code's MCP config. All 32 hooks are wired in `~/.claude/settings.json`.

### Agent Optimization

```bash
cd C:/Users/trg16/Dev/Bricklayer2.0

# Single cycle: eval → optimize → compare
python masonry/scripts/improve_agent.py research-analyst

# Multiple cycles
python masonry/scripts/improve_agent.py research-analyst --loops 3

# Baseline eval only (no changes)
python masonry/scripts/improve_agent.py research-analyst --dry-run

# Karen uses a specialized scoring signature
python masonry/scripts/improve_agent.py karen --signature karen
```

Run from Git Bash (not inside an active Claude session).

### Daemon Workers

```bash
bash masonry/src/daemon/daemon-manager.sh
```

Workers run in background and write output to `.autopilot/`:
- `test-gaps.md` — implementation files missing test coverage
- `refactor-candidates.md` — god files, duplicate blocks, deep nesting
- `benchmark.md` — test timing baselines and regressions

Workers also store patterns to Recall and are auto-started at session begin when a project directory is detected.

---

## MCP Tools (22)

| Tool | Purpose |
|------|---------|
| `masonry_status` | Campaign state, question counts, wave |
| `masonry_questions` | List questions filtered by status |
| `masonry_findings` | List findings filtered by verdict/severity |
| `masonry_run` | Run the research loop for a project |
| `masonry_nl_generate` | Generate questions from plain English |
| `masonry_weights` | Question weight report |
| `masonry_git_hypothesis` | Questions from recent git diffs |
| `masonry_run_question` | Run a single question by ID |
| `masonry_run_simulation` | Run simulate.py with given parameters |
| `masonry_sweep` | Parameter sweep across scenario space |
| `masonry_fleet` | Agent list with scores |
| `masonry_recall` | Search Recall memories |
| `masonry_route` | Route through four-layer engine |
| `masonry_pattern_store` | Store a build pattern |
| `masonry_pattern_search` | Search build patterns |
| `masonry_worker_status` | Daemon worker PID status + output freshness |
| `masonry_task_assign` | Assign autopilot task to worker |
| `masonry_agent_health` | Agent score, drift, run history |
| `masonry_wave_validate` | Validate campaign wave quality |
| `masonry_swarm_init` | Initialize parallel agent swarm |
| `masonry_consensus_check` | Multi-agent consensus vote |
| `masonry_doctor` | System health check (Recall, daemons, hooks, registry, training data) |

---

## Hook System (32 hooks)

Hooks are Node.js scripts invoked by Claude Code on lifecycle events. All are graceful — any error exits 0, never blocking Claude Code.

| Event | Hook | Purpose |
|-------|------|---------|
| SessionStart | `masonry-session-start` | Restore context; auto-start daemons; write session lock |
| UserPromptSubmit | `masonry-register` | Register prompt for routing |
| UserPromptSubmit | `masonry-prompt-router` | Auto-route via intent detection |
| PreToolUse Write/Edit | `masonry-session-lock` | Block writes to files owned by another session |
| PreToolUse Write/Edit/Bash | `masonry-approver` | Auto-approve in build/fix/compose mode |
| PreToolUse ExitPlanMode | `masonry-context-safety` | Block if build active or context ≥80% |
| PreToolUse Agent | `masonry-mortar-enforcer` | Force routing through Mortar |
| PreToolUse Agent | `masonry-preagent-tracker` | Track agent spawns before start |
| PostToolUse Write/Edit | `masonry-observe` | Finding detection + Recall storage (async) |
| PostToolUse Write/Edit | `masonry-lint-check` | ruff + prettier + eslint |
| PostToolUse Write/Edit | `masonry-design-token-enforcer` | Warn on hardcoded hex/banned fonts |
| PostToolUse Write/Edit | `masonry-guard` | 3-strike error fingerprinter (async) |
| PostToolUse Write/Edit | `masonry-tdd-enforcer` | Block in build mode if no test file |
| PostToolUse Write/Edit | `masonry-agent-onboard` | Auto-onboard new agent .md files (async) |
| PostToolUse Write/Edit | `masonry-build-patterns` | Extract + store build patterns to Recall (async) |
| PostToolUse Write/Edit | `masonry-pulse` | Session heartbeat to `.mas/pulse.jsonl` |
| PostToolUseFailure | `masonry-tool-failure` | Error tracking + 3-strike escalation |
| SubagentStart | `masonry-subagent-tracker` | Track active agent spawns |
| TeammateIdle / TaskCompleted | `masonry-teammate-idle` | Auto-assign pending tasks to idle agents |
| SessionEnd | `masonry-session-end` | Agent trust scoring; release session lock |
| PreCompact | `masonry-pre-compact` | Preserve state before context compaction |
| Stop | `masonry-stop-guard` | Block on uncommitted git changes |
| Stop | `masonry-session-summary` | Write session summary |
| Stop | `masonry-handoff` | Write handoff notes (async) |
| Stop | `masonry-context-monitor` | Warn when context exceeds 750K tokens |
| Stop | `masonry-build-guard` | Block if `.autopilot/` has pending tasks |
| Stop | `masonry-ui-compose-guard` | Block if `.ui/` compose has pending tasks |
| Stop | `masonry-score-trigger` | Trigger agent scoring if training data >24h stale (async) |
| Stop | `masonry-system-status` | Write system health snapshot |
| Stop | `masonry-training-export` | Export findings to training corpus |
| statusLine | `masonry-statusline` | Live status in Claude Code status bar |

---

## External Dependencies

| Service | URL | Used by |
|---------|-----|---------|
| Recall (System-Recall) | http://100.70.195.84:8200 | recall.js, hooks, daemon workers |
| Ollama | http://192.168.50.62:11434 | semantic.py (qwen3-embedding:0.6b) |
| Claude CLI | subprocess | llm_router.py, improve_agent.py |

All external calls have timeouts (2–15s) and fail gracefully. Masonry remains functional if any service is unavailable.
