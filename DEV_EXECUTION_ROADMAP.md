# BrickLayer Dev Execution Roadmap
# Goal: Ruflo-level end-to-end app creation capability
# Reference: ruvnet/ruflo studied 2026-03-27
# Language note: Ruflo is TypeScript; BrickLayer agents are Markdown prompts + JS hooks

---

## Phase 1 — Zero-Friction Core (Highest Impact, Build First)

### 1.1 UserPromptSubmit Transparent Router
**File**: `masonry/src/hooks/masonry-prompt-router.js`
**Trigger**: UserPromptSubmit (fires before Claude sees the prompt)
**What it does**:
- Reads prompt from stdin
- Detects intent: coding / research / git / UI / campaign / architecture / debug
- Injects routing suggestion into context: "→ Routing: developer+test-writer+code-reviewer"
- Falls back silently if intent unclear
**Impact**: Every natural-language request auto-routed — no slash commands required.
**Ruflo equivalent**: `hook-handler.cjs route` via UserPromptSubmit

### 1.2 TeammateIdle Auto-Assignment
**File**: `masonry/src/hooks/masonry-teammate-idle.js`
**settings.json addition**:
```json
"TeammateIdle": [{"hooks": [{"type": "command", "command": "node C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-teammate-idle.js", "timeout": 5}]}],
"TaskCompleted": [{"hooks": [{"type": "command", "command": "node C:/Users/trg16/Dev/Bricklayer2.0/masonry/src/hooks/masonry-teammate-idle.js", "timeout": 5}]}]
```
**What it does**: Reads `.autopilot/progress.json`, finds first PENDING task, outputs task prompt for idle agent.
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

1. **Phase 1.2** — TeammateIdle hook (2h, zero risk, huge impact)
2. **Phase 1.1** — UserPromptSubmit router (4h, requires intent detection logic)
3. **Phase 3.1–3.2** — Coordination + consensus agents (write .md files, low effort)
4. **Phase 3.3** — Domain specialist agents (write .md files)
5. **Phase 2** — Pattern memory extraction (requires careful Recall schema design)
6. **Phase 4** — Daemon workers (bash scripts, medium effort)
7. **Phase 5** — SPARC modes (modify /build orchestrator logic)
8. **Phase 6** — MCP expansion (TypeScript, highest effort)

---

## What We Already Have That Ruflo Doesn't

- `ENABLE_TOOL_SEARCH: "auto:3"` — better than Ruflo's role-based scoping (native Claude Code deferred tools)
- Recall (System-Recall) — production vector+graph memory vs Ruflo's SQLite+HNSW stub
- Masonry 4-layer router — Ruflo's router is static regex; Masonry has semantic + LLM layers
- Campaign/research mode (Trowel) — Ruflo has no research campaign equivalent
- Kiln (BrickLayerHub) — Ruflo has no monitoring UI

## Firecrawl Fix

Self-hosted container is down at 192.168.50.35:3002 and 192.168.50.19:3002.
Options:
A) Restart big-bear-firecrawl container on CasaOS: `docker start <container>`
B) Switch to Exa MCP (already connected) for web scraping — covers most use cases
C) Use cloud firecrawl-mcp with FIRECRAWL_API_KEY env var
