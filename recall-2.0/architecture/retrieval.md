# Retrieval Engine — Recall 2.0

Retrieval is the most latency-sensitive operation and the one that most directly determines the system's value. A memory system that surfaces the wrong things fast is worse than useless.

**Last updated**: 2026-03-16

---

## The Core Problem with Current Retrieval

Recall 1.0 does ANN search: embed the query, find the nearest vectors by cosine distance, return top-K.

This is wrong for three reasons:
1. **Cosine similarity is a proxy for relevance, not relevance itself.** "The deployment is failing" is semantically similar to "the production deploy worked" — both are about deployments. But only one is useful in the moment.
2. **Static similarity ignores behavioral history.** If you've retrieved memory X in the context of task Y twelve times, that's a direct measurement of causal relevance — not a proxy.
3. **Every retrieval leaves no trace.** The next retrieval starts from the same baseline. Nothing improves.

Recall 2.0 retrieval is multi-tier, behavioral, and self-improving.

---

## Retrieval Architecture: Four-Tier Cascade

```
Query arrives
     │
     ▼
┌─────────────────────────────────────────┐
│  Tier 0: Session Cache                  │
│  In-memory. Current session's           │
│  retrieved memories. O(1) lookup.       │
│  Hit: return immediately               │
│  Miss: continue                         │
└────────────────────┬────────────────────┘
                     │ Miss
                     ▼
┌─────────────────────────────────────────┐
│  Tier 1: LLPC Working Set               │
│  "Long-Lived Pattern Cache"             │
│  Memories with high behavioral score:  │
│  access_count × recency × co_retrieval │
│  ~100-500 memories, fits in L3 cache   │
│  Approximate match via bloom filter     │
│  Hit: return with Hopfield reactivation │
│  Miss: continue                         │
└────────────────────┬────────────────────┘
                     │ Miss
                     ▼
┌─────────────────────────────────────────┐
│  Tier 2: Hopfield Hot Layer             │
│  Pattern completion over full           │
│  associative memory                     │
│  One step: x(t+1) = X·softmax(βXᵀx)   │
│  Returns activation levels, not scores  │
│  Hit: return with reinforcement         │
│  Low confidence: continue              │
└────────────────────┬────────────────────┘
                     │ Low confidence / Miss
                     ▼
┌─────────────────────────────────────────┐
│  Tier 3: Cold ANN                       │
│  Qdrant or custom HNSW                 │
│  Full-corpus semantic search            │
│  Result promoted to Hopfield            │
│  Always returns something               │
└─────────────────────────────────────────┘
```

---

## Tier 0: Session Cache

Memories retrieved in the current session are held in memory. Second retrieval of the same memory in the same session is instant.

- **Structure**: HashMap<MemoryId, (ActivationLevel, RetrievedAt)>
- **Scope**: Per-session, discarded at session end
- **Eviction**: Session cache grows without bound during session (max session size is small enough that this is fine)
- **Effect on Hopfield**: None — session cache hits don't trigger additional reinforcement

---

## Tier 1: LLPC Working Set

The "Long-Lived Pattern Cache" is a dynamically maintained set of memories with high demonstrated behavioral value. Not a fixed list — it evolves as the system learns.

### Scoring Formula (no importance scores)
```
behavioral_score(m) =
    access_count(m) × 0.40
  + recency_factor(m) × 0.35        // e^(-λ × time_since_access)
  + co_retrieval_density(m) × 0.25  // how often retrieved with other high-value memories
```

**Note**: This is behavioral scoring, not importance scoring. The inputs are measured facts (how often accessed, when, with what), not LLM predictions about future relevance.

### LLPC Maintenance
- Recomputed on a slow background pass (every N writes or when memory count changes significantly)
- Top 100-500 memories by behavioral score enter the LLPC
- LLPC is stored in LMDB for persistence across restarts

### Bloom Filter
A probabilistic filter answers "is this query likely to match anything in the LLPC?" without scanning all 100-500 memories. False positives → full LLPC scan (cheap). False negatives → Hopfield (more expensive but correct).

---

## Tier 2: Hopfield Hot Layer

The primary retrieval mechanism. Given a query embedding, the Hopfield network completes the pattern to the nearest stored memory.

### Retrieval Steps
```
1. Normalize query embedding: x₀ = normalize(embed(query))
2. Run one update step: x₁ = X · softmax(β · Xᵀ · x₀)
3. Identify activated patterns: patterns where softmax weight > threshold
4. Return top-K by activation level
5. Trigger reinforcement for retrieved patterns (see below)
```

### Confidence Threshold
If the maximum activation level is below a confidence threshold, the result is unreliable (spurious attractor or genuine miss). In this case, cascade to cold ANN.

```
confidence = max(softmax(β · Xᵀ · x₀))
if confidence < HOPFIELD_CONFIDENCE_THRESHOLD:
    cascade_to_cold_ann()
```

### Retrieval Reinforcement
This is where P2 (Retrieval Must Reinforce) is implemented.

```
for each retrieved memory m:
    w_ij += η × m_i × m_j    // Hebbian update — deepen the energy well
    lmdb.increment_access_count(m.id)
    lmdb.record_access_event(m.id, session_id, context_hash)
    lmdb.update_last_accessed(m.id, now())
```

Co-retrieval tracking:
```
for each pair (m_a, m_b) in retrieved_memories:
    lmdb.increment_co_retrieval(m_a.id, m_b.id)
```

Reinforcement is a property of the retrieval mechanism, not a separate write call. It happens automatically.

---

## Tier 3: Cold ANN

Last resort. The cold store has the full corpus but no behavioral enrichment.

### What Happens on Cold Hit
```
1. ANN search returns memory m
2. Promote m to Hopfield hot layer:
   - Add m's embedding as a new stored pattern
   - If Hopfield is at capacity: evict lowest behavioral score memory
3. Trigger same reinforcement as Tier 2 hit
4. Return m with note: "cold promoted"
```

Cold hits are self-healing. A memory retrieved from cold once is now in Hopfield. Second retrieval goes through Tier 2.

---

## Result Format

Recall 1.0 returns memories with importance scores and relevance percentages. Recall 2.0 returns:

```
{
  memories: [
    {
      id: UUID,
      text: string,
      activation_level: float,     // from Hopfield dynamics (NOT importance score)
      tier: "session" | "llpc" | "hopfield" | "cold",
      access_count: int,           // total access count from LMDB
      last_accessed: timestamp,
      co_retrieved_with: UUID[],   // memories frequently retrieved in same context
    }
  ],
  retrieval_latency_ms: float,
  confidence: float,               // Hopfield max activation (quality signal)
}
```

**No importance scores. No relevance percentages.** The activation level is a physical quantity from the Hopfield dynamics — not an LLM-assigned number.

---

## Retrieval Latency Targets

| Tier | Target | Notes |
|---|---|---|
| Session cache hit | < 1ms | HashMap lookup |
| LLPC hit | < 5ms | Bloom filter + small set scan |
| Hopfield hit | < 20ms | Single matrix multiply + softmax |
| Cold ANN hit | < 50ms | Network call to Qdrant or HNSW scan |
| **Full cascade (worst case)** | **< 75ms** | All tiers miss until cold |

These targets are achievable on the RTX 3090 with fp16 Hopfield matrices.

---

## Context Injection Format

How retrieved memories reach Claude's context window is an open question (see `architecture/injection.md`). The retrieval engine returns structured results — the injection layer formats them for the prompt.

The retrieval engine does NOT decide how to format memories for Claude. That is the injection layer's responsibility. Separation of concerns.
