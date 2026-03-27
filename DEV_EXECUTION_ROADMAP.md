# BrickLayer Dev Execution Roadmap
# Goal: Ruflo-level end-to-end app creation capability
# Reference: ruvnet/ruflo studied 2026-03-27
# Language note: Ruflo is TypeScript; BrickLayer agents are Markdown prompts + JS hooks

---

## Phase 1 — Zero-Friction Core (Highest Impact, Build First)

### 1.1 UserPromptSubmit Transparent Router ✅ DONE
**File**: `masonry/src/hooks/masonry-prompt-router.js`
**Trigger**: UserPromptSubmit (fires before Claude sees the prompt)
**What it does**:
- Reads prompt from stdin
- Detects intent: coding / research / git / UI / campaign / architecture / debug
- Injects routing suggestion into context: "→ Mortar: routing to developer+test-writer+code-reviewer"
- Falls back silently if intent unclear or slash command
**Impact**: Every natural-language request auto-routed — no slash commands required.
**Ruflo equivalent**: `hook-handler.cjs route` via UserPromptSubmit

### 1.2 TeammateIdle Auto-Assignment ✅ DONE
**File**: `masonry/src/hooks/masonry-teammate-idle.js`
**Wired into settings.json**: `TeammateIdle` + `TaskCompleted` hook events.
**What it does**:
- Fires when an agent team member goes idle or completes a task
- Reads `.autopilot/progress.json`, atomically claims first PENDING task (marks IN_PROGRESS)
- Outputs TDD task assignment with SPARC mode support (`[mode:tdd]`, `[mode:security]`, etc.)
- Handles all-done signal when no tasks remain
**Prereq**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` — already set in settings.json.
**Ruflo equivalent**: `post-task` handler + `autoAssignOnIdle: true`

---

## Phase 2 — Pattern Memory (Learning Loop)

### 2.1 Build Pattern Extraction
**File**: `masonry/src/hooks/masonry-build-patterns.js`
**Trigger**: PostToolUse(Write|Edit) during a build session
**What it does**:
- Detects if `.autopilot/` is active
- Extracts: file type, framework, pattern name from the written code
- Stores to Recall: `domain: "build-patterns"`, tags: `["lang:python", "framework:fastapi", "layer:router"]`
**Ruflo equivalent**: `trainPatternsOnComplete: true` in agentTeams coordination config

### 2.2 SessionStart Pattern Import
**File**: `masonry/src/hooks/masonry-session-start.js` (extend existing)
**What it does**: Query Recall for build patterns matching current project type and inject as context preamble.
**Ruflo equivalent**: `session-restore` + `auto-memory-hook.mjs import`

---

## Phase 3 — New Agents (Add to ~/.claude/agents/)

### 3.1 Swarm Coordination Agents
- `hierarchical-coordinator` — enforces coordinator→worker topology, detects drift
- `adaptive-coordinator` — switches topology (hierarchical/mesh/ring) based on task type
- `queen-coordinator` — assigns tasks from shared queue to idle workers (hive-mind pattern)
- `worker-specialist` — pulls tasks from queue autonomously, reports to queen

### 3.2 Consensus / Anti-Drift Agents
- `quorum-manager` — requires majority agreement before destructive actions (drop DB, force push)
- `raft-manager` — coordinates multi-session builds (multiple Claude Code instances)
- `byzantine-coordinator` — detects a failing/diverging agent, isolates and reassigns its tasks

### 3.3 Domain Specialists (Narrow-Focus Implementers)
- `python-specialist` — FastAPI, Pydantic, asyncio, pytest deep expertise
- `typescript-specialist` — React 19, Tailwind v4, Vite, Vitest deep expertise
- `database-specialist` — PostgreSQL, Qdrant, Neo4j, Redis schema and query expertise
- `solana-specialist` — already exists ✓

### 3.4 Optimization Background Workers
- `benchmark-suite` — runs perf benchmarks after builds
- `performance-monitor` — watches build metrics proactively
- `production-validator` — validates in prod-like environment before marking DONE

### 3.5 Testing Specialists
- `tdd-london-swarm` — parallel TDD agents using London-school mocking
- `mutation-tester` — runs mutation testing to verify test quality (not just coverage)

---

## Phase 4 — Background Daemon Workers

**Mechanism**: nohup + sleep loops (same as Ruflo — simpler than cron).
**File**: `masonry/src/daemon/daemon-manager.sh`

Workers to implement:
| Worker | Interval | What it does |
|--------|----------|-------------|
| `testgaps` | 30min | Scans for files without tests, writes `.autopilot/testgaps.md` |
| `optimize` | 30min | Runs linter + typecheck in background, writes `.autopilot/quality.md` |
| `consolidate` | 2h | Deduplicates Recall build patterns via similarity |
| `deepdive` | 4h | Audits code complexity, dead code, duplication |
| `benchmark` | trigger | Runs perf benchmarks after build completion |

---

## Phase 5 — SPARC Modes in spec.md

**Add `mode` field to task items**:
```markdown
- [ ] **Task 3** [mode:tdd] — implement user auth endpoint
- [ ] **Task 4** [mode:security] — audit auth for OWASP Top 10
- [ ] **Task 5** [mode:devops] — write Dockerfile and compose config
```

**Orchestrator behavior**: reads mode, dispatches right specialist:
- `tdd` → test-writer first (forced), then developer
- `security` → security agent, no code-write permission
- `devops` → devops agent
- `architect` → architect agent, no implementation

---

## Phase 6 — Masonry MCP Expansion

Current: ~12 tools. Target: 50+ tools.

Priority tools to add:
- `masonry_route` — expose 4-layer router as callable tool
- `masonry_pattern_store` / `masonry_pattern_search` — build pattern memory
- `masonry_worker_status` — query daemon worker state
- `masonry_task_assign` — TeammateIdle can call to get next task
- `masonry_agent_health` — per-agent performance metrics
- `masonry_wave_validate` — between-wave state validation for /ultrawork
- `masonry_swarm_init` — spawn a coordinator+worker swarm for a build
- `masonry_consensus_check` — quorum gate before destructive actions

---

## Implementation Order

1. ~~**Phase 1.2** — TeammateIdle hook~~ ✅ DONE
2. ~~**Phase 1.1** — UserPromptSubmit router~~ ✅ DONE
3. ~~**Phase 3.1 (partial)**~~ — `hierarchical-coordinator.md` ✅ DONE
4. ~~**Phase 3.3 (partial)**~~ — `python-specialist`, `typescript-specialist`, `database-specialist`, `production-validator` ✅ DONE
5. ~~**Phase 3.1 (remaining)**~~ — `queen-coordinator`, `worker-specialist`, `adaptive-coordinator`, `quorum-manager`, `tdd-london-swarm`, `mutation-tester` ✅ DONE
6. ~~**Phase 2**~~ — `masonry-build-patterns.js` (PostToolUse extraction) + `masonry-session-start.js` (Recall pattern import) ✅ DONE
7. ~~**Phase 4**~~ — Daemon manager + `worker-testgaps.js`, `worker-optimize.js`, `worker-consolidate.js`, `worker-deepdive.js` ✅ DONE
8. ~~**Phase 5**~~ — SPARC modes in SKILL.md (`[mode:X]` dispatch table) + spec-writer.md annotations ✅ DONE
9. ~~**Hook Safety Audit**~~ — `continueOnError: true` on all non-blocking synchronous hooks ✅ DONE
10. ~~**Phase 6**~~ — MCP expansion (9 new tools: route, pattern_store/search, worker_status, task_assign, agent_health, wave_validate, swarm_init, consensus_check) ✅ DONE
11. ~~**Phase 7 (Ruflo Gap — Tier 1)**~~ — Firecrawl gap analysis + 5 highest-ROI additions ✅ DONE

---

## Phase 7 — Ruflo Gap Closures (Tier 1)

### 7.1 `verification` Agent ✅ DONE
**File**: `~/.claude/agents/verification.md`
**What it does**: Build-time truth enforcement. Runs after each developer task in `/build`. Cross-checks agent claims against git diff, file existence, test results. Emits VERIFICATION_PASS / VERIFICATION_SUSPICIOUS / VERIFICATION_REJECT with structured evidence.
**Ruflo equivalent**: Verification sidecar — Ruflo's #1 differentiator for multi-agent build quality

### 7.2 Effort-Level Routing ✅ DONE
**File**: `masonry/src/hooks/masonry-prompt-router.js`
**What it does**: Classifies every prompt as `low/medium/high/max` effort (Opus 4.6 thinking budget). Injects `[effort:X]` annotation alongside routing hint. Maps to 76% token savings at `medium` vs `high`.
**Ruflo equivalent**: Effort-level dispatch in hook-handler.cjs

### 7.3 `worker-ultralearn.js` ✅ DONE
**File**: `masonry/src/daemon/worker-ultralearn.js`
**Interval**: 60 min
**What it does**: Analyzes last 20 git commits, extracts build patterns (lang/framework/layer), stores new patterns to Recall. Deduplicates before storing. Deeper than per-write extraction — retrospective analysis.
**Ruflo equivalent**: `ultralearn` daemon + `trainPatternsOnComplete`

### 7.4 `worker-map.js` ✅ DONE
**File**: `masonry/src/daemon/worker-map.js`
**Interval**: 30 min
**What it does**: Walks codebase, detects stack (langs, frameworks, test runner, build tool), entry points, key directories, test coverage ratio. Writes `.autopilot/map.md`.
**Ruflo equivalent**: `worker-map.mjs` structure mapper

### 7.5 Context Curator Upgrade ✅ DONE
**File**: `masonry/src/hooks/masonry-session-start.js`
**What it does**: Reads `.autopilot/map.md` at session start and injects a compact 3-line codebase snapshot (stack, entry points, key dirs). Saves Claude from re-discovering project structure each session.
**Ruflo equivalent**: `session-restore` + `auto-memory-hook.mjs import` with codebase context

---

## Phase 8 — Ruflo Gap Closures (Tier 2, Backlog) ✓ COMPLETE

- ✅ `worker-document.js` — auto-docstring extraction + Recall storage (60min interval)
- ✅ `worker-refactor.js` — god files + duplicate blocks + deep nesting → `.autopilot/refactor-candidates.md` (2h interval)
- ✅ `worker-benchmark.js` — test suite timing, baseline tracking, regression detection → `.autopilot/benchmark.md` (4h interval)
- ✅ Agent trust scoring wired into `masonry-session-end.js` — Bayesian update on developer agent score from VERIFICATION_REJECT/PASS markers
- ✅ Daemon auto-start in `masonry-session-start.js` (Ruflo-style) — map + ultralearn auto-start on real projects
- ✅ `masonry_doctor` MCP tool — 6-point health check: Recall, daemons, hooks, registry, training data, output freshness
- ⏭ compact-manual / compact-auto PreCompact split — skipped (existing masonry-pre-compact.js handles both cases correctly)

---

## What We Already Have That Ruflo Doesn't

- `ENABLE_TOOL_SEARCH: "auto:3"` — better than Ruflo's role-based scoping (native Claude Code deferred tools)
- Recall (System-Recall) — production vector+graph memory vs Ruflo's SQLite+HNSW stub
- Masonry 4-layer router — Ruflo's router is static regex; Masonry has semantic + LLM layers
- Campaign/research mode (Trowel) — Ruflo has no research campaign equivalent
- Kiln (BrickLayerHub) — Ruflo has no monitoring UI

## New Findings (Firecrawl Deep Dive, 2026-03-27)

### Parallel Execution Mechanisms (Ruflo's actual power)

**`claude -p` headless instances** — spawn non-interactive Claude for background work:
```bash
result=$(claude -p "Read file.ts, find all TODO comments, return JSON list" --output-format json)
```
Key flags: `--output-format json|text|stream-json`, `--max-turns N`, `--fork-session` (parallel hypothesis exploration from a resumed session).

**`run_in_background: true` in Task calls** — non-blocking agent spawning:
```javascript
// Fire-and-forget parallel agents
Agent({subagent_type: "developer", prompt: "...", run_in_background: true})
Agent({subagent_type: "test-writer", prompt: "...", run_in_background: true})
```
BrickLayer already has `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` but barely uses `run_in_background`.

**Native agent team tools** (already available in BrickLayer):
- `TeamCreate` — create a named team of agents
- `TaskCreate / TaskList / TaskUpdate / TaskGet / TaskOutput` — task queue
- `SendMessage` — send message to a specific named agent
All these are deferred tools — use `ToolSearch` to load them.

### Token Optimizer (30-50% reduction)
Ruflo claims these sources of reduction:
- ReasoningBank retrieval: pull pre-computed reasoning instead of regenerating (-32%)
- Agent Booster edits: WASM patches vs full rewrites (-15%)
- Prompt cache: reuse session context (-10%)
- Optimal batch size: group similar work (-20%)

BrickLayer equivalent: inject cached context from Recall into session start instead of regenerating (-10-15% likely achievable now).

### In-Process MCP Server
Ruflo runs MCP server in the same process as the agent (no IPC overhead). Sub-millisecond tool execution.
BrickLayer Masonry MCP runs out-of-process via stdio. Not worth changing unless perf becomes a bottleneck.

### Hook Safety Audit Needed
Issue #1107 warning: hooks without `continueOnError: true` hard-block every Claude Code session if they crash.
**Action**: Audit all hooks in settings.json — any synchronous (non-async) hook that doesn't `process.exit(0)` on error path must add `continueOnError: true`.

### SPARC 16 Dev Modes (slash commands in Ruflo)
`/architect`, `/code`, `/tdd`, `/debug`, `/security-review`, `/docs-writer`, `/integration`, `/devops`, `/refinement`, `/spec-pseudocode`, `/mcp`, `/ask`, `/reset`, `/deep-research`, `/batch`, `/workflow`
BrickLayer equivalent: add these as mode annotations in spec.md tasks (Phase 5).

### Dual-Mode Collaboration
Ruflo: Claude Code (architecture/security/testing) + OpenAI Codex (implementation/optimization).
Shared memory namespace `collaboration` via `memory_store/memory_search`.
BrickLayer equivalent: already has Recall shared memory — just need the naming convention.

## Firecrawl Fix

Cloud firecrawl-mcp (`npx -y firecrawl-mcp`) is working — use this.
Self-hosted container at 192.168.50.35:3002 and 192.168.50.19:3002 is down (separate issue).
