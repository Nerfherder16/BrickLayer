# Background Consolidation — Recall 2.0

Consolidation is P7: mandatory, not optional, not manually triggered. It is the software equivalent of sleep — the process that transforms raw episodic memories into durable semantic knowledge.

**Last updated**: 2026-03-16

---

## The Problem Consolidation Solves

Without consolidation, a memory system degrades over time:
- Raw memories accumulate redundancy (same fact stored 50 different ways across sessions)
- Low-level specificity dominates (individual stack traces, not "this system fails under X condition")
- No higher-order patterns emerge (no "Tim always needs context on the Proxmox VMs when working on networking")
- Retrieval precision decreases as noise grows

Current systems that claim consolidation (mem0, Zep) do it on write — LLM decides whether to ADD/UPDATE/DELETE each new memory against existing ones. This is expensive (every write requires LLM inference) and limited (only creates one level of abstraction: deduplicated facts).

Recall 2.0 consolidation is:
- **Idle-time** — runs when the system is not serving requests
- **Multi-level** — builds abstractions over abstractions (episodes → patterns → principles)
- **Autonomous** — no trigger, no schedule, no LLM write-time call
- **Generative** — creates new memory nodes that didn't exist, not just deduplication

---

## Trigger: Idle Detection

The consolidation process is not scheduled. It activates when the system is idle — no retrieval requests for N consecutive minutes.

```rust
struct ConsolidationController {
    last_request_at: Instant,
    idle_threshold: Duration,   // configurable, default 5 minutes
    consolidation_active: bool,
}

impl ConsolidationController {
    fn tick(&mut self) {
        let idle_duration = self.last_request_at.elapsed();
        if idle_duration > self.idle_threshold && !self.consolidation_active {
            self.start_consolidation();
        }
        if idle_duration < self.idle_threshold && self.consolidation_active {
            self.pause_consolidation();  // resume when idle again
        }
    }
}
```

**Consolidation is interruptible.** Any incoming request pauses it. It resumes when idle again.

Open question: what is the right idle threshold? Too short → consolidates during brief pauses, competes with retrieval. Too long → never runs during active work periods.

---

## Consolidation Process: Three Phases

### Phase 1: Cluster Discovery

Identify groups of related memories using the Hopfield energy landscape — memories that co-activate form natural clusters.

```python
def discover_clusters(hopfield: HopfieldLayer, lmdb: LmdbDatabase) -> List[MemoryCluster]:
    # Use Hopfield dynamics to find basins of attraction
    # Each basin = a cluster of related memories
    clusters = hopfield.find_attractor_basins(
        n_probes=1000,           # random starting points
        convergence_threshold=0.95
    )

    # Filter clusters by behavioral evidence
    # A cluster is worth consolidating if its members are co-retrieved
    enriched = []
    for cluster in clusters:
        co_retrieval_density = lmdb.co_retrieval_density(cluster.member_ids)
        if co_retrieval_density > CONSOLIDATION_MIN_DENSITY:
            enriched.append(ClusterWithContext(cluster, co_retrieval_density))

    return enriched
```

**Key**: clusters are discovered from the Hopfield energy landscape and validated with behavioral co-retrieval evidence. Not from LLM similarity judgments.

### Phase 2: Abstraction Generation

For each cluster, run a local LLM to generate an abstraction node — a higher-level memory that captures the pattern.

```python
def generate_abstraction(cluster: ClusterWithContext, llm: LocalLLM) -> Memory:
    member_texts = [load_text(m) for m in cluster.member_ids]

    abstraction = llm.generate(
        prompt=f"""
These memories were frequently retrieved together. Identify the higher-level pattern they share.
Write a single, precise statement that captures what these memories collectively represent.
Do not summarize. Identify the underlying principle or pattern.

Memories:
{chr(10).join(member_texts)}
        """,
        model="qwen3:14b",
        max_tokens=200,
    )

    return Memory(
        text=abstraction,
        source="consolidation",
        source_memories=cluster.member_ids,
        abstraction_level=cluster.level + 1,  // episodic=0, semantic=1, schematic=2
        created_at=now(),
    )
```

**Abstraction types by level:**
- Level 0: Episodic — raw memories from sessions ("Got a 503 error on the Proxmox API at 3pm")
- Level 1: Semantic — patterns across episodes ("Proxmox API returns 503 when memory pressure is high")
- Level 2: Schematic — principles across patterns ("Homelab services degrade under memory pressure, not CPU pressure")

### Phase 3: Writing Back

Abstractions are written back as first-class memories — they go through the full write pipeline, including deduplication and Hopfield integration.

```python
def consolidation_write(abstraction: Memory, write_pipeline: WritePipeline):
    # Full write pipeline — same as any memory
    result = write_pipeline.write(abstraction)

    # Additionally: link source memories to abstraction
    for source_id in abstraction.source_memories:
        lmdb.record_abstraction_link(source_id, abstraction.id)
```

Source memories are NOT deleted after abstraction. They remain available for retrieval. The abstraction node is an additional memory, not a replacement.

**Why not delete source memories?** Abstraction loses specificity. If you need the exact stack trace, you need the episodic memory, not the abstraction. Keep both.

---

## Consolidation Priority

Not all clusters are worth consolidating with equal urgency:

```
priority(cluster) =
    co_retrieval_density(cluster) × 0.50
  + cluster_size(cluster) × 0.30
  + age_of_oldest_member(cluster) × 0.20
```

Consolidation processes the highest-priority clusters first. If interrupted, the most valuable work is done.

---

## Conflict and Contradiction Detection

When generating abstractions, the LLM may identify contradictions in the cluster:

```
Memory A: "The RTX 3090 is on 192.168.50.62"
Memory B: "The RTX 3090 is on 192.168.50.63"
```

Consolidation generates a contradiction record rather than an abstraction:

```
{
  type: "contradiction",
  source_memories: [A, B],
  description: "RTX 3090 IP conflict — two different IPs recorded",
  requires_human_resolution: true,
}
```

Contradiction records are surfaced via the health endpoint — not silently resolved.

---

## Consolidation and the Hopfield Layer

Abstract memories are stored in Hopfield like any other memory. They create new attractors in the energy landscape at a higher level of abstraction. When a query activates an abstract memory, it also activates (via energy propagation) the source episodic memories that gave rise to it.

This is the mechanism by which retrieval improves with use: consolidation enriches the energy landscape, retrieval from the enriched landscape is more precise.

---

## What Consolidation Does NOT Do

- **Does not delete memories** — consolidation only adds (abstraction nodes)
- **Does not modify source memories** — they remain unchanged
- **Does not run on a cron schedule** — purely event-driven (idle detection)
- **Does not require a trigger from Claude** — fully autonomous
- **Does not assign importance scores** — abstraction priority is behavioral

---

## Open Questions

- What is the right idle threshold? (see `decisions/open.md` candidate questions)
- Should abstractions write to the same collection or a separate "abstract memory" tier?
- At what point does multi-level abstraction start losing useful specificity?
- How does the LLM handle contradictory source memories? What prompt design minimizes confabulation?
- What is the right cluster density threshold for triggering consolidation?
