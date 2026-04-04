# Ruflo Gap Analysis — BrickLayer 2.0 Dev Execution

**Date**: 2026-03-27
**Synthesized from**: Tasks 1-4 (orchestration, hooks, memory, build pipeline)
**Focus**: Closing gaps that block autonomous end-to-end app building

---

## Top 10 Gaps by Implementation Impact

Ranked by how much each gap costs BrickLayer on Tim's #1 goal: building apps end-to-end without needing to intervene.

---

### Gap 1 — No Learning Loop (Biggest Multiplier)

**What Ruflo has:** A 5-stage Training Pipeline. Ruflo runs all three execution strategies (conservative, balanced, aggressive) against real tasks, learns via exponential moving average, and locks in the winning strategy per task type. After training, success rate rises from 68.8% to 85.5%. It improves with every build.

**What BrickLayer has:** A fixed orchestration path. Every build is the same — no feedback, no improvement. A task that failed last week fails the same way next week.

**Impact if fixed:** Every build gets incrementally smarter. Patterns that work get reinforced. Patterns that fail get retired. This is the compounding advantage that makes Ruflo look better the longer you use it.

---

### Gap 2 — Two-Stage Build vs Five-Stage SPARC

**What Ruflo has:** Specification → Pseudocode → Architecture → Refinement (TDD) → Completion. Each phase produces a gated artifact that the next phase consumes. Architecture is designed before a line of code is written. Pseudocode makes logic explicit before implementation. Rollback to any prior checkpoint on failure.

**What BrickLayer has:** Plan (spec.md) → Build. No pseudocode phase, no explicit architecture phase, no phase-level rollback. When a task fails, the only option is abort or retry from scratch.

**Impact if fixed:** Fewer downstream rewrites. Architecture decisions made at the right phase instead of discovered mid-implementation. Phase checkpoints mean failure in phase 4 rolls back to phase 3, not back to zero.

---

### Gap 3 — No Memory System with Confidence Decay

**What Ruflo has:** ReasoningBank — hybrid SQLite + HNSW vector index, 2-3ms queries (150x faster than JSON), 11,000+ pre-trained expert patterns. Bayesian confidence scoring: success +20%, failure -15%, time decay -0.005/hr. Session-start pattern injection automatically surfaces relevant patterns before work begins.

**What BrickLayer has:** Patterns stored as JSON in Recall (Qdrant + Neo4j). No confidence scoring, no time decay, no success/failure feedback. Patterns that produce bad outcomes survive indefinitely alongside patterns that work.

**Impact if fixed:** Agent decisions improve over time. Stale patterns decay out. Session-start injection means every build starts with relevant context already loaded — no cold-start problem.

---

### Gap 4 — No Adaptive Execution Strategies

**What Ruflo has:** Three named strategies — conservative (~42ms, thorough, 68.8% first-run success), balanced (~28ms, 85.5% after training), aggressive (~14ms, 79.6%). Ruflo selects the right strategy per task type based on learned history. Simple CRUD endpoints get aggressive; database migrations get conservative.

**What BrickLayer has:** One strategy. Same approach for a one-line config change and a multi-service database migration.

**Impact if fixed:** Faster builds on simple tasks, more thorough handling on risky ones. 3x speed difference between aggressive and conservative — applied correctly this is a significant throughput gain.

---

### Gap 5 — No Agent-Complete Hook (Results Are Batched, Not Streamed)

**What Ruflo has:** `agent-complete` hook fires immediately when any agent finishes. Results are collected and merged in real-time. Combined with stream-JSON chaining (40-60% faster than file handoffs), downstream agents can start consuming output before the upstream agent finishes.

**What BrickLayer has:** Orchestrator waits for worker agents to write to files, then reads results. No real-time streaming. No immediate result collection. Agents finishing in parallel are serialized at the file boundary.

**Impact if fixed:** Faster parallel builds. Early completion of one agent unblocks dependent agents immediately instead of waiting for the whole batch. Stream-JSON chaining is especially valuable for long-running tasks (frontend build → integration test can start while build is still running).

---

### Gap 6 — 7-Point Verification vs Basic Test Pass

**What Ruflo has:** Verification blocks progress if any of 7 checks fail: test coverage ≥80%, unit/integration/E2E all pass, performance benchmarks met, OWASP security compliant, no lint errors, integration works, Docker builds and K8s validates.

**What BrickLayer has:** Tests pass + lint clean. No performance checks, no security audit, no deployment validation.

**Impact if fixed:** Catches more classes of failures before they hit production. Security issues caught at build time instead of discovered post-deploy. Deployment failures caught in CI instead of at the moment Tim tries to push.

---

### Gap 7 — Smart Escalation vs Human-Only Escalation

**What Ruflo has:** Tiered escalation: retry with backoff (1s/2s/4s, max 3) → fallback to different approach → escalate agent to senior agent (coder → architect) → escalate to human + create GitHub issue with full logs.

**What BrickLayer has:** 3-strike rule → stop and ask Tim. No intermediate escalation level, no automatic GitHub issue creation, no senior agent tier.

**Impact if fixed:** Fewer interruptions for Tim. Many failures that currently require human attention (a junior coder hitting an architectural wall) can be resolved by promoting the task to a more capable agent. Tim only gets interrupted for genuinely unresolvable issues.

---

### Gap 8 — No Pre-Task / Post-Task Hooks (No Task-Level Telemetry)

**What Ruflo has:** `pre-task` initializes tracking and creates a task ID before work begins. `post-task` persists metrics and completion status. `perf-start/perf-end` track CPU/memory per task. `pre-edit` creates backups before file modifications.

**What BrickLayer has:** No task-level lifecycle hooks. No performance monitoring. No automatic backups before edits.

**Impact if fixed:** Task duration tracking feeds the training pipeline. Performance data identifies bottlenecks. Pre-edit backups mean a bad write can be reverted without a full git reset — faster recovery from bad tool calls.

---

### Gap 9 — No Knowledge Graph / PageRank Pattern Ranking

**What Ruflo has:** Knowledge graph with PageRank-based pattern ranking. Patterns that are referenced by many other successful patterns rank higher. Patterns cluster by domain. Agent-scoped memory with project/local/user isolation.

**What BrickLayer has:** Flat Recall storage. No graph relationships between patterns. No ranking beyond recency and semantic distance. No scoping — a pattern learned in one project can bleed into another.

**Impact if fixed:** Better pattern retrieval. High-value cross-cutting patterns (error handling, auth flows, API client design) surface reliably. Project-scoped memory prevents patterns from one codebase contaminating a different one.

---

### Gap 10 — No Auto-Memory Bridge (Markdown ↔ Agent DB Sync)

**What Ruflo has:** Bidirectional sync between markdown files and AgentDB. When an agent writes a finding to a markdown file, it's automatically indexed. When AgentDB is queried, results surface in markdown format. No manual export/import step.

**What BrickLayer has:** Recall integration via hooks (masonry-memory-export at stop time). Sync is one-directional and session-end only. Findings written mid-session aren't queryable until the session closes.

**Impact if fixed:** Mid-session memory access. An agent halfway through a long build can query what was learned 3 tasks ago without waiting for the session to end. Particularly valuable for multi-hour builds where early findings are relevant to later decisions.

---

## Quick Wins (1-2 Weeks)

These close significant gaps with minimal architectural change.

**1. Pre-task/post-task hooks** — Wire `masonry-pre-task.js` and `masonry-post-task.js` into the build lifecycle. Pre-task creates a task record with timestamp and estimated complexity. Post-task writes duration, outcome, and agent used. This is pure additive work — no existing behavior changes. Feeds Gap 1 (training pipeline) when that's ready.

**2. Pre-edit backup hook** — `masonry-pre-edit.js` snapshots the file being modified to `.autopilot/backups/{filename}.{timestamp}` before any Write/Edit. Enables instant rollback without a git reset. 50 lines of JS.

**3. Agent-complete hook** — `masonry-agent-complete.js` fires on SubagentStop. Collects the agent's output, writes it to a results cache, and unblocks any dependent tasks immediately. Removes the file-polling delay.

**4. Execution strategy flag** — Add `--strategy conservative|balanced|aggressive` to `/build`. Conservative adds extra verification steps. Aggressive skips redundant checks. Even without the training pipeline to auto-select, letting Tim (or the orchestrator) set strategy per task is immediately useful.

**5. Phase checkpoint commits** — After each major phase (spec approved, architecture written, refinement complete), create a git commit tagged as a phase checkpoint. Rollback to checkpoint instead of full abort. Already fits the existing git-nerd pattern.

---

## Medium Term (2-4 Weeks)

**1. SPARC phases 2-3** — Add explicit Pseudocode and Architecture phases between `/plan` and `/build`. Pseudocode phase produces a `.autopilot/pseudocode.md` for each task. Architecture phase produces `.autopilot/architecture.md` for the overall system design. Both are artifacts that the developer agent reads — reducing blind implementation.

**2. Confidence-scored pattern storage** — Extend Recall integration so every pattern stored via masonry-memory-export includes an initial confidence score (0.7 default). Add a feedback path: when a task completes successfully, increment confidence for patterns it used. When a task fails, decrement. Prune patterns below 0.2. No HNSW required — Qdrant already handles vector retrieval.

**3. 7-point verification** — Extend the verification checklist to include security scan (bandit for Python, eslint-plugin-security for JS), performance benchmark (basic timing against a baseline), and deployment validation (docker build succeeds). The security and deployment checks are mostly wrapping existing tools — 70% of the value for 30% of the work.

**4. Senior agent tier** — Add `architect` and `senior-developer` agents to the escalation chain. When a developer agent DEV_ESCALATEs after 3 attempts, route to senior-developer before hitting diagnose-analyst. Senior developer has a wider system context and can unblock issues that junior agents hit (missing interface, wrong abstraction layer). Reduces the load on diagnose-analyst for non-architectural failures.

---

## Long Term (Architecture Changes)

**1. Training Pipeline** — The highest-leverage long-term investment. After the pre-task/post-task hooks are collecting data, build the 5-stage learning loop: collect outcomes by task type, compute EMA of strategy success rates, select optimal strategy automatically. Initial training data comes from existing masonry-state.json history. After ~50 tasks per task type, the system has enough signal to auto-select strategy. This is what turns BrickLayer from a static orchestrator into a learning system.

**2. ReasoningBank (HNSW vector index)** — Replace JSON-based pattern storage with a hybrid SQLite + HNSW index. 2-3ms retrieval vs the current multi-hundred-ms Qdrant round-trip makes session-start pattern injection feasible (currently too slow to use synchronously at session start). SQLite keeps it local and offline-capable. Qdrant can remain for long-term archival and full-text search.

**3. Knowledge graph with PageRank** — Add graph relationships between Recall patterns. When pattern A is cited by a successful task that also used pattern B, create a weighted edge A→B. PageRank identifies the high-connectivity patterns (the ones that matter). Project-scope isolation prevents cross-contamination. This is a Neo4j schema change (already available in the stack) + a background job.

**4. Adaptive topology selection** — Extend swarm spawning to support hierarchical, mesh, and ring topologies. Current BrickLayer uses a fixed hierarchical model (orchestrator + workers). Mesh is better for peer tasks (multiple agents reviewing the same codebase section). Ring is better for pipeline tasks (output of agent N feeds agent N+1 directly). Auto-select topology based on task dependency graph.

---

## What BrickLayer Already Does Better Than Ruflo

Don't lose these advantages while closing gaps.

**1. Deterministic task execution** — BrickLayer's question bank + progress.json provides explicit, auditable task ordering. Ruflo's task store is flat JSON CRUD — it had no execution engine until v3.5.43 and still had sync bugs in v3.5.42. BrickLayer's deterministic model means a build can be resumed reliably from any task.

**2. Richer hook system** — BrickLayer has 25 hooks vs Ruflo's 12. Conditional matching (`PreToolUse:Write|Edit`), TDD enforcement, design token enforcement, UserPromptSubmit interception, and the 8-hook ordered stop sequence are all more sophisticated than anything in Ruflo. The hook architecture is a genuine strength.

**3. Semantic routing with four layers** — Mortar's four-layer routing (deterministic → semantic → LLM → fallback) handles 60%+ of routing with zero LLM calls. Ruflo's routing is not documented as having anything comparable — it relies on explicit tool calls.

**4. Research campaign depth** — BrickLayer's full campaign apparatus (question bank, wave management, synthesis, findings) has no equivalent in Ruflo. Ruflo is build-focused. BrickLayer does both.

**5. Recall integration (Qdrant + Neo4j)** — BrickLayer's memory backend is already more capable than Ruflo's memory.db. The gap is in the access patterns (confidence scoring, session-start injection) not the underlying storage. The infrastructure is ahead of how it's being used.

**6. Masonry MCP tool surface** — `masonry_route`, `masonry_fleet`, `masonry_recall`, `masonry_wave_validate`, `masonry_task_assign` give the orchestrator fine-grained control that Ruflo's `claude-flow` CLI doesn't match. MCP-native integration beats CLI subprocess orchestration for speed and reliability.

**7. TDD enforcement is wired, not optional** — `masonry-tdd-enforcer.js` fires on every Write/Edit and blocks non-compliant changes. Ruflo's TDD is a methodology that the agent is instructed to follow — but it's not enforced by the system. BrickLayer's hook-level enforcement is a meaningful quality gate.

---

## Summary Recommendation

The single highest-ROI action is implementing the **pre-task/post-task telemetry hooks** (Quick Win #1) now, even though the training pipeline that consumes that data is weeks away. Telemetry data starts accumulating immediately. When the training pipeline is built, it has a history to learn from.

The second-highest-ROI action is the **SPARC phase 2-3 expansion** — adding pseudocode and architecture phases catches the class of failures where a developer agent builds the wrong thing because the design was implicit. This is the most common source of multi-cycle rework in current builds.

The **learning pipeline** (long-term Gap 1) is the architecture change with the highest ceiling. It's what separates a tool that's useful from a tool that gets more useful the more you use it.
