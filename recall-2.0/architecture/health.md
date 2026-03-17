# Health Monitoring — Recall 2.0

P8: health measures retrieval quality, not infrastructure. A system where all services respond 200 OK but retrieval is surfacing the wrong memories is broken — and current health monitoring doesn't catch this.

**Last updated**: 2026-03-16

---

## The Problem with Infrastructure Health

Recall 1.0 health endpoint tells you:
- Is Qdrant reachable?
- Is Neo4j reachable?
- Is Redis reachable?
- Is the PostgreSQL database reachable?

This is necessary but not sufficient. The question that determines whether the memory system is working is not "are the stores reachable?" — it's **"is the system retrieving the right things?"**

A memory system can be fully healthy by infrastructure metrics while:
- Returning memories from wrong tier (session cache never warm, always cold ANN)
- Hopfield spurious attractors dominating retrieval results
- Consolidation never running (idle threshold never triggered)
- Reinforcement working correctly but co-retrieval graph empty (no learning)
- Decay never computed because timestamps are malformed in LMDB

These are all silent failures. Infrastructure health monitoring doesn't catch any of them.

---

## Retrieval Quality Signals

### Signal 1: Tier Distribution

Where are retrieval results coming from?

```
tier_distribution = {
  session_cache: float,   // % of retrievals served from Tier 0
  llpc: float,            // % from Tier 1 (behavioral working set)
  hopfield: float,        // % from Tier 2 (associative memory)
  cold_ann: float,        // % from Tier 3 (cold fallback)
}
```

**Healthy**: Most retrievals served from Tier 2 (Hopfield), moderate LLPC warm. Low cold_ann.
**Unhealthy signals**:
- cold_ann > 20% sustained → Hopfield not learning, or wrong retrieval routing
- session_cache = 0% always → session cache not being populated correctly
- hopfield = 0% → Hopfield layer not reachable

### Signal 2: Hopfield Confidence Distribution

What are the activation levels on retrieval results?

```
confidence_histogram = {
  "0.0-0.3": int,  // very low confidence (likely spurious attractor)
  "0.3-0.6": int,  // medium confidence
  "0.6-0.8": int,  // good confidence
  "0.8-1.0": int,  // high confidence (correct attractor)
}
```

**Healthy**: Most retrievals in 0.6-1.0 range.
**Unhealthy**: High proportion in 0.0-0.3 → spurious attractors forming (Hopfield at capacity, or decay not working).

### Signal 3: Reinforcement Throughput

How many memories received reinforcement in the last hour?

```
reinforcement_rate = memories_reinforced / retrievals_performed
```

**Healthy**: reinforcement_rate ≈ 1.0 (every retrieval reinforces).
**Unhealthy**: reinforcement_rate < 0.9 → reinforcement pathway broken.

### Signal 4: Behavioral Graph Density

How rich is the co-retrieval graph?

```
behavioral_graph = {
  total_memories: int,
  memories_with_co_retrieval_edges: int,
  median_co_retrieval_degree: float,   // median edges per memory
  density: float,                      // edges / (n × (n-1)/2)
}
```

**Healthy**: density growing over time as the system learns. Not zero.
**Unhealthy**: density = 0 → co-retrieval tracking broken. Flat density → system not learning from use.

### Signal 5: Consolidation Activity

Is background consolidation running?

```
consolidation = {
  last_run_at: timestamp,
  abstractions_generated_24h: int,
  clusters_discovered_24h: int,
  contradictions_flagged_24h: int,
  idle_time_available_24h: hours,
}
```

**Healthy**: consolidation runs regularly when system is idle. Abstractions being generated.
**Unhealthy**: last_run_at > 24h ago despite idle time → consolidation not triggering. abstractions_generated = 0 → cluster discovery not finding patterns.

### Signal 6: Decay Health

Is the decay model functioning?

```
decay_health = {
  memories_near_eviction_threshold: int,   // activation < 0.1
  memories_with_stale_timestamps: int,      // last_accessed > 90 days
  average_activation_by_age: {             // activation should decrease with age
    "0-7d": float,
    "7-30d": float,
    "30-90d": float,
    "90d+": float,
  }
}
```

**Healthy**: activation decreasing with age (decay working). Near-eviction count proportional to old memory count.
**Unhealthy**: activation uniform across all ages → decay not being applied. Massive spike in near-eviction → decay running too fast.

---

## Health API Response

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "infrastructure": {
    "hopfield_layer": true,
    "lmdb": true,
    "cold_store": true,
    "embedding_service": true
  },
  "retrieval_quality": {
    "tier_distribution": {
      "session_cache": 0.12,
      "llpc": 0.31,
      "hopfield": 0.52,
      "cold_ann": 0.05
    },
    "hopfield_confidence": {
      "mean": 0.74,
      "p10": 0.45,
      "p90": 0.91
    },
    "reinforcement_rate": 0.98,
  },
  "learning": {
    "behavioral_graph_density": 0.034,
    "behavioral_graph_density_7d_trend": "+0.002",
    "consolidation_last_run": "2h ago",
    "abstractions_generated_24h": 14,
    "contradictions_flagged_24h": 2
  },
  "decay": {
    "mean_activation": 0.62,
    "memories_near_eviction": 847,
    "decay_model_healthy": true
  },
  "issues": [
    {
      "severity": "warning",
      "signal": "cold_ann_rate",
      "message": "Cold ANN retrieval rate above 10% for the last 6 hours. Hopfield may need retraining.",
      "recommendation": "Check Hopfield layer capacity and recent write volume."
    }
  ]
}
```

---

## Health Dashboard

Not required for MVP. But the dashboard should show:

1. **Tier distribution over time** — stacked area chart. Watch for cold_ann growing.
2. **Confidence distribution** — histogram, updated per retrieval session.
3. **Behavioral graph density** — single trend line. Should trend up over time.
4. **Consolidation timeline** — when did it last run, how many abstractions.
5. **Contradiction queue** — list of unresolved conflicts.

---

## Alerting Thresholds

| Signal | Warning | Critical |
|---|---|---|
| cold_ann_rate | > 10% sustained 1h | > 25% sustained 30m |
| hopfield_confidence (mean) | < 0.60 | < 0.40 |
| reinforcement_rate | < 0.95 | < 0.80 |
| behavioral_graph_density trend | Flat > 7d | Decreasing |
| consolidation_last_run | > 24h | > 72h (if idle time available) |
| contradictions_unresolved | > 10 | > 50 |

---

## What Infrastructure Health Still Covers

Infrastructure checks remain necessary — but they're table stakes, not the product:

- Hopfield PyTorch service: responsive, GPU allocated, memory available
- LMDB: environment open, no corruption flags
- Cold vector store: reachable, index healthy
- Embedding service (Ollama): model loaded, GPU available, latency within budget
- CRDT sync: last sync timestamp per peer machine

Infrastructure health = "is the system on?"
Retrieval quality health = "is the system working?"

Both are needed. Neither alone is sufficient.
