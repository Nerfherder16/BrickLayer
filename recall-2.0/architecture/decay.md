# Decay — Recall 2.0

Decay is P3: physics, not schedule. This document explains the mechanism and the implementation.

**Last updated**: 2026-03-16

---

## Why Scheduled Decay Is Wrong

Recall 1.0 runs an ARQ background worker that periodically applies importance decay to memories on a schedule. This is wrong for multiple reasons:

1. **Discrete approximation of a continuous process.** Memory fading is continuous. A cron job creates artificial step functions — memories are fine at 11:59pm and then suddenly 10% less important at midnight.

2. **Timing artifacts.** A memory stored just after a decay pass gets a free ride until the next pass. A memory stored just before gets decayed immediately.

3. **Infrastructure dependency.** If the decay worker crashes, memories stop decaying. If it runs twice, they decay twice. Operational fragility.

4. **Wrong model.** Decay is a property of time passing and access patterns — not an independent process that happens to memories from the outside.

**The correct model**: decay is a function of timestamps. Compute it at read time. No background process.

---

## The Decay Model

### Exponential Decay

```
activation(m, t) = activation₀(m) × e^(-λ(m) × Δt)

Where:
  activation₀(m) = baseline activation (from last reinforcement)
  λ(m)           = per-memory decay rate
  Δt             = time since last access (seconds)
```

This is the same model used for radioactive decay, drug clearance, and capacitor discharge. It has a continuous closed-form — no discretization needed.

### Per-Memory Decay Rate

Not all memories should decay at the same rate. Procedural knowledge (how to configure Proxmox) should decay slowly. Situational awareness (what error appeared in the last session) should decay quickly.

But: we don't assign decay rates based on LLM importance predictions (P1). Instead, decay rates are inferred from behavioral patterns:

```
λ(m) = λ_base × (1 / (1 + access_frequency(m)))

Where:
  λ_base = 0.01 per hour (decays to ~37% in 100 hours ≈ 4 days)
  access_frequency = accesses per day over last 30 days
```

Memories accessed frequently have slower decay. Memories never accessed have the fastest decay. This is behavioral, not predicted.

### Initial Baseline

At write time, activation is set to 1.0 (maximum). At any later read:

```
activation_now = 1.0 × e^(-λ(m) × hours_since_last_access)
```

At retrieval (reinforcement):
```
activation_now += reinforcement_boost   // deepens the energy well
last_accessed = now()                   // resets the Δt clock
```

---

## Implementation

### What Gets Stored in LMDB

Per memory:
```
decay_lambda: float32    // current λ, updated when access_frequency changes
last_accessed: u64       // Unix timestamp (milliseconds)
activation_0: float32    // activation at time of last_accessed
access_count: u64        // total all-time accesses
recent_accesses: u64[]   // timestamps of last N accesses (for frequency calculation)
```

### Read-Time Computation

```rust
fn current_activation(memory_id: Uuid, db: &LmdbDatabase) -> f32 {
    let record = db.get_decay_record(memory_id);
    let delta_hours = (now_ms() - record.last_accessed) as f32 / 3_600_000.0;
    record.activation_0 * (-record.decay_lambda * delta_hours).exp()
}
```

This is pure timestamp arithmetic. No background job. No network call. Microseconds.

### Retrieval Reinforcement Update

```rust
fn reinforce(memory_id: Uuid, db: &mut LmdbDatabase) {
    let record = db.get_decay_record(memory_id);
    let current = current_activation(memory_id, db);

    // Boost activation by reinforcement
    let new_activation = (current + REINFORCEMENT_BOOST).min(1.0);

    // Update decay rate based on new access frequency
    let new_lambda = compute_lambda(record.recent_accesses, record.access_count + 1);

    db.put_decay_record(memory_id, DecayRecord {
        activation_0: new_activation,
        last_accessed: now_ms(),
        decay_lambda: new_lambda,
        access_count: record.access_count + 1,
        recent_accesses: append_and_trim(record.recent_accesses, now_ms()),
    });
}
```

---

## Decay in the Hopfield Layer

In the Hopfield network, decay is expressed as weight matrix decay:

```
W(t) = W(0) × e^(-λ_global × t)
```

But individual memory decay rates can't be represented in a single weight matrix (the matrix is shared). Two approaches:

**Option A: Global decay rate, per-memory activation threshold**
- Apply global decay to weights
- Track per-memory activation in LMDB
- At retrieval, filter results below their individual activation threshold
- Simpler, slight loss of precision in the energy landscape

**Option B: Separate weight matrices per memory**
- Each memory has its own weight slice
- Decay each slice independently
- More accurate, more memory-intensive

**Default**: Option A — global weight decay + LMDB activation thresholds. Revisit if precision is inadequate.

---

## Eviction Policy

When should a memory be removed entirely?

- **Not based on importance score** (P1)
- **Not based on age alone** — a memory that's old but frequently accessed should not be evicted
- **Based on activation level** — when `current_activation(m)` falls below EVICTION_THRESHOLD:
  - Move to cold store archive (if not already there)
  - Remove from Hopfield hot layer
  - Tombstone in CRDT OR-Set
  - Retain LMDB record (for migration and audit)

```
EVICTION_THRESHOLD = 0.05   // ~5% of original activation
```

At λ = 0.01/hour and EVICTION_THRESHOLD = 0.05:
- A never-accessed memory is evicted after ~300 hours (12.5 days)
- A frequently-accessed memory (λ = 0.001/hour) would take ~3000 hours (125 days) to evict

This is automatic. No cron job. No administrator decision. Physics.

---

## Contrast with Recall 1.0

| Recall 1.0 | Recall 2.0 |
|---|---|
| ARQ background worker runs decay on schedule | Decay computed from timestamps at read time |
| Global decay rate for all memories | Per-memory decay rate based on access frequency |
| Decay reduces "importance score" | Decay reduces activation level in Hopfield energy landscape |
| Decayed memories still take up Qdrant space | Decayed memories evicted from Hopfield, archived to cold store |
| Decay can fail if worker crashes | Decay cannot fail — it's arithmetic |
| Decay has timing artifacts | Decay is continuous |
