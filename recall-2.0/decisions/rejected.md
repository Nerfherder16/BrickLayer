# Rejected — Recall 2.0

Design options that were considered and explicitly rejected. Documenting rejections prevents the same ideas from being re-proposed without context.

**Last updated**: 2026-03-16

---

## How to Use This File

When an option is rejected (either from `open.md` or proposed during Frontier research):
1. Add it here with: what was rejected, why, and what edge case or condition might make it reconsidered
2. If the rejection closes an open decision, update `open.md` and `decided.md` accordingly

---

## Rejected Options

### R-001: LLM-Assigned Importance Scores for Any Decision
**Rejected at**: Principle level (P1)
**What it is**: Using an LLM to assign an importance score at write time, then using that score for eviction, routing, decay rate, or retrieval ranking.
**Why rejected**: Importance is a write-time prior. It has no relationship to causal relevance at retrieval time. A memory scored "low importance" when stored may be exactly what's needed for a task that didn't exist yet. All relevance evidence must come from demonstrated behavior (access frequency, co-retrieval, recency), not predicted future relevance.
**When to reconsider**: If empirical testing shows that importance-scored memories produce measurably better retrieval precision than behavioral scoring — and only then.

---

### R-002: Scheduled/Cron Decay Worker
**Rejected at**: Principle level (P3)
**What it is**: A background process that runs on a schedule and applies decay updates to memory importance/activation scores.
**Why rejected**: Creates timing artifacts (memories decay discretely, not continuously), requires operational infrastructure (worker must stay running), can fail independently of the main system, introduces a fixed discretization error on a continuous process. Timestamp arithmetic at read time is exact, stateless, and requires no infrastructure.
**When to reconsider**: If read-time decay computation proves to be a performance bottleneck at very high retrieval volume. Even then, prefer caching computed activation values with short TTL rather than reverting to scheduled decay.

---

### R-003: Coordination Protocols for Multi-Machine Consistency
**Rejected at**: Principle level (P4)
**What it is**: Any combination of: vector clocks, leader election, distributed locking, outbox flush workers, two-phase commit, Paxos, Raft.
**Why rejected**: Coordination protocols require all participating machines to be reachable to make progress, add latency on every write, and create failure modes (split-brain, partition) that CRDTs make mathematically impossible. For a personal memory system with two machines, the overhead of coordination is completely unjustified.
**When to reconsider**: If the system ever grows to a use case where strong consistency guarantees are required (financial data, audit logs, safety-critical systems). For AI memory, eventual consistency is correct.

---

### R-004: Using Recall 1.0's Four-Store Architecture in Recall 2.0
**Rejected at**: Architecture level
**What it is**: Keeping Qdrant + Neo4j + Redis + PostgreSQL as the storage substrate for Recall 2.0.
**Why rejected**: Four-store coherence is complex and fragile. Divergence is a known failure mode in production. Each store was chosen for general-purpose reasons, not for the specific semantics of AI memory. The new substrate (Hopfield + LMDB + CRDT) replaces all four with stores chosen specifically for memory system semantics.
**When to reconsider**: If the custom substrate proves too risky or complex to build and maintain, a hybrid approach (keep Qdrant as cold store, LMDB replaces Redis + PostgreSQL, no Neo4j) may be viable. This is OD-01.

---

### R-005: mem0's Write-Time LLM Consolidation
**Rejected at**: Design level
**What it is**: Calling an LLM on every write to decide whether to ADD, UPDATE, DELETE, or NOOP the new memory against existing ones.
**Why rejected**: Every write requires an LLM call — adds 200-2000ms to the write path and creates model dependency. Only operates at write time — can't build abstractions from patterns that emerge over many sessions. The four operations (ADD/UPDATE/DELETE/NOOP) are a useful model for deduplication but not for genuine consolidation. Recall 2.0 consolidation is async, idle-time, multi-level — fundamentally different from mem0's approach.
**When to reconsider**: If idle-time consolidation proves too slow or too low-quality, a lightweight write-time deduplication step (not full consolidation) may be added. This would be a simpler version of mem0's NOOP/ADD decision — and only for deduplication, not as a replacement for async consolidation.

---

### R-006: Importance-Scored LLPC (Long-Lived Pattern Cache)
**Rejected at**: Design level
**What it is**: Populating the LLPC working set based on LLM-assigned importance scores rather than behavioral scoring.
**Why rejected**: P1 (No Importance Scores). The LLPC must be populated based on demonstrated behavioral value: access frequency, recency, co-retrieval density. These are measurements of actual use, not predictions.
**When to reconsider**: Never. This is a principle-level rejection.

---

## Options Under Consideration (Not Yet Rejected)

*(Add options here that are being actively debated before reaching a rejection decision)*
