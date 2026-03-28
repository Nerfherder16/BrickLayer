# Dev Execution Roadmap — Closing the Ruflo Gaps

**Created**: 2026-03-27
**Source**: `.autopilot/ruflo-gap-synthesis.md`
**Goal**: Ruflo-level autonomous app building without human intervention

---

## Phase 1 — Quick Wins (1-2 weeks)

Additive work only. No existing behavior changes. No architectural dependencies.

---

### 1.1 Pre-task / Post-task Telemetry Hooks

**Gap addressed**: Gap 8 — no task-level telemetry feeding the future training pipeline.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-pre-task.js` | CREATE | PreToolUse(Agent) — write task record to `.autopilot/telemetry.jsonl` with timestamp, task_id, complexity |
| `masonry/src/hooks/masonry-post-task.js` | CREATE | PostToolUse(Agent) — append outcome, duration_ms, agent_used, success/fail |
| `masonry/src/schemas/payloads.py` | EXTEND | Add `TaskTelemetryRecord` Pydantic model |
| `masonry/.claude/settings.json` | REGISTER | Add both hooks to PreToolUse/PostToolUse(Agent) events |

Record schema:
```json
{"task_id": "t-001", "phase": "pre", "timestamp": "ISO", "type": "frontend", "complexity": "low"}
{"task_id": "t-001", "phase": "post", "timestamp": "ISO", "duration_ms": 4200, "success": true, "agent": "general-purpose"}
```

**Why now**: Training pipeline (Phase 3) needs 50+ samples per task type. Every build after this hook accumulates signal. Start collecting immediately.

---

### 1.2 Pre-edit Backup Hook

**Gap addressed**: Gap 8 — a bad Write/Edit currently requires `git reset --hard`.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-pre-edit.js` | CREATE | PreToolUse(Write/Edit) — snapshot file to `.autopilot/backups/` before modification |
| `masonry/src/hooks/masonry-build-guard.js` | EXTEND | Add backup cleanup (prune backups >7 days old) to Stop event |

Behavior:
- Only fires when `.autopilot/mode` is `build` or `fix` (no-op otherwise)
- Backup path: `.autopilot/backups/{relative_path}/{filename}.{ISO_timestamp}`
- Silent exit if file doesn't exist yet (new file write)

**Why now**: Enables instant single-file rollback without touching git history. Immediate pain relief.

---

### 1.3 Agent-complete Hook

**Gap addressed**: Gap 5 — results polled via files; dependent agents can't start until the full batch completes.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-agent-complete.js` | CREATE | SubagentStop — write to `.autopilot/results/{agent_id}.json`; signal dependent tasks |
| `masonry/bin/masonry-mcp.js` — toolSwarmInit | EXTEND | Add `depends_on` field to task schema |
| `masonry/src/hooks/masonry-teammate-idle.js` | EXTEND | Check result cache; wake dependent tasks immediately on completion |

Dependency format in progress.json:
```json
{"id": 4, "description": "Integration test", "status": "PENDING", "depends_on": [3]}
```

**Why now**: Frontend build → integration test chains can start the moment the build finishes rather than waiting for the whole batch.

---

### 1.4 Execution Strategy Flag

**Gap addressed**: Gap 4 — one strategy for all tasks; a db migration runs the same as a config typo fix.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-prompt-router.js` | EXTEND | Parse `--strategy conservative/balanced/aggressive` from UserPromptSubmit |
| `masonry/bin/masonry-mcp.js` — toolSwarmInit | EXTEND | Accept `strategy` field; write to `.autopilot/strategy` |
| `masonry/src/hooks/masonry-teammate-idle.js` | EXTEND | Inject strategy context into task assignment output |
| `~/.claude/skills/build.md` | EXTEND | Document the `--strategy` flag |

Strategy definitions (written to `.autopilot/strategy`):
```
conservative  → extra verification steps, security scan, slower but thorough
balanced      → default path, standard test suite
aggressive    → skip redundant checks, parallel tasks, fastest path
```

**Why now**: Even before the training pipeline auto-selects strategy, giving Tim (or the orchestrator) explicit control per task is immediately useful.

---

### 1.5 Phase Checkpoint Commits

**Gap addressed**: Gap 2 — failure means full restart; no mid-build rollback point.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-build-guard.js` | EXTEND | Detect phase boundary on DONE task; fire git-nerd for tagged commit |
| `masonry/bin/masonry-mcp.js` — toolSwarmInit | EXTEND | Accept `phases` array; mark `phase_end` on tasks in progress.json |
| `~/.claude/agents/git-nerd.md` | EXTEND | Handle `--phase-checkpoint` flag; tag as `phase/{name}` |

Phase boundary detection in progress.json:
```json
{"id": 5, "description": "Architecture approved", "status": "DONE", "phase_end": "architecture"}
```

Tag format: `phase/spec`, `phase/architecture`, `phase/refinement`, `phase/completion`

**Why now**: Fits directly onto the existing git-nerd pattern. Rollback to checkpoint instead of full abort.

---

## Phase 2 — Medium Term (2-4 weeks)

---

### 2.1 SPARC Phases: Pseudocode + Architecture

**Gap addressed**: Gap 2 — 2-stage build (spec → code) vs 5-stage SPARC.

**Current**: `spec.md` → `/build`
**Target**: `spec.md` → `pseudocode.md` → `architecture.md` → `/build` (Refinement + Completion)

| File | Action | Purpose |
|------|--------|---------|
| `~/.claude/agents/spec-writer.md` | EXTEND | Add pseudocode + architecture phases before returning |
| `~/.claude/skills/pseudocode.md` | CREATE | New skill — writes `.autopilot/pseudocode.md` (plain English logic, no code syntax) |
| `~/.claude/skills/architecture.md` | CREATE | New skill — spawns architect; writes `.autopilot/architecture.md` |
| `~/.claude/agents/developer.md` | EXTEND | Inject both docs into task prompt if present |

Pseudocode = per-task logic in plain English (flow + edge cases, no syntax).
Architecture = component diagram, interface contracts, data flow, explicit out-of-scope list.

**Why**: The most common source of multi-cycle rework is a developer agent building the right code for the wrong design. Pseudocode makes logic explicit before implementation.

---

### 2.2 Confidence-Scored Pattern Storage

**Gap addressed**: Gap 3 — patterns never decay; bad patterns survive indefinitely alongside good ones.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/hooks/masonry-post-task.js` | EXTEND | Success: `confidence += 0.20*(1-c)`; Failure: `confidence -= 0.15*c` |
| `masonry/src/hooks/masonry-training-export.js` | EXTEND | Include confidence delta in recall export payload on Stop |
| `masonry/bin/masonry-mcp.js` | EXTEND | Add `masonry_pattern_decay` tool: prune patterns below 0.2 threshold |
| `masonry/src/schemas/payloads.py` | EXTEND | Add `confidence` float field to `PatternRecord` |

Bayesian update rules (matching Ruflo):
```
success:    confidence += 0.20 * (1 - confidence)
failure:    confidence -= 0.15 * confidence
time decay: -0.005 per hour since last use
prune:      remove if confidence < 0.2
initial:    0.7 for all existing patterns
```

**Why**: Qdrant already handles retrieval. The gap is in the feedback loop, not the storage backend.

---

### 2.3 7-Point Verification Checklist

**Gap addressed**: Gap 6 — tests + lint is the full bar. Security and deployment never checked.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/bin/masonry-mcp.js` | EXTEND | Add `masonry_verify_7point` tool: runs all 7 checks, returns structured report |
| `masonry/src/hooks/masonry-lint-check.js` | EXTEND | Add security scan as check 5 |
| `~/.claude/skills/verify.md` | EXTEND | Call `masonry_verify_7point`; block PASS verdict on any failure |
| `~/.claude/agents/verification.md` | EXTEND | Add 7-point checklist to verdict criteria |

7 checks (fail-fast order):
1. Test coverage >= 80%
2. Unit tests pass
3. Integration tests pass
4. E2E tests pass (if test files exist)
5. **Security scan** — `bandit -r src/ -q` (Python) or `eslint --plugin security` (JS) — NEW
6. **Performance baseline** — warn if >20% slower than prior run — NEW
7. **Docker build** — only if Dockerfile present — NEW

**Why**: Security and deployment checks wrap existing tools. 70% of the value for 30% of the work.

---

### 2.4 Senior Agent Escalation Tier

**Gap addressed**: Gap 7 — 3 developer failures goes straight to Tim; no intermediate capable agent.

**Current**: `developer x3` → `diagnose-analyst` → human
**Target**: `developer x3` → `senior-developer` → `architect` → `diagnose-analyst` → human + GitHub issue

| File | Action | Purpose |
|------|--------|---------|
| `~/.claude/agents/senior-developer.md` | CREATE | Wider system context, reads all related files, can propose refactors |
| `~/.claude/skills/build.md` | EXTEND | Add senior-developer before diagnose-analyst in escalation chain |
| `masonry/bin/masonry-mcp.js` | EXTEND | Add `masonry_github_issue` tool: auto-create issue + full log on human escalation |
| `~/.claude/agents/hierarchical-coordinator.md` | EXTEND | Wire escalation chain with new senior tier |

Escalation flow:
```
developer fails x3 → DEV_ESCALATE
  → senior-developer (full system context, wider file scope)
senior-developer fails → SENIOR_ESCALATE
  → diagnose-analyst (root cause analysis)
diagnose-analyst → DIAGNOSIS_COMPLETE → fix-implementer
fix-implementer fails → HUMAN_ESCALATE
  → create GitHub issue with full task log + notify Tim
```

**Why**: Most failures that currently interrupt Tim (junior agent hitting architectural wall) can be resolved by a more capable agent with broader context.

---

## Phase 3 — Long Term (Architecture Changes)

---

### 3.1 Training Pipeline

**Gap addressed**: Gap 1 — every build uses the same strategy; no learning across builds.
**Depends on**: Phase 1.1 telemetry — needs ~50 samples per task type first.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/training/collector.py` | CREATE | Read `telemetry.jsonl`; group by task_type; compute EMA success rate per strategy |
| `masonry/src/training/selector.py` | CREATE | Given task_type + history, return optimal strategy |
| `masonry/bin/masonry-mcp.js` | EXTEND | Add `masonry_training_update` tool: trigger EMA recompute after each build |
| `masonry/src/hooks/masonry-pre-task.js` | EXTEND | Auto-call selector; write recommended strategy to `.autopilot/strategy` |

EMA formula: `alpha=0.3; ema = 0.3*outcome + 0.7*ema`
Cold start: all strategies begin at 0.688 (Ruflo's base conservative success rate).

---

### 3.2 ReasoningBank (Local HNSW Index)

**Gap addressed**: Gap 3 — Qdrant ~200ms round-trips too slow for synchronous session-start injection.
**Depends on**: Phase 2.2 confidence scoring (patterns need confidence fields before indexing).

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/reasoning/bank.py` | CREATE | SQLite (metadata) + hnswlib (vectors); 2-3ms local retrieval |
| `masonry/src/hooks/masonry-session-start.js` | EXTEND | Query ReasoningBank synchronously; inject top-5 patterns into context |
| `masonry/bin/masonry-mcp.js` | EXTEND | Add `masonry_reasoning_query` and `masonry_reasoning_store` tools |

Dependencies: `hnswlib-python`, `sqlite3` (stdlib)
Qdrant stays for long-term archival and full-text search.

---

### 3.3 Knowledge Graph + PageRank Pattern Ranking

**Gap addressed**: Gap 9 — flat Recall storage; no pattern relationships; high-value patterns don't surface reliably.
**Depends on**: Phase 3.2 ReasoningBank.

| File | Action | Purpose |
|------|--------|---------|
| `masonry/src/reasoning/graph.py` | CREATE | Neo4j CITES edges between co-used successful patterns |
| `masonry/src/reasoning/pagerank.py` | CREATE | PageRank run; updates confidence scores in bank |
| `masonry-daemon-manager.js` | EXTEND | Nightly PageRank recompute |

Edge creation: task T succeeds using patterns [A, B, C] → create CITES edges between all three.
Project isolation: each project gets its own graph scope.

---

### 3.4 Adaptive Topology Selection

**Gap addressed**: BrickLayer always uses hierarchical topology; mesh/ring never applied.
**Depends on**: Phase 1.1 telemetry (task dependency graph data).

| File | Action | Purpose |
|------|--------|---------|
| `masonry/bin/masonry-mcp.js` — toolSwarmInit | EXTEND | Analyze task dependency graph; recommend topology |
| `~/.claude/agents/adaptive-coordinator.md` | UPDATE | Receive explicit topology recommendation from swarm_init |

Selection rules:
```
All tasks independent        → hierarchical (current default)
Tasks with shared code review → mesh (peer review between agents)
Linear chain (N feeds N+1)   → ring (stream output directly)
Mixed                        → hybrid
```

---

## Sequencing Map

```
No deps — start immediately:
  1.2 pre-edit backup         ← smallest, immediate pain relief
  1.4 strategy flag           ← zero architectural change
  1.5 phase checkpoints       ← fits existing git-nerd
  1.1 pre/post telemetry      ← starts data clock for 3.1
  1.3 agent-complete          ← dependency signaling

No deps — weeks 3-5:
  2.4 senior agent tier       ← biggest Tim interruption reduction
  2.3 7-point verify          ← wraps existing tools
  2.1 SPARC phases            ← biggest rework cycle reduction
  2.2 confidence scoring      ← Recall metadata extension
    └─> 3.2 ReasoningBank
          └─> 3.3 knowledge graph

  1.1 telemetry (after 50+ samples/type)
    └─> 3.1 training pipeline
          └─> 3.4 adaptive topology
```

---

## Net New Files

```
masonry/src/hooks/masonry-pre-task.js
masonry/src/hooks/masonry-post-task.js
masonry/src/hooks/masonry-pre-edit.js
masonry/src/hooks/masonry-agent-complete.js
~/.claude/skills/pseudocode.md
~/.claude/skills/architecture.md
~/.claude/agents/senior-developer.md
masonry/src/training/collector.py
masonry/src/training/selector.py
masonry/src/reasoning/bank.py
masonry/src/reasoning/graph.py
masonry/src/reasoning/pagerank.py
```

---

## Recommended Start Order

1. **Phase 1.2** — smallest, immediate pain relief on bad writes during builds
2. **Phase 1.4** — zero architectural change; immediately controls build behavior
3. **Phase 1.1** — starts the data clock for the training pipeline
4. **Phase 2.4** — biggest reduction in Tim interruptions per build
5. **Phase 2.1** — biggest reduction in multi-cycle rework
