# Ruflo Gap Analysis — BrickLayer 2.0

**Created**: 2026-03-28
**Ruflo version analyzed**: v3.5.0 (first production release, formerly Claude-Flow)
**Ruflo repo**: https://github.com/ruvnet/ruflo
**Prior synthesis**: `.autopilot/ruflo-gap-synthesis.md` (2026-03-27) — incorporated and extended here

This document covers every capability Ruflo has that BrickLayer 2.0 lacks, every agent archetype missing from our fleet, and every pattern worth stealing. It supersedes the prior synthesis with deeper coverage of agent categories, tooling, consensus mechanisms, and WASM-acceleration patterns.

---

## How to Read This Document

Sections 1–5 are the comparative analysis. Section 6 is a ranked implementation backlog. Section 7 documents what BrickLayer does better — things Ruflo is trying to match.

A note on scope: Ruflo is primarily a **build platform** (code, test, deploy). BrickLayer is a **research + build** hybrid. Some Ruflo capabilities are irrelevant to BrickLayer's research mission. Those are called out explicitly.

---

## Section 1 — Core Orchestration Patterns BrickLayer Lacks

### 1.1 Three-Tier Model Routing with WASM Tier-0

Ruflo uses four execution tiers for every operation:

| Tier | Handler | Latency | Cost | Trigger |
|------|---------|---------|------|---------|
| 0 | Agent Booster (WASM) | <1ms | $0 | Simple transforms — no LLM at all |
| 1 | Claude Haiku | ~500ms | $0.0002 | Low-complexity (<30% threshold) |
| 2 | Claude Sonnet | 2-3s | $0.003 | Standard tasks |
| 3 | Claude Opus | 5s+ | $0.015 | Architecture, security, deep analysis |

**The WASM Tier-0 is the key insight BrickLayer is missing.** The Agent Booster executes a defined set of code transforms without any LLM call:
- `var-to-const` — ES6 variable hoisting
- `add-types` — TypeScript annotation injection
- `add-error-handling` — try/catch wrapping
- `async-await` — Promise→async conversion
- `add-logging` / `remove-console` — logging toggles

These transforms run in <1ms vs 500ms-5s for LLM equivalents. 352x faster. The principle extends beyond these specific transforms — any deterministic operation that doesn't require reasoning should skip the LLM entirely.

**BrickLayer's current model routing**: Three-tier (haiku/sonnet/opus) per-agent, declared in frontmatter. Correct but missing the zero-cost WASM tier for fully deterministic sub-operations.

**Gap**: No mechanism to execute deterministic code transforms without an LLM call. Every operation, no matter how trivial, goes through an agent.

### 1.2 Self-Learning Neural Architecture (SONA)

Ruflo implements a 5-stage learning pipeline called SONA (Self-Optimizing Neural Architecture):

```
RETRIEVE → JUDGE → DISTILL → CONSOLIDATE → ROUTE (loops)
```

Each build execution feeds the pipeline:
1. **RETRIEVE** — pull relevant patterns from ReasoningBank by task type
2. **JUDGE** — score the current execution against past outcomes
3. **DISTILL** — extract transferable patterns from the current execution
4. **CONSOLIDATE** — update the ReasoningBank with confidence scoring
5. **ROUTE** — update routing weights for future similar tasks

This implements adaptive execution strategy selection: after enough runs, the system auto-selects between conservative (42ms, 68.8% first-run success), balanced (28ms, 85.5% post-training), and aggressive (14ms, 79.6%) strategies per task type.

**BrickLayer's current state**: DSPy optimization pipeline for agent prompts (offline batch). No online learning that improves routing decisions during live builds. Every build uses the same strategy.

**Gap**: No online learning loop. The DEV_EXECUTION_ROADMAP.md documents this as the #1 long-term gap (Gap 1) and outlines the EMA-based training pipeline. The path is planned but not built.

### 1.3 Byzantine Fault Tolerant Consensus (Multiple Mechanisms)

Ruflo implements four distinct consensus mechanisms for multi-agent decision-making:

| Mechanism | Protocol | Tolerance | Use Case |
|-----------|----------|-----------|----------|
| Raft | Leader-based | Single leader failure | Authoritative state, hive-mind operations |
| PBFT | Byzantine | Up to 1/3 faulty agents | Security-critical operations |
| Gossip | Eventual consistency | High network latency | Speed-priority coordination |
| CRDT | Conflict-free | Network partition | Distributed knowledge merge |

**Weighted voting**: In Ruflo's Hive Mind, queen agent votes count 3x over worker votes. Majority consensus + leader tiebreaker.

**BrickLayer's current state**: No consensus mechanism. Orchestrator (Mortar/Trowel) is authoritative and makes all routing decisions alone. No mechanism to resolve conflicting agent outputs beyond asking Tim.

**Gap**: When multiple agents produce conflicting findings or code reviews, there is no structured resolution protocol. The first agent's output wins by default, or Tim is asked to adjudicate. A lightweight majority-vote mechanism for code review conflicts (code-reviewer + peer-reviewer + design-reviewer voting on APPROVED/BLOCKED) would be immediately useful.

### 1.4 Circuit Breaker Pattern for Failed Operations

Ruflo's retry/recovery logic:
```
Retry: max 3 attempts, exponential backoff (1s → 2s → 4s)
Fallback: route to backup processor in degraded mode
Circuit Breaker: 5 failures within 60s → open circuit (30s)
               → probe (1 attempt) → close if successful
```

The circuit breaker prevents cascading failures: if a tool or external service is failing consistently, Ruflo stops calling it for 30 seconds and uses fallback mode rather than hammering it.

**BrickLayer's current state**: 3-strike rule stops the build. No circuit breaker, no fallback mode, no degraded-mode operation.

**Gap**: A failing MCP tool or external service (Recall, GitHub, Exa) takes down the whole build. No graceful degradation.

### 1.5 Stream-JSON Chaining (Agent Output Piping)

Ruflo supports real-time output piping between agents without intermediate file storage. Rather than:
```
Agent A → writes file → Agent B reads file → processes
```
Ruflo does:
```
Agent A output stream → directly piped to Agent B input
```
This eliminates file I/O overhead and allows downstream agents to start processing before upstream agents finish (40-60% faster than file handoffs for long-running tasks).

**BrickLayer's current state**: All inter-agent communication goes through files (findings/*.md, progress.json, build.log). Agents wait for file writes to complete before downstream agents can start.

**Gap**: No streaming inter-agent communication. This is particularly costly for build chains: frontend compiler output → integration test → deployment can start downstream stages while upstream stages are still running.

### 1.6 Dual-Mode Platform Integration (Claude + Codex)

Ruflo explicitly coordinates two AI platforms in parallel:
- Claude Code: architecture, security review, reasoning
- Codex: implementation, bulk transformations, performance optimization

Shared memory namespace (`collaboration`) allows findings to transfer bidirectionally. The rationale: cross-validation between two platforms catches more errors than a single platform catching its own mistakes.

**BrickLayer's current state**: Claude Code only. No multi-platform coordination.

**Gap**: Low priority for BrickLayer's current use case. Claude Code is already BrickLayer's primary platform, and the `/masonry-team` skill handles multi-instance coordination. However, Codex integration for bulk code transforms (complementing Agent Booster patterns) is worth revisiting when bandwidth allows.

### 1.7 Adaptive Topology Selection

Ruflo selects swarm topology based on task dependency structure:

| Task Pattern | Recommended Topology |
|-------------|---------------------|
| All tasks independent | Hierarchical (coordinator + parallel workers) |
| Shared code review needed | Mesh (peer-to-peer, any agent reviews any) |
| Linear chain (N→N+1) | Ring (output piped directly to next agent) |
| Hub-and-spoke validation | Star (central coordinator, agents report back) |
| Mixed | Hybrid |

**BrickLayer's current state**: Fixed hierarchical topology (Mortar/Trowel orchestrator + workers). DEV_EXECUTION_ROADMAP.md Phase 3.4 documents this as a planned gap.

**Gap**: Mesh topology (particularly useful for peer code review between multiple specialist agents) is never used. Ring topology (build pipeline where output feeds directly to next stage) is never used.

---

## Section 2 — Agent Archetypes BrickLayer Is Missing

### Ruflo Agent Taxonomy (64 total, 12 categories)

| Category | Count | Key Agents |
|----------|-------|-----------|
| Core Development | 5 | Coder, Reviewer, Tester, Planner, Researcher |
| Swarm Coordination | 3 | Hierarchical, Mesh, Adaptive coordinators |
| Hive-Mind Intelligence | 3 | Collective intelligence, consensus builder, memory manager |
| Consensus & Distributed | 7 | Byzantine, Raft, Gossip, CRDT controllers, security manager |
| Performance & Optimization | 5 | Load balancer, monitor, topology optimizer |
| GitHub & Repository | 12 | PR manager, code review swarm, issue tracker, release manager |
| SPARC Methodology | 4 | Specification, pseudocode, architecture, refinement |
| Specialized Development | 8 | Backend, mobile, ML developer, CI/CD engineer |
| Testing & Validation | 2 | TDD London school, production validator |
| Templates & Orchestration | 7 | Automation coordinator, memory coordinator |
| Analysis & Architecture | 2 | Code quality analyzer, system designer |
| Specialized Domains | 3 | ML model developer, DevOps engineer, API documenter |

### BrickLayer Agent Inventory

**Global agents (~/.claude/agents/)**:
adaptive-coordinator, agent-auditor, architect, bl-verifier, database-specialist, developer, devops, e2e, economizer, frontier-analyst, health-monitor, hierarchical-coordinator, hypothesis-generator, hypothesis-generator-bl2, karen, mortar, mutation-tester, overseer, peer-reviewer, production-validator, prompt-engineer, python-specialist, queen-coordinator, quorum-manager, refactorer, retrospective, rust-analyst, rust-developer, security, self-host, senior-developer, solana-specialist, spec-writer, spreadsheet-wizard, tdd-london-swarm, test-writer, tools-manifest, trowel, typescript-specialist, uiux-master, verification, worker-specialist

**Project agents (.claude/agents/)**:
agent-auditor, benchmark-engineer, bug-catcher, cascade-analyst, code-reviewer, competitive-analyst, compliance-auditor, design-reviewer, diagnose-analyst, evolve-optimizer, fix-implementer, forge-check, frontier-analyst, git-nerd, health-monitor, hypothesis-generator, hypothesis-generator-bl2, kiln-engineer, mcp-advisor, mortar, overseer, peer-reviewer, planner, pointer, quantitative-analyst, question-designer-bl2, regulatory-researcher, research-analyst, retrospective, rough-in, senior-developer, skill-forge, synthesizer, synthesizer-bl2, trowel

### Missing Agent Archetypes

**1. Pseudocode Agent**
Ruflo's SPARC Phase 2 produces a `pseudocode.md` before any code is written. The pseudocode agent writes per-task logic in plain English (flow + edge cases, no syntax). This is fed to the developer agent as an explicit specification of what to build.

BrickLayer has no pseudocode phase. Developers receive `spec.md` only. The spec describes **what** to build; pseudocode describes **how** to build it. This is the most common source of rework — developer agents implementing correct code for the wrong algorithm.

**2. Architecture Phase Agent**
Ruflo's SPARC Phase 3 produces an `architecture.md` covering: component boundaries, interface contracts, data flows, explicit out-of-scope list. The architecture agent differs from the spec-writer and the architect agent — it is narrowly scoped to translate the spec into an architectural decision document that the developer can mechanically follow.

BrickLayer's architect agent is general-purpose and invoked on demand. There is no systematic architecture phase between spec approval and build start.

**3. Token Optimizer Agent (WASM Wrapper)**
The pattern: detect simple transforms, dispatch to WASM instead of LLM, return result in <1ms. BrickLayer could implement a subset of this using Python AST transforms (add type hints, convert f-strings, enforce import order) without any LLM call. The agent becomes a dispatcher: "does this match a known deterministic transform? if yes, apply it; if no, pass to developer."

**4. Performance Optimizer Agent**
Ruflo has a dedicated performance optimization specialist that profiles code, identifies bottlenecks, and applies optimizations. Distinct from refactorer (which is structure-focused) and developer (which is feature-focused).

BrickLayer has no performance-focused agent. Performance issues discovered during verification fall back to the developer agent, which is not trained for performance work.

**5. ML Developer Agent**
Ruflo has an ML model developer agent for neural architecture work, training configuration, and model evaluation. BrickLayer's Python specialist and research-analyst cover adjacent territory, but there is no dedicated ML/model development specialist.

**6. Mobile Developer Agent**
Ruflo includes a mobile development specialist. BrickLayer has Kotlin capability via developer/rust-developer but no dedicated mobile agent with Android/iOS-specific patterns. Relevant for JellyStream.

**7. API Documentation Agent**
Ruflo has a dedicated API documentation specialist that generates OpenAPI specs, README documentation, and endpoint documentation from code. BrickLayer's karen agent handles documentation but is focused on project-level docs (CHANGELOG, ROADMAP, ARCHITECTURE), not API-level documentation generation.

**8. Release Manager Agent**
Ruflo has a release manager that coordinates versioning, changelog generation, GitHub release creation, and deployment gating. BrickLayer's git-nerd handles commits and PRs but not the full release lifecycle (semver bump, release notes, GitHub Release artifact creation, deployment gate).

**9. Consensus Builder Agent**
When multiple BrickLayer agents produce conflicting verdicts (code-reviewer says APPROVED, peer-reviewer says CONCERNS), there is no structured resolution. A consensus builder would collect all agent outputs, apply voting logic, and produce a final verdict.

**10. Memory Coordinator Agent**
Ruflo has an agent dedicated to managing shared memory state across a swarm — writing to shared namespaces, detecting conflicts, compressing old entries, and managing TTL. BrickLayer's memory coordination happens in hooks (masonry-observe.js, masonry-memory-export at stop time). There is no agent-level memory coordinator that can be invoked mid-build to resolve memory state issues.

**11. Load Balancer Agent**
Ruflo explicitly balances work across available agents based on current load. BrickLayer dispatches tasks based on task type and agent tier, but has no mechanism to detect that a specialist is overloaded and reroute to an available generalist.

**12. CI/CD Engineer Agent**
Ruflo has a CI/CD specialist for pipeline configuration, GitHub Actions, deployment scripting. BrickLayer's devops agent covers adjacent territory but is primarily focused on Docker and infrastructure rather than CI/CD pipeline engineering.

---

## Section 3 — Workflow Patterns

### 3.1 SPARC vs Two-Stage Build

**Ruflo's SPARC (5 phases)**:
```
Phase 1: Specification  → spec.md (current, requirements, success criteria)
Phase 2: Pseudocode     → pseudocode.md (per-task logic in plain English)
Phase 3: Architecture   → architecture.md (components, interfaces, data flow, out-of-scope)
Phase 4: Refinement     → TDD cycle (RED-GREEN-REFACTOR, test-first)
Phase 5: Completion     → Integration, verification, deployment gate
```
Each phase is gated. Failure in Phase 4 rolls back to Phase 3 checkpoint, not Phase 1. Code is never written without an explicit architecture document.

**BrickLayer's build pipeline**:
```
/plan  → spec.md (Phase 1 equivalent)
/build → TDD cycle (Phase 4 equivalent, skipping 2 and 3)
/verify → verification
/fix   → targeted fixes
```

**Missing**: Phases 2 (pseudocode) and 3 (architecture). The DEV_EXECUTION_ROADMAP.md documents this as Gap 2 with a concrete implementation plan. Status: planned, not built.

### 3.2 Declarative DAG Dependencies

Ruflo's task system declares dependencies as a directed acyclic graph:
```json
{
  "tasks": [
    {"id": "analyze", "agent": "analyzer"},
    {"id": "design", "agent": "architect", "depends": ["analyze"]},
    {"id": "implement", "agent": "coder", "depends": ["design"]},
    {"id": "test", "agent": "tester", "depends": ["implement"]},
    {"id": "review", "agent": "reviewer", "depends": ["implement"]},
    {"id": "document", "agent": "documenter", "depends": ["implement"]}
  ]
}
```
"test" and "review" and "document" all depend on "implement" — they run in parallel automatically. The DAG enables maximum parallelism within the constraint graph.

**BrickLayer's current state**: `progress.json` has a task list with `depends_on: [N]` field defined in schema but not yet active. The DEV_EXECUTION_ROADMAP.md Phase 1.3 documents adding dependency signaling. Status: schema designed, not wired.

### 3.3 Conditional Deployment Gates

Ruflo's verification gates use conditional expressions:
```
staging_gate:    tests.passed && coverage > 80
production_gate: staging.passed && response_time < 200ms && security.score > 0.9
```
These gates are evaluated before deployment proceeds. If a gate fails, the system stops and reports which condition failed, not just that the gate failed.

**BrickLayer's current state**: Verification is a pass/fail report written by the verification agent. No conditional gate logic that auto-blocks deployment based on specific metric thresholds.

### 3.4 Checkpoint Frequency and Rollback Granularity

Ruflo creates checkpoints after each stage: "after-each-stage" frequency with 7-day retention and automatic restoration on failure. The checkpoint includes full agent state, not just file state.

**BrickLayer's current state**: Git commits after each task (via git-nerd). No explicit phase-level checkpoints, no agent state snapshots, 7-day retention not enforced.

DEV_EXECUTION_ROADMAP.md Phase 1.5 documents phase checkpoint commits as a quick win. Status: planned.

### 3.5 Research Swarm Topology

Ruflo defines a dedicated research swarm using mesh topology with 6 specialized agents:
- Web researcher
- Academic specialist
- Data analyst
- Pattern analyzer
- Source validator
- Report writer

These work in parallel, cross-validating each other's sources. The source validator explicitly checks the credibility, recency, and authority of sources that the web researcher and academic specialist find.

**BrickLayer's current state**: Research campaigns use Trowel + specialist agents (research-analyst, competitive-analyst, regulatory-researcher) but these run sequentially per question, not as a concurrent swarm for a single question. No cross-validation between researchers on a single finding.

**Gap**: High-confidence research findings require source cross-validation. BrickLayer currently produces single-source findings. A parallel research swarm on high-stakes questions would produce stronger evidence.

### 3.6 Human Claims System

Ruflo implements a "claims" system for human-agent handoffs: when an agent determines that human input is required, it writes a structured claim to a claims board rather than stopping the build. The human can review the board asynchronously, resolve claims, and the build continues.

**BrickLayer's current state**: When Tim is needed, the build stops. There is no async claims board. Tim must be present at the moment the escalation fires.

**Gap**: The claims pattern allows longer autonomous runs. Instead of stopping a 12-hour overnight build to ask Tim one question, the build writes the question to a claims board, continues with independent tasks, and Tim resolves the claim when available. The build engine checks claim resolution before attempting blocked tasks.

---

## Section 4 — Tooling Ruflo Has That BrickLayer Lacks

### 4.1 AgentDB — 8-Controller Distributed State System

Ruflo's AgentDB v3 has 8 specialized controllers:

| Controller | Purpose |
|------------|---------|
| HierarchicalMemory | Memory organized by scope (project/local/user) |
| MemoryConsolidation | Merges related memories, removes redundancy |
| SemanticRouter | Routes queries to appropriate memory partition |
| GNNService | Graph Neural Network for pattern relationships |
| RVFOptimizer | RuVector Format compression for storage efficiency |
| MutationGuard | Cryptographic proof-verified writes (HMAC signed) |
| AttestationLog | Audit trail for all memory writes |
| GuardedVectorBackend | Secure vector operations with access control |

**BrickLayer's current state**: Recall (Qdrant + Neo4j + FastAPI) at `100.70.195.84:8200`. Comprehensive backend but all accessed via HTTP. No local tier. No mutation auditing. No cryptographic proof of memory integrity.

**Most useful gaps to close**:
- **MemoryConsolidation**: BrickLayer accumulates memories without merging similar ones. Over time, Recall fills with redundant variations of the same pattern.
- **MutationGuard**: Audit trail for who wrote what memory when — valuable for debugging which agent introduced a bad pattern.
- **HierarchicalMemory**: Project-scoped vs global memory separation. Currently, memories from ADBP campaign can surface during Recall queries on a different project.

### 4.2 ReasoningBank (Local HNSW Vector Index)

Ruflo's ReasoningBank is a hybrid SQLite (metadata) + HNSW (vectors) local index. Key characteristics:
- 2-3ms retrieval vs 150-200ms for remote Qdrant queries
- hnswlib for vector operations (150x-12,500x faster than naive search)
- Pre-trained with 11,000+ expert patterns
- Confidence-scored with Bayesian update: success +20% (1-c), failure -15% (c)
- Time decay: -0.005/hr since last use
- Prune threshold: confidence < 0.2

**BrickLayer's current state**: Recall (Qdrant) at remote address. 150-200ms round-trip latency makes synchronous session-start injection infeasible. DEV_EXECUTION_ROADMAP.md Phase 3.2 documents the ReasoningBank as a long-term goal.

**Gap**: Session-start pattern injection (surfacing relevant patterns before work begins) requires <10ms retrieval. The current remote Qdrant latency is 15-20x too slow for synchronous use. This forces the cold-start problem on every session.

### 4.3 Statusline Intelligence (Real-Time Build HUD)

Ruflo's statusline tracks and displays:
- Current context usage percentage
- Token usage and cost estimate
- Active agent count and states
- Task completion progress
- Benchmark regression warnings (if >20% slower than baseline)
- Memory optimization triggers (if approaching limits)

**BrickLayer's current state**: `masonry-statusline.js` provides a rich HUD with campaign progress, verdicts, context %, Recall memory count, agent count, and git branch. This is a genuine strength — arguably better than Ruflo's statusline in campaign-mode display.

**Gap**: Build-mode statusline is less rich than campaign-mode. Cost tracking and token budget awareness are missing from build mode specifically.

### 4.4 Doctor Tool (System Health Check)

Ruflo's `doctor` command runs a comprehensive system health check:
- MCP server connectivity
- Memory system health
- Hook registration verification
- Background worker status
- Provider connectivity (Claude, Ollama, etc.)
- Permission checks

**BrickLayer's current state**: `masonry doctor` tool exists via MCP (`masonry_doctor`). Hook-level health is not aggregated into a single diagnostic command.

**Gap**: Partial. BrickLayer has some diagnostic capability but no unified "everything is working" health check equivalent to Ruflo's doctor.

### 4.5 Background Worker Daemon (12 Persistent Workers)

Ruflo runs 12 background workers continuously:
- Memory indexing (continuous Qdrant updates)
- Pattern analysis (identify emerging patterns)
- Drift detection (monitor agent output quality)
- Consensus maintenance (keep quorum state consistent)
- Performance profiling (collect baseline metrics)
- Checkpoint management (prune old checkpoints)
- Training pipeline (update EMA weights from recent outcomes)

**BrickLayer's current state**: Masonry daemon exists (`masonry-daemon-manager.js`) but is minimal — manages periodic agent scoring and state sync. No continuous pattern analysis, no background training pipeline updates.

**Gap**: The training pipeline requires continuous background operation. Without a background worker, training happens in batch at session end rather than continuously.

### 4.6 26-Command CLI with 140+ Subcommands

Ruflo's `claude-flow` CLI provides:

| Domain | Key Commands |
|--------|-------------|
| Swarm | `swarm init --topology mesh --max-agents 8 --consensus raft` |
| Agent | `agent spawn --type coder --name "backend-dev"` |
| Memory | `memory store --key 'auth-patterns' --namespace project` |
| Hive-Mind | `hive-mind spawn --queen-type strategic --workers 5` |
| Neural | `neural train --model reinforcement --algorithm q-learning` |
| Session | `session restore --checkpoint latest` |
| Daemon | `daemon start --workers 12 --port 3001` |
| Claims | `claims list --status pending` |
| Performance | `performance benchmark --compare-baseline` |
| Security | `security scan --owasp-top10 --auto-fix` |

**BrickLayer's current state**: Masonry MCP tools (20+ tools) accessed via `masonry_*` functions from Claude Code. No standalone CLI. Skills (`/build`, `/plan`, `/masonry-run`) are the human-facing entry points.

**Gap**: Ruflo's CLI enables scripted orchestration (run swarm from GitHub Actions, from cron, from shell scripts) independent of Claude Code. BrickLayer's skills only work inside a Claude Code session. The `bl-parallel.ps1` script partially addresses this but is not a full CLI equivalent.

### 4.7 IPFS Decentralized Storage Option

Ruflo supports IPFS as a storage backend for distributing agent findings across multiple nodes. Useful for multi-machine setups where Claude Code runs on casaclaude and proxyclaude simultaneously.

**BrickLayer's current state**: Single Recall instance at `100.70.195.84`. No distributed storage. Running builds on two machines produces findings that only exist on the machine that ran them.

**Gap**: Low priority for single-machine builds. Medium priority when casaclaude + proxyclaude need to coordinate on the same campaign.

---

## Section 5 — Quality Gates Ruflo Enforces

### 5.1 AIDefence Security Screening (Input Layer)

Ruflo screens every incoming request through AIDefence before routing:
- Prompt injection detection
- Input validation and sanitization
- Path traversal prevention
- Command injection protection
- PII detection and masking
- Multi-agent security consensus

**BrickLayer's current state**: `masonry-approver.js` auto-approves writes in build mode. No input screening. `masonry/src/hooks/masonry-lint-check.js` checks output quality. Security review is invoked explicitly via `/masonry-security-review`.

**Gap**: No systematic prompt injection detection. In build mode, the auto-approver is intentionally permissive — which means a malformed task definition could write dangerous code without any gate.

### 5.2 7-Point Verification Checklist

Ruflo's verification blocks progress if any of 7 checks fail (in fail-fast order):
1. Test coverage >= 80%
2. Unit tests pass
3. Integration tests pass
4. E2E tests pass (if test files exist)
5. Security scan (bandit/eslint-plugin-security)
6. Performance baseline (warn if >20% slower)
7. Docker build (if Dockerfile present)

**BrickLayer's current state**: Tests pass + lint clean. DEV_EXECUTION_ROADMAP.md Phase 2.3 documents adding checks 5-7 to verification. Status: planned.

**Gap**: Security scan, performance baseline, and Docker build validation are not part of the automated verification path.

### 5.3 Coverage-Aware Agent Routing

Ruflo's routing considers agent specialization when assigning tasks: if a backend task is available and a `backend-developer` agent is idle, it gets priority over a generic `developer` agent. The router tracks which agent types have handled similar tasks successfully and biases toward specialists.

**BrickLayer's current state**: Mortar routes by agent capability declared in registry YAML. No coverage-aware selection that biases toward the specialist with the highest success rate on this task type.

**Gap**: The routing_log.jsonl (being built in Phase 16.05b) will eventually enable this. The data collection is happening; the routing bias update is not yet wired.

### 5.4 Cryptographic Memory Integrity (MutationGuard)

Ruflo's MutationGuard verifies every memory write with a cryptographic proof. Any memory read can be verified against its write-time HMAC. This prevents memory poisoning — where a bad agent writes incorrect patterns that corrupt future decisions.

**BrickLayer's current state**: Recall stores memories via HTTP API with no write-time verification. A misbehaving agent can write incorrect memories with no audit trail.

**Gap**: No memory integrity checking. Low priority unless BrickLayer scales to untrusted agent execution environments.

### 5.5 Performance Regression Baseline

Ruflo benchmarks each build against a stored baseline and warns if any component is >20% slower than the baseline. The baseline is stored at the checkpoint level, not just the commit level.

**BrickLayer's current state**: Introspection tracer (`per-step trace {thought, tool_call, result, tokens, latency}`) collects latency data per agent step. No aggregation into a performance baseline, no regression detection.

**Gap**: The raw data exists (introspection tracer). The aggregation and regression detection pipeline does not exist.

---

## Section 6 — Implementation Backlog (Ranked by Impact)

### Tier 1 — Quick Wins (1-2 weeks, additive only)

**P1.1 — Pre-task / Post-task Telemetry Hooks**
Start the data clock for the training pipeline. Every build after this hook accumulates signal.
- `masonry/src/hooks/masonry-pre-task.js` — write task record to `.autopilot/telemetry.jsonl`
- `masonry/src/hooks/masonry-post-task.js` — append duration_ms, agent, success/fail
- Schema: `{"task_id": "t-001", "phase": "pre|post", "timestamp": "ISO", "type": "frontend|backend|infra", "complexity": "low|medium|high", "duration_ms": 4200, "success": true}`
- Register in `masonry/.claude/settings.json` on PreToolUse/PostToolUse(Agent)

**P1.2 — Pre-edit Backup Hook**
Instant single-file rollback without git reset.
- `masonry/src/hooks/masonry-pre-edit.js` — snapshot to `.autopilot/backups/{path}/{filename}.{ISO}`
- Only fires when `.autopilot/mode` == "build" or "fix"
- Cleanup: prune backups >7 days on Stop event

**P1.3 — Agent-Complete Dependency Signaling**
Unblock dependent tasks immediately when upstream completes.
- `masonry/src/hooks/masonry-agent-complete.js` — SubagentStop → write result to `.autopilot/results/{agent_id}.json`
- Add `depends_on: [N]` field activation in progress.json schema (field exists, needs wiring)
- Wake dependent tasks on completion

**P1.4 — Execution Strategy Flag**
`/build --strategy conservative|balanced|aggressive` with per-strategy behavior.
- conservative: extra verification, security scan, slower
- balanced: default path
- aggressive: skip redundant checks, maximize parallelism
- Persisted to `.autopilot/strategy` for the duration of the build

**P1.5 — Phase Checkpoint Commits (SPARC Gate)**
Tagged git commits at phase boundaries (spec → architecture → refinement → completion).
- Tag format: `phase/spec`, `phase/architecture`, `phase/refinement`, `phase/completion`
- Wired into git-nerd's `--phase-checkpoint` flag
- Rollback to checkpoint instead of full abort on phase failure

**P1.6 — Claims Board (Async Human Escalation)**
Replace build-stopping human escalation with an async claims file.
- `.autopilot/claims.json` — list of pending questions with task context
- Build continues on independent tasks while claims are pending
- Blocked tasks check claim resolution before attempting
- `masonry-statusline.js` shows pending claim count in HUD

### Tier 2 — Medium Term (2-4 weeks)

**P2.1 — SPARC Pseudocode Phase**
The highest single-item reduction in multi-cycle developer rework.
- spec-writer produces `pseudocode.md` after spec approval, before build
- Pseudocode = per-task logic in plain English: flow + edge cases + explicit failure modes
- developer agent receives pseudocode + spec for each task
- `/pseudocode` skill: explicitly invoke pseudocode phase on demand

**P2.2 — SPARC Architecture Phase**
- `architecture.md` = component diagram, interface contracts, data flow, out-of-scope list
- Produced by architect agent after pseudocode, before build
- architecture.md is injected into every developer task prompt
- `/architecture` skill: explicitly invoke architecture phase on demand

**P2.3 — Confidence-Scored Pattern Storage**
Bayesian confidence updates in Recall, decay, and pruning.
- Initial confidence: 0.7 for all new patterns
- Success update: `confidence += 0.20 * (1 - confidence)`
- Failure update: `confidence -= 0.15 * confidence`
- Time decay: -0.005/hr since last use
- Prune threshold: confidence < 0.2 → delete pattern
- `masonry_pattern_decay` MCP tool to trigger pruning

**P2.4 — 7-Point Verification Checklist**
Extend verification to include security, performance, and deployment checks.
- Check 5: `bandit -r src/ -q` (Python) or `eslint --plugin security` (JS)
- Check 6: performance timing vs stored baseline, warn if >20% regression
- Check 7: `docker build .` — only if Dockerfile present
- `masonry_verify_7point` MCP tool with structured pass/fail per check

**P2.5 — Senior Agent Escalation Tier**
Replace direct Tim escalation with a capable intermediate agent.
- Escalation chain: `developer ×3 → senior-developer → architect → diagnose-analyst → human + GitHub issue`
- senior-developer: wider system context, reads all related files, can propose refactors
- Auto-create GitHub issue with full task log on human escalation (masonry_github_issue tool)

**P2.6 — Lightweight Consensus for Code Review**
Majority-vote resolution when reviewers conflict.
- When code-reviewer, peer-reviewer, and design-reviewer disagree, invoke consensus builder
- Weighted voting: each reviewer votes APPROVED/BLOCKED with confidence score
- Majority verdict wins; tie → escalate to senior-developer
- Log consensus decision with individual votes for audit trail

**P2.7 — Mid-Build Memory Sync (Not Session-End Only)**
Make Recall queryable mid-build rather than only updated at session end.
- `masonry-observe.js` already writes to Recall asynchronously on PostToolUse
- Add `masonry-mid-build-recall.js` — every N tasks, query Recall for relevant patterns and inject into orchestrator context
- N = configurable, default 5 tasks

### Tier 3 — Architecture Changes (4-8 weeks)

**P3.1 — Training Pipeline (EMA Strategy Selector)**
Online learning loop for adaptive execution strategy selection.
- Depends on P1.1 telemetry (needs ~50 samples per task type)
- `masonry/src/training/collector.py` — reads telemetry.jsonl, groups by task_type
- `masonry/src/training/selector.py` — given task_type + history, returns optimal strategy
- EMA formula: `alpha=0.3; ema = 0.3*outcome + 0.7*ema`
- Cold start: all strategies at 0.688 (Ruflo's conservative baseline)

**P3.2 — ReasoningBank (Local HNSW Index)**
2-3ms local retrieval for synchronous session-start pattern injection.
- Depends on P2.3 confidence scoring (patterns need confidence fields)
- SQLite (metadata) + hnswlib (vectors)
- Session-start: inject top-5 patterns synchronously before build starts
- Qdrant stays for long-term archival and full-text search
- Dependencies: `pip install hnswlib`

**P3.3 — Knowledge Graph + PageRank Pattern Ranking**
High-connectivity patterns surface reliably; stale patterns don't.
- Depends on P3.2 ReasoningBank
- Neo4j CITES edges between co-used successful patterns (already in stack)
- PageRank run identifies high-value patterns
- Project isolation: each project gets its own graph scope

**P3.4 — Adaptive Topology Selection**
Auto-select swarm topology based on task dependency graph.
- Depends on P1.1 telemetry (task dependency graph data)
- Analysis in swarm_init: all independent → hierarchical; shared review → mesh; linear chain → ring
- `adaptive-coordinator.md` receives explicit topology recommendation
- Mesh topology specifically enables peer-review between specialist agents

**P3.5 — Agent Booster Pattern (Zero-LLM Transforms)**
Deterministic transforms that skip the LLM entirely.
- Catalog of deterministic Python AST transforms (add type hints, enforce imports, add docstrings)
- Pre-execution check: does this task match a known transform? If yes, apply directly.
- MCP tool: `masonry_apply_transform` — takes file path + transform name + params
- Fallback to developer agent if transform doesn't match
- Potential: 50-300x faster for tasks that match, zero API cost

**P3.6 — Stream-JSON Inter-Agent Piping**
Direct output-to-input streaming between pipeline agents.
- Design: stdout of upstream agent piped to stdin of downstream agent via temp buffer
- Eliminates file I/O for build chains (compiler → test → deploy)
- Implementation: subprocess stdout pipe + rolling buffer in masonry-agent-complete.js
- Fallback to file-based handoff if stream fails

---

## Section 7 — What BrickLayer Does Better Than Ruflo

These are genuine strengths. Don't compromise them while closing gaps.

**1. Research Campaign Depth (No Ruflo Equivalent)**
BrickLayer's question bank, wave management, synthesis, CAMPAIGN_PLAN.md, findings corpus, adaptive follow-up (FAILURE auto-drills Q2.4 → Q2.4.1), and the full BL 2.0 operational mode system (simulate, diagnose, fix, research, audit, validate, benchmark, evolve, monitor, predict, frontier) have no equivalent in Ruflo. Ruflo is a build platform. BrickLayer is a research + build platform. This is a genuine architectural advantage.

**2. Hook System Depth (25 hooks vs Ruflo's 17)**
BrickLayer's hook architecture is more sophisticated:
- Conditional matching (`PreToolUse:Write|Edit` pattern)
- TDD enforcement at the hook level (not just agent instruction)
- Design token enforcement for UI files
- 8-hook ordered stop sequence
- UserPromptSubmit interception (masonry-prompt-router.js)
- 3-strike error fingerprinting in masonry-guard.js

Ruflo's hooks are broader in categories but shallower in per-hook sophistication.

**3. Four-Layer Semantic Routing (Ruflo Has Q-Learning Only)**
Mortar's deterministic → semantic → LLM → fallback pipeline handles 60%+ of routing with zero LLM calls. Ruflo's routing is Q-Learning based — it learns but it always calls the router model. BrickLayer's deterministic layer is faster for known patterns.

**4. Typed Payload Schemas (Pydantic v2)**
BrickLayer's `QuestionPayload`, `FindingPayload`, `RoutingDecision`, `DiagnosePayload`, `DiagnosisPayload` are typed Pydantic v2 models with validation. Ruflo's inter-agent communication is JSON passed through memory namespaces without enforced schemas.

**5. DSPy Optimization Pipeline**
BrickLayer's agent optimization loop (eval → optimize → compare → revert if worse) with `improve_agent.py`, per-agent scored_all.jsonl, and Kiln OPTIMIZE button has no documented equivalent in Ruflo. Ruflo mentions "neural optimization" but does not expose a systematic prompt optimization workflow.

**6. Masonry MCP Tool Surface (20+ Targeted Tools)**
`masonry_route`, `masonry_fleet`, `masonry_recall`, `masonry_wave_validate`, `masonry_task_assign`, `masonry_run_question`, `masonry_swarm_init`, `masonry_worker_status`, `masonry_consensus_check` give the orchestrator fine-grained control that Ruflo's CLI doesn't match in precision. MCP-native integration avoids subprocess overhead.

**7. Deterministic Task Execution with Progress Tracking**
BrickLayer's `progress.json` with explicit `PENDING/IN_PROGRESS/DONE/BLOCKED` per task, `build.log` append-only audit trail, and ability to resume from any task ID has more reliability than Ruflo's task store (which had no execution engine until v3.5.43 and had sync bugs through v3.5.42).

**8. Self-Audit Campaigns (BrickLayer Runs BL on Itself)**
The `bl2` project is BrickLayer running 25 waves of campaign on its own codebase, producing 49 fixes and shipping 13+ improvements via its own research loop. No equivalent in Ruflo. This self-improvement via research loop is unique to BrickLayer's hybrid architecture.

**9. Campaign Working Memory Architecture (scratch.md + pointer + wave partitioning)**
BrickLayer's typed signal board (`scratch.md` with WATCH/BLOCK/DATA/RESOLVED signals), mid-wave pointer agent (checkpoint every 8 questions), and wave-partitioned findings structure are more sophisticated than anything in Ruflo's memory architecture for long-running research tasks.

---

## Section 8 — Agent Inventory Cross-Reference

### Ruflo Has, BrickLayer Lacks

| Ruflo Agent | BrickLayer Equivalent | Gap |
|-------------|----------------------|-----|
| Pseudocode Agent | None | Missing SPARC Phase 2 |
| Architecture Phase Agent | architect (general) | Needs dedicated phase agent |
| Token Optimizer (WASM) | None | No zero-LLM transform tier |
| Performance Optimizer | refactorer (partial) | No perf-focused specialist |
| Mobile Developer | developer (partial) | No mobile-specific agent |
| API Documenter | karen (partial) | No API-doc specialist |
| Release Manager | git-nerd (partial) | No full release lifecycle agent |
| Consensus Builder | None | No structured verdict resolution |
| Memory Coordinator | hooks only | No agent-level memory management |
| Load Balancer | mortar routing | No dynamic load awareness |
| CI/CD Engineer | devops (partial) | CI/CD pipeline specialist gap |
| ML Developer | python-specialist (partial) | No ML-specific agent |
| Byzantine Agent | None | No fault-tolerant consensus agent |

### BrickLayer Has, Ruflo Lacks

| BrickLayer Agent | Purpose |
|-----------------|---------|
| trowel | Campaign conductor — owns full BL 2.0 research loop |
| planner | Pre-campaign strategic planning |
| question-designer-bl2 | Question bank generation with operational modes |
| hypothesis-generator-bl2 | Wave N+1 question generation from findings |
| synthesizer-bl2 | Wave synthesis with CHANGELOG/ARCHITECTURE/ROADMAP maintenance |
| skill-forge | Crystallizes findings into reusable skills |
| mcp-advisor | Maps failures to missing MCP servers |
| cascade-analyst | Failure cascade and dependency analysis |
| forge-check | Agent fleet gap detection |
| pointer | Mid-wave compression and checkpoint |
| overseer | Fleet-level agent health and optimization |
| tdd-london-swarm | London School TDD specialist |
| mutation-tester | Mutation testing for test suite quality |
| economizer | Token/cost optimization |
| solana-specialist | Anchor programs and DeFi integration |
| kiln-engineer | Kiln (BrickLayerHub) specialist |

---

## Section 9 — Summary Priority Matrix

| Rank | Item | Category | BL Current | Ruflo Has | Effort | Impact |
|------|------|----------|-----------|-----------|--------|--------|
| 1 | SPARC Pseudocode Phase | Workflow | Missing | Phase 2 of 5 | Medium | Very High |
| 2 | Pre/post-task telemetry hooks | Tooling | Missing | pre-task/post-task hooks | Low | Very High (enables training) |
| 3 | Claims Board (async escalation) | Workflow | Stop-build | Claims system | Low | High |
| 4 | 7-Point Verification | Quality Gates | 2-point | 7-point | Medium | High |
| 5 | Senior agent escalation tier | Orchestration | Human-only | Tiered escalation | Medium | High |
| 6 | Pre-edit backup hook | Tooling | Missing | pre-edit hook | Low | High |
| 7 | Agent-complete dependency signaling | Orchestration | File-based | Real-time | Low | High |
| 8 | Execution strategy flag | Orchestration | Fixed | 3-strategy adaptive | Low | Medium |
| 9 | Phase checkpoint commits | Workflow | Missing | After-each-stage | Low | Medium |
| 10 | SPARC Architecture Phase | Workflow | Missing | Phase 3 of 5 | Medium | Medium |
| 11 | Confidence-scored patterns | Memory | Missing | Bayesian + decay | Medium | High |
| 12 | Lightweight consensus for review | Orchestration | Missing | Weighted voting | Medium | Medium |
| 13 | Mid-build memory sync | Memory | Session-end only | Real-time | Medium | Medium |
| 14 | Training pipeline (EMA) | Learning | Missing | SONA pipeline | High | Very High (long-term) |
| 15 | ReasoningBank (HNSW local) | Memory | Remote Qdrant | 2-3ms local | High | High |
| 16 | Agent Booster pattern (WASM) | Tooling | Missing | Tier-0 WASM | High | High |
| 17 | Adaptive topology selection | Orchestration | Hierarchical fixed | Auto-select | High | Medium |
| 18 | Knowledge graph + PageRank | Memory | Flat Recall | Graph + PageRank | High | Medium |
| 19 | Stream-JSON inter-agent piping | Orchestration | File-based | Stream | High | Medium |
| 20 | Circuit breaker for tools | Orchestration | Stop-on-failure | Graceful degrade | Medium | Medium |

---

## Appendix A — Ruflo v3.5.0 Release Highlights

Relevant capabilities added in the production release (2026-02-27):

- **agentic-flow v3 integration**: ReasoningBank WASM, 3-tier model routing (75% API cost reduction target), lazy-loading bridge
- **AgentDB v3 with 8 new controllers** (documented in Section 4.1)
- **Security hardening**: command injection fix, TOCTOU race elimination, HMAC key rotation, timing attack mitigations
- **MutationGuard**: cryptographic proof-verified memory writes
- **Performance**: memory search 150x-12,500x faster (HNSW), embedding generation 75x faster, Agent Booster 352x faster, CLI startup 4x faster

---

## Appendix B — What Not to Steal

Some Ruflo capabilities are architectural choices that would conflict with BrickLayer's design philosophy:

**Multi-provider LLM routing (Claude + GPT + Gemini + Cohere + Ollama failover)**
BrickLayer is Claude-native. Provider abstraction adds complexity for marginal benefit given Tim's preference for Anthropic models. Ollama is already used for Recall's semantic layer — that's sufficient.

**IPFS decentralized storage**
Overkill for current BrickLayer usage. Recall at `100.70.195.84:8200` handles cross-machine access via Tailscale already.

**Browser-based fine-tuning (WASM in-browser training)**
BrickLayer uses the Linux LXC for training. Browser-based training is a Ruflo-specific deployment constraint irrelevant to BrickLayer.

**LoRA/MicroLoRA adapter management**
BrickLayer's fine-tuning pipeline (TRAINING_BRANCH_PLAN.md) uses standard LoRA via the LXC. MicroLoRA compression (128x) is interesting but premature — get the base training pipeline working first.

**K8s deployment validation**
Tim's infrastructure is Docker Compose on CasaOS. Kubernetes validation in the verification gate would always fail. Docker build validation (Section 5.2, Check 7) is the relevant parallel.

---

*This analysis was produced from direct reading of the Ruflo repository (README.md, CLAUDE.md, wiki pages, skills), BrickLayer's ROADMAP.md, DEV_EXECUTION_ROADMAP.md, agent_registry.yml, CLAUDE.md, and the prior `.autopilot/ruflo-gap-synthesis.md`. All Ruflo capability claims are sourced from the v3.5.0 production documentation.*
