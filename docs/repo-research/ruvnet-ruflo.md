# Repo Research: ruvnet/ruflo

**Repo**: https://github.com/ruvnet/ruflo
**Researched**: 2026-03-28
**Researcher**: repo-researcher agent
**Purpose**: Identify capability gaps and patterns for BrickLayer 2.0

---

## Verdict Summary

Ruflo is a thin alias package for `claude-flow` v3.5.48 — a production-grade AI agent framework with 5,900+ commits, 259 MCP tools, 60+ agents, and a deeply sophisticated runtime that treats autonomous dev execution as its primary job, not a secondary concern. In dev execution depth, it significantly beats BrickLayer: 16 SPARC modes vs BL's 6 phases, 12 background daemon workers vs BL's zero, a GitHub agent suite with full PR/issue/release automation, and a UserPromptSubmit hook that injects learned patterns into every prompt before Claude processes it. BrickLayer beats Ruflo in research campaign infrastructure (BL's Trowel loop, consensus builder, question bank, quantitative simulation pipeline have no equivalent in Ruflo), and in typed payload routing (Pydantic v2 schemas, four-layer deterministic routing, EMA training pipeline) — Ruflo's routing is simpler and less structured.

---

## File Inventory

### Root level
| File | Category | Description |
|------|----------|-------------|
| `CLAUDE.md` | docs | Master behavioral config — 3-tier routing, swarm protocols, dual-mode orchestration, Agent Teams, 17 hooks, 12 workers, 26 CLI commands |
| `AGENTS.md` | docs | OpenAI Codex CLI integration guide — Codex=EXECUTOR, claude-flow=ORCHESTRATOR, memory search protocol |
| `README.md` | docs | Public readme — package overview, install instructions, quick-start |
| `package.json` | config | npm package definition, `claude-flow` v3.5.48, optional deps: agentdb, agentic-flow, @ruvector/* |
| `tsconfig.json` | config | TypeScript compiler options |
| `vitest.config.ts` | config | Vitest test configuration |
| `eslint.config.mjs` | config | ESLint flat config |
| `CHANGELOG.md` | docs | Version history |
| `LICENSE` | docs | Apache 2.0 |
| `agents/architect.yaml` | agent | Minimal YAML definition — frontmatter only |
| `agents/coder.yaml` | agent | Minimal YAML definition — frontmatter only |
| `agents/reviewer.yaml` | agent | Minimal YAML definition — frontmatter only |
| `agents/security-architect.yaml` | agent | Minimal YAML definition — frontmatter only |
| `agents/tester.yaml` | agent | Minimal YAML definition — frontmatter only |

### `.agents/`
| File | Category | Description |
|------|----------|-------------|
| `config.toml` | config | Codex integration — profiles (dev/safe/ci), security policies, worker scheduling, MCP server definitions |

### `.claude/`
| File | Category | Description |
|------|----------|-------------|
| `settings.json` | config | Live Claude Code settings — 11 hook events wired to handler scripts |
| `statusline.mjs` | code | Terminal status bar — model, tokens, cost, swarm status, session time |

### `.claude/agents/` (agent definitions)
| File | Category | Description |
|------|----------|-------------|
| `sparc/refinement.md` | agent | TDD refinement — Red-Green-Refactor with TypeScript examples, circuit breaker, error hierarchy, coverage thresholds |
| `sparc/architect.md` | agent | System design mode — architecture decisions, component design |
| `sparc/code.md` | agent | Implementation mode — clean code, SOLID principles |
| `sparc/tdd.md` | agent | Test-driven development mode |
| `sparc/debug.md` | agent | Debugging mode — systematic isolation, root cause analysis |
| `sparc/security-review.md` | agent | Security audit mode — OWASP, threat modeling |
| `sparc/docs-writer.md` | agent | Documentation generation mode |
| `sparc/integration.md` | agent | Integration testing and API contract mode |
| `sparc/post-deployment-monitoring.md` | agent | Monitoring and observability mode |
| `sparc/refinement-optimization.md` | agent | Performance refinement and optimization mode |
| `sparc/ask.md` | agent | Interactive clarification mode |
| `sparc/devops.md` | agent | DevOps, CI/CD, infrastructure mode |
| `sparc/tutorial.md` | agent | Tutorial and learning content mode |
| `sparc/supabase-admin.md` | agent | Supabase database administration mode |
| `sparc/spec-pseudocode.md` | agent | Specification and pseudocode planning mode |
| `sparc/mcp.md` | agent | MCP server development mode |
| `development/dev-backend-api.md` | agent | Backend developer with explicit reasoningBank self-learning protocol |
| `development/dev-frontend-ui.md` | agent | Frontend developer with pattern search protocol |
| `development/dev-fullstack.md` | agent | Full-stack developer combining backend + frontend protocols |
| `github/pr-manager.md` | agent | Pull request creation, review, merge automation |
| `github/issue-tracker.md` | agent | GitHub issue creation, triage, labeling |
| `github/release-manager.md` | agent | Release notes, versioning, changelog generation |
| `github/multi-repo-swarm.md` | agent | Coordinate changes across multiple repositories |
| `github/project-board-sync.md` | agent | Sync task state to GitHub Projects |
| `github/workflow-automation.md` | agent | GitHub Actions workflow creation and maintenance |
| `github/code-review-swarm.md` | agent | Multi-agent code review swarm |
| `github/release-swarm.md` | agent | Multi-agent release coordination |
| `github/repo-architect.md` | agent | Repository structure and governance |
| `github/swarm-issue.md` | agent | Swarm-based issue resolution |
| `github/swarm-pr.md` | agent | Swarm-based PR resolution |
| `github/sync-coordinator.md` | agent | Cross-repo sync and dependency management |
| `github/github-modes.md` | agent | Entry point routing to GitHub sub-agents |

### `.claude/commands/`
| File | Category | Description |
|------|----------|-------------|
| `sparc.md` | agent | SPARC command — 16 invocable modes, memory integration via MCP |
| `swarm.md` | agent | Swarm orchestration command |
| `memory.md` | agent | Memory management commands |
| `github.md` | agent | GitHub workflow command entry point |

### `.claude/helpers/`
| File | Category | Description |
|------|----------|-------------|
| `hook-handler.cjs` | hook | Central dispatcher — reads stdin JSON, routes to handler functions |
| `auto-memory-hook.mjs` | hook | AutoMemoryBridge + LearningBridge + MemoryGraph lifecycle wiring |
| `intelligence.cjs` | hook | Pattern matching stub — Jaccard similarity, top-5 context injection |
| `learning-service.mjs` | code | Full HNSW learning service — SQLite persistence, short/long-term promotion, ONNX embeddings |
| `router.cjs` | hook | Request routing (required by hook-handler) |
| `session.cjs` | hook | Session state management (required by hook-handler) |
| `memory.cjs` | hook | Memory operations (required by hook-handler) |

### `.claude/checkpoints/`
| File | Category | Description |
|------|----------|-------------|
| `1767754460.json` | docs | Example checkpoint — tag, file, timestamp, type, branch, diff_summary |

### `v3/`
| File/Dir | Category | Description |
|----------|----------|-------------|
| `swarm.config.ts` | config | TypeScript-typed 15-agent swarm config — domains, phases, topology, load balancing |
| `src/` | code | Core runtime source (large directory — sampled) |
| `mcp/` | code | MCP server implementations (259 tools) |
| `agents/` | agent | Agent definitions for v3 (sampled) |
| `plugins/` | code | Plugin system including healthcare, financial, legal domain plugins |
| `scripts/` | code | Build and utility scripts |
| `@claude-flow/` | code | Sub-packages: claims, codex, tokens, etc. |

### `docs/`
| File/Dir | Category | Description |
|----------|----------|-------------|
| `adr/` | docs | Architectural Decision Records (ADR-001 through ADR-049+) |
| `api/` | docs | API reference documentation |
| `guides/` | docs | User guides |
| `ddd/` | docs | Domain-Driven Design bounded context documentation |

---

## Architecture Overview

Ruflo (claude-flow v3.5.48) is built around four interconnected systems:

**1. Hook Runtime (`.claude/settings.json` + helpers)**
11 hook events cover the complete Claude Code lifecycle: UserPromptSubmit injects learned patterns before every prompt, PreToolUse(Bash) blocks dangerous commands, PostToolUse(Write|Edit|MultiEdit) records edit patterns and metrics, SessionStart/End/Restore manage session state and memory import/export, PreCompact(manual/auto) injects CLAUDE.md guidelines before compaction, TeammateIdle auto-assigns pending work to idle agents, TaskCompleted trains patterns and notifies lead agents. The hook-handler.cjs dispatcher requires all helper modules and routes stdin JSON to the appropriate handler function.

**2. Learning Pyramid (learning-service.mjs + intelligence.cjs)**
A three-layer learning system: short-term patterns in SQLite (24h retention, 500 max), long-term patterns promoted when usage_count >= 3 AND quality >= 0.6 (30d retention, 2000 max), and an intelligence layer (intelligence.cjs) that loads MEMORY.md at session start, performs Jaccard word similarity matching on every user prompt, and injects the top-5 relevant patterns as `[INTELLIGENCE]` context blocks before Claude processes the request. ONNX embeddings via agentic-flow with deterministic hash fallback. Auto-memory bridge syncs patterns to MEMORY.md on Stop.

**3. Swarm Orchestration (v3/swarm.config.ts + CLAUDE.md)**
A 15-agent typed swarm with 6 specialized domains (security, core, integration, quality, performance, deployment), 4 execution phases, hierarchical-mesh topology, and capability-match load balancing. Rafts consensus for coordinator selection, 6-8 agents max per swarm to avoid coordination overhead. Agent Teams experimental feature enables true parallel teammates with mailbox communication via SendMessage, idle reassignment, and inter-agent task delegation.

**4. 3-Tier Model Routing (CLAUDE.md ADR-026)**
Tier 1: Agent Booster WASM (<1ms, $0 cost) for simple transforms (var→const, add-types, add-error-handling, reformat, simplify). Tier 2: Claude Haiku (~500ms) for moderate complexity. Tier 3: Claude Sonnet/Opus for complex reasoning. The WASM tier skips LLM calls entirely for mechanical edits, delivering significant cost and latency reduction.

**5. GitHub Integration Layer**
A full suite of GitHub-native agents covering the complete development lifecycle: pr-manager, issue-tracker, release-manager, multi-repo-swarm, project-board-sync, workflow-automation, code-review-swarm, release-swarm, repo-architect, swarm-issue, swarm-pr, sync-coordinator. None of these are in BrickLayer.

**6. SPARC Mode System**
16 named modes invocable via `mcp__claude-flow__sparc_mode` or CLI, each with specialized methodology: sparc (orchestrator), architect, code, tdd, debug, security-review, docs-writer, integration, post-deployment-monitoring, refinement-optimization, ask, devops, tutorial, supabase-admin, spec-pseudocode, mcp. Persists context via memory namespace per mode.

---

## Agent Catalog

### SPARC Agents (16 modes)

| Agent | File | Purpose | Key Unique Capabilities |
|-------|------|---------|------------------------|
| `sparc` | `.claude/commands/sparc.md` | Orchestrator entry point | Routes to 16 modes, memory integration per mode |
| `refinement` | `sparc/refinement.md` | TDD Red-Green-Refactor | Circuit breaker FSM, error hierarchy (AppError→ValidationError), performance testing with concurrent requests, 80% coverage thresholds |
| `architect` | `sparc/architect.md` | System design | ADR generation, DDD bounded context validation |
| `code` | `sparc/code.md` | Implementation | SOLID principles enforcement, clean code patterns |
| `tdd` | `sparc/tdd.md` | Test-first development | Strict RED-GREEN-REFACTOR cycle |
| `debug` | `sparc/debug.md` | Systematic debugging | Isolation methodology, root cause tracking |
| `security-review` | `sparc/security-review.md` | Security audit | OWASP enforcement, threat modeling |
| `docs-writer` | `sparc/docs-writer.md` | Documentation | Auto-generates API docs, guides |
| `integration` | `sparc/integration.md` | Integration testing | API contract validation |
| `post-deployment-monitoring` | `sparc/post-deployment-monitoring.md` | Observability | SLO tracking, alerting review |
| `refinement-optimization` | `sparc/refinement-optimization.md` | Performance | Profiling, optimization patterns |
| `ask` | `sparc/ask.md` | Clarification | Interactive requirement gathering |
| `devops` | `sparc/devops.md` | Infrastructure | CI/CD pipeline construction |
| `tutorial` | `sparc/tutorial.md` | Learning content | Step-by-step tutorial generation |
| `supabase-admin` | `sparc/supabase-admin.md` | Database admin | Supabase-specific operations |
| `mcp` | `sparc/mcp.md` | MCP development | Build new MCP servers |

### Development Agents

| Agent | File | Purpose | Key Unique Capabilities |
|-------|------|---------|------------------------|
| `dev-backend-api` | `development/dev-backend-api.md` | Backend implementation | Before-task reasoningBank search (minReward=0.85), GNN-enhanced search during (k=10, gnnLayers=3), flashAttention for large schemas, after-task pattern storage with reward/success/critique/latencyMs |
| `dev-frontend-ui` | `development/dev-frontend-ui.md` | Frontend implementation | Same pattern-search/store protocol, UI-specific patterns |
| `dev-fullstack` | `development/dev-fullstack.md` | Full-stack implementation | Combines both protocols, shared memory namespace |

### GitHub Agents (12 agents)

| Agent | File | Purpose | Key Unique Capabilities |
|-------|------|---------|------------------------|
| `pr-manager` | `github/pr-manager.md` | PR lifecycle | Create, review, merge, close PRs via GitHub API |
| `issue-tracker` | `github/issue-tracker.md` | Issue management | Create, triage, label, close issues |
| `release-manager` | `github/release-manager.md` | Release automation | Semver bumping, changelog, GitHub release creation |
| `multi-repo-swarm` | `github/multi-repo-swarm.md` | Cross-repo coordination | Parallel changes across multiple repos |
| `project-board-sync` | `github/project-board-sync.md` | Project boards | Sync task status to GitHub Projects v2 |
| `workflow-automation` | `github/workflow-automation.md` | GitHub Actions | Create, modify, debug CI/CD workflows |
| `code-review-swarm` | `github/code-review-swarm.md` | Multi-agent review | Parallel code review with specialized reviewers |
| `release-swarm` | `github/release-swarm.md` | Release coordination | Multi-agent release execution |
| `repo-architect` | `github/repo-architect.md` | Repo governance | Structure, conventions, branch policies |
| `swarm-issue` | `github/swarm-issue.md` | Issue resolution | Swarm spawned per issue |
| `swarm-pr` | `github/swarm-pr.md` | PR resolution | Swarm spawned per PR |
| `sync-coordinator` | `github/sync-coordinator.md` | Cross-repo sync | Dependency and version sync |

---

## Feature Gap Analysis

| Feature | In Ruflo | In BrickLayer 2.0 | Gap Level | Notes |
|---------|----------|-------------------|-----------|-------|
| **UserPromptSubmit hook** | Yes — fires on every user message, injects top-5 learned patterns as `[INTELLIGENCE]` context blocks before Claude processes the prompt | No — Mortar routing happens after prompt lands, no pre-prompt context injection | HIGH | This is the most impactful single hook BL lacks. Proactive context injection vs reactive routing. |
| **Background daemon workers** | Yes — 12 workers on schedules: testgaps, ultralearn, deepdive, benchmark, document, refactor, map, audit (1h), optimize (30m), consolidate, predict, preload | No — all BL activity is reactive; no autonomous background processes | HIGH | Autonomous code health maintenance without user prompting |
| **TeammateIdle hook** | Yes — auto-assigns pending tasks to idle agent teammates | SubagentStart only — no idle detection or auto-reassignment | HIGH | Enables true parallel agent teams; BL stops at spawn, Ruflo continues coordinating |
| **TaskCompleted hook** | Yes — trains patterns on task completion, notifies lead agent | No equivalent | HIGH | Enables per-task learning loops without requiring explicit invocation |
| **PreCompact context injection** | Yes — two hooks (manual+auto), injects CLAUDE.md + agent list + concurrent execution rules | masonry-pre-compact.js backs up task-ids.json only | HIGH | BL backup is recovery-focused; Ruflo's injection is quality-focused — keeps Claude coherent across compaction |
| **Short-term/long-term pattern promotion** | Yes — SQLite, usage_count >= 3 AND quality >= 0.6 promotes to long-term; dedup at 0.95 similarity | HNSW + hnswlib present, no promotion lifecycle, no usage counting, no quality gating | HIGH | BL has the vector store but not the lifecycle that makes it self-improving |
| **GitHub agent suite** | Yes — 12 agents covering full GitHub lifecycle (PRs, issues, releases, projects, workflows, multi-repo) | git-nerd handles commits/branches; no GitHub API integration | HIGH | BL can't create PRs, file issues, sync project boards, or automate GitHub Actions |
| **16 SPARC modes** | Yes — each mode is a distinct agent with specialized methodology | 6 SPARC phases (/plan → /pseudocode → /architecture → /build → /verify → /fix) — all phases, no sub-mode specialization | HIGH | debug, docs-writer, integration, post-deployment-monitoring, devops, tutorial are completely absent from BL |
| **Session forking** | Yes — `claude -p --resume <id> --fork-session` for parallel approach exploration | No concept of session forking | MEDIUM | Enables A/B implementation comparison; valuable for architecture decisions |
| **3-Tier WASM agent booster** | Yes — Tier 1 WASM (<1ms, $0 cost) for mechanical transforms skips LLM entirely | Deterministic routing layer exists but still routes to Haiku; no LLM-free execution tier | MEDIUM | 30-50% token cost reduction; BL deterministic layer dispatches but still calls an agent |
| **Pattern self-learning in agent prompts** | Yes — dev agents explicitly call reasoningBank.searchPatterns before implementation, store results after with reward/success/critique | No — BL agents don't embed self-learning protocol in their prompts | MEDIUM | Enables compound improvement; each successful task teaches future tasks |
| **ADR auto-generation** | Yes — adr.autoGenerate=true, madr template, creates records on settings changes | No ADR tracking | MEDIUM | Architecture traceability; useful for BL platform decisions |
| **Terminal statusline** | Yes — model, token counts (in/out), cost, swarm status, session time in terminal bar | Kiln desktop app for monitoring; no terminal-integrated status | MEDIUM | Lightweight alternative to Kiln for quick health checks |
| **Checkpoint-on-edit system** | Yes — JSON checkpoints on PostToolUse(Write) with diff_summary, branch, timestamp | masonry-pre-compact backs up task-ids.json; no general checkpoint system | MEDIUM | Enables point-in-time rollback and edit history |
| **Agent Booster edit types** | Yes — var→const, add-types, add-error-handling, reformat, simplify, add-docs | None | MEDIUM | LLM-free micro-edits at scale |
| **Statusline cost tracking** | Yes — real-time cost display per session | No cost tracking | MEDIUM | Visibility into resource usage per session/campaign |
| **DDD bounded context tracking** | Yes — ddd.trackDomains=true, validateBoundedContexts | No | LOW | Overly complex for BL's use case |
| **Claims-based authorization** | Yes — @claude-flow/claims: check, grant, revoke, list | No | LOW | Niche; BL's single-user context doesn't need this |
| **IPFS plugin distribution** | Yes — decentralized plugin registry via Pinata | No | LOW | Not aligned with BL's local-first architecture |
| **doctor health check CLI** | Yes — `claude-flow doctor --fix` checks Node, git, config, daemon, memory DB, API keys, disk | masonry_status and masonry_drift_check partially cover this | LOW | Nice to have; BL has functional equivalent via MCP tools |
| **Dual-mode Claude+Codex** | Yes — Claude (architecture/security/testing) + Codex (implementation/optimization) in parallel | No — Claude-only by design | LOW | Codex integration requires paid API; BL is intentionally Claude-native |
| **Healthcare/financial/legal plugins** | Yes — domain-specific plugins via IPFS | No | LOW | Specialized vertical domains; not relevant to BL's horizontal platform role |
| **Mortar 4-layer routing** | No equivalent — simpler routing | Yes — deterministic → semantic → LLM → fallback with EMA training | BL wins | BL's routing is more sophisticated and measurable |
| **Research campaign infrastructure** | No — dev-focused, no campaign loop | Yes — full Trowel BL 2.0 loop, consensus builder, question bank, wave management | BL wins | Core BL differentiator |
| **Typed payload schemas** | No — untyped hook stdin JSON | Yes — Pydantic v2 QuestionPayload, FindingPayload, RoutingDecision | BL wins | BL's inter-agent contracts are more reliable |
| **Quantitative simulation pipeline** | No | Yes — simulate.py, constants.py, results.tsv, failure boundary mapping | BL wins | No equivalent in Ruflo |
| **Agent prompt optimization loop** | No | Yes — DSPy-style eval → optimize → compare with EMA scoring | BL wins | BL's optimization pipeline has no Ruflo equivalent |
| **Graph/PageRank confidence scoring** | No | Yes — damping=0.85, pattern confidence via PageRank | BL wins | More principled than Ruflo's reward-based scoring |
| **Recall integration** | No | Yes — Qdrant + Neo4j + Ollama at 100.70.195.84:8200 | BL wins | BL has structured long-term memory; Ruflo's is session-scoped |
| **Claims board (human escalation)** | No | Yes — async human escalation via .autopilot/claims.json | BL wins | Human-in-the-loop is more deliberate in BL |

---

## Top 5 Recommendations

### 1. UserPromptSubmit Hook for Proactive Context Injection [4h, CRITICAL]

**What Ruflo does**: Fires on every user message via `UserPromptSubmit` hook event. The intelligence layer loads MEMORY.md patterns, runs Jaccard similarity against the incoming prompt, and injects the top-5 relevant patterns as context blocks (`[INTELLIGENCE] Relevant patterns: * (0.75) pattern summary`) before Claude processes the message. Claude sees both the user's original prompt AND the injected context in a single pass.

**Why BL needs this**: Mortar routing is reactive — it receives the prompt and dispatches after the fact. By the time Mortar decides which agents to spawn, the opportunity to prime Claude with relevant learned context has already passed. A UserPromptSubmit hook runs before any routing, ensuring every interaction benefits from accumulated learning without requiring explicit invocation.

**Implementation sketch**:
1. Add `UserPromptSubmit` event to `masonry/settings.json` hooks block, pointing to `masonry-prompt-inject.js`
2. In `masonry-prompt-inject.js`: call `masonry_recall` MCP tool with the incoming prompt text as query
3. If recall returns results above 0.7 confidence, prepend them as a structured context block to the prompt
4. Write elapsed time and match count to a `.masonry/prompt-inject.log` for telemetry
5. Always `exit 0` — never block the prompt

Cost: The Recall integration already exists at `100.70.195.84:8200`. This is a 4-hour hook file + settings update, no new infrastructure.

---

### 2. Background Daemon Workers for Autonomous Code Health [8h, HIGH]

**What Ruflo does**: 12 persistent workers run on daemon-managed schedules: `audit` every 1h (scans for security issues, outdated deps), `optimize` every 30m (identifies refactor opportunities), `testgaps` on demand (finds untested code paths), `benchmark` hourly (tracks performance metrics), `document` weekly (auto-updates stale docs), `consolidate` every 30m (merges duplicate patterns in learning DB).

**Why BL needs this**: Everything in BL is reactive — an agent runs because a user invoked a skill. No background process monitors code health between sessions. The EMA training pipeline only runs when telemetry is manually collected. The reasoning bank only updates during active campaigns. A daemon layer would make BL self-improving between sessions.

**Implementation sketch**:
1. Create `masonry/src/daemon/` with a Node.js worker manager (`daemon.js`)
2. Add a `masonry_daemon` MCP tool: `start`, `stop`, `status`, `list-workers`
3. Implement three initial workers with the highest value:
   - `masonry-worker-audit.js` — runs `masonry_drift_check` every 2h, writes findings to `.masonry/audit.log`
   - `masonry-worker-testgaps.js` — scans for implementation files lacking test pairs, writes to `.masonry/testgaps.md`
   - `masonry-worker-recall-consolidate.js` — calls Recall API to deduplicate and consolidate memories every 4h
4. Add daemon autoStart to `settings.json` under `daemon` block
5. Surface daemon status in Kiln sidebar

---

### 3. TeammateIdle + TaskCompleted Hooks for Agent Team Coordination [6h, HIGH]

**What Ruflo does**: When an agent finishes its current task and becomes idle, `TeammateIdle` fires and the post-task handler scans a shared pending-tasks queue and auto-assigns the next task to the idle agent without coordinator intervention. When a task completes, `TaskCompleted` fires and stores the task pattern (input, output, reward, success) to the learning service, then notifies the lead agent.

**Why BL needs this**: BL spawns subagents via SubagentStart but has no feedback loop after they finish. The orchestrator (Mortar) has to poll or wait; there's no push notification when work completes. More critically, there's no mechanism for idle agents to self-assign from a work queue — the orchestrator must explicitly dispatch each unit of work.

**Implementation sketch**:
1. Add `TeammateIdle` and `TaskCompleted` to `masonry/settings.json` hooks, pointing to `masonry-agent-coordinator.js`
2. In `masonry-agent-coordinator.js`:
   - On `TeammateIdle`: read `.autopilot/progress.json`, find first `PENDING` task, assign it to the idle agent ID
   - On `TaskCompleted`: read task result from hook payload, store to EMA telemetry (`telemetry.jsonl`), update `progress.json` task status to DONE
3. This eliminates the orchestrator polling pattern in `/build` — agents pull their own work
4. Add a `run_in_background: true` flag support to the agent runner for pure background execution

---

### 4. PreCompact Context Injection for Coherence Preservation [2h, HIGH]

**What Ruflo does**: Two PreCompact hooks (manual and auto) inject a structured context block before Claude's context window is compacted. The injection includes: the full CLAUDE.md guidelines, the current agent list with capabilities, and concurrent execution rules. This ensures Claude doesn't "forget" its operating context after compaction reduces the window.

**What BL does today**: `masonry-pre-compact.js` backs up `task-ids.json` for panel ID survival — this is recovery-focused (preserving state), not quality-focused (preserving behavior).

**Why BL needs this**: After compaction, Claude can drift from its operating instructions — it may stop following Mortar routing, forget which agents are available, or lose the BL/Masonry architecture context. Injecting CLAUDE.md context on compaction prevents this drift.

**Implementation sketch**:
1. Update `masonry-pre-compact.js` to additionally:
   - Read `.claude/CLAUDE.md` (the project CLAUDE.md)
   - Read `masonry/agent_registry.yml` — extract agent names and capabilities
   - Format both as a structured summary block
   - Write to `.masonry/compact-context.md` (auto-included by the PreCompact hook output)
2. The hook output should prepend this block to whatever Claude's compaction sees
3. Total implementation: ~50 lines added to the existing hook file

---

### 5. GitHub Agent Suite — Starting with PR Manager [12h, HIGH]

**What Ruflo does**: 12 GitHub-native agents automate the full development lifecycle beyond local git operations: creating PRs with structured descriptions, filing issues from test failures, automating release notes, syncing work to GitHub Projects, and running GitHub Actions — all via GitHub API calls, not just local git CLI.

**Why BL needs this as Tim's #1 gap** (dev execution): The BL `/build` cycle ends at `git push`. The gap between "code committed locally" and "PR reviewed, merged, issues tracked, release cut" is entirely manual. This is a major dev execution gap. git-nerd handles branches and commits well but stops at the local/remote boundary.

**Implementation sketch** — Phase 1 (pr-manager first):
1. Create `.claude/agents/pr-manager.md` using BL's agent frontmatter format
2. Agent capabilities:
   - Read `.autopilot/spec.md` for PR description content
   - Read `git log --oneline origin/master..HEAD` for commit list
   - Call `gh pr create` with structured title + body from spec
   - Add labels, reviewers from project config
   - Post PR URL to `.autopilot/build.log`
3. Wire to `/build` completion — after all tasks DONE and committed, auto-invoke pr-manager
4. Phase 2: issue-tracker (file issues from verify-report findings), release-manager (cut GitHub releases from CHANGELOG)

---

## Novel Patterns to Incorporate (Future)

**Session forking for A/B implementation**: `claude -p --resume <id> --fork-session` lets you branch a session and try two approaches in parallel, then compare results. BL could implement this as a Masonry skill `/fork` that spawns two parallel /build sessions with different specs and presents a diff.

**3-Tier WASM agent booster**: A tier below Haiku for purely mechanical edits — var→const, add-types, reformat. Could be implemented as a local rule-based transformer (tree-sitter based) that runs before any LLM call. Would meaningfully reduce campaign cost at scale.

**Checkpoint-on-edit with diff_summary**: Every Write/Edit PostToolUse stores a JSON checkpoint with the diff summary. Enables point-in-time rollback without full git history. BL's current recovery story is git reset only.

**Statusline terminal display**: A lightweight status bar (`masonry-statusline.mjs`) showing current model, token counts, session cost, and active agent count. Complement to Kiln rather than replacement — visible without switching to the desktop app.

**ADR auto-generation**: When `masonry/settings.json` or agent registry undergoes significant change, auto-generate an ADR to `docs/adr/`. Uses BL's existing karen agent for the writing task. Provides traceability for platform decisions without manual documentation effort.

**Pattern self-learning in agent system prompts**: Add a standardized block to all BL dev agents (developer, test-writer, code-reviewer) instructing them to: (1) query Recall for relevant patterns before starting, (2) store successful patterns to Recall after completing with quality and task metadata. This doesn't require new infrastructure — Recall already exists. It just requires updating the agent prompts to make the behavior explicit.

**Doctor command for platform health**: A `masonry doctor` CLI command that checks: Node version, required MCP servers reachable, Recall API healthy, Qdrant healthy, Neo4j healthy, agent registry valid YAML, hook files parseable. Surfaces issues proactively rather than waiting for a campaign to fail.

---
