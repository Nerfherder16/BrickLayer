# Write Path — Recall 2.0

The path a memory takes from Claude's context to durable storage. Must be fast enough to not add perceptible latency to the hook that calls it.

**Last updated**: 2026-03-16

---

## Design Constraints

- **Latency budget**: < 200ms total from hook call to acknowledgement (embedding is the bottleneck)
- **Durability**: acknowledged memories must survive process restart
- **Deduplication**: same memory must not be stored twice across machines or sessions
- **Concurrency**: casaclaude and proxyclaude may write simultaneously

---

## Write Pipeline: Three-Layer Deduplication

```
Hook (observe-edit.js / session-end)
     │
     ▼
┌────────────────────────────────────────────┐
│  L0: Exact Hash Check                      │
│  SHA-256 of normalized text                │
│  Cost: ~1ms (LMDB lookup)                  │
│  Action: REJECT if hash already exists     │
└──────────────────────┬─────────────────────┘
                       │ PASS
                       ▼
┌────────────────────────────────────────────┐
│  L1: Near-Duplicate Check                  │
│  SimHash (locality-sensitive hash)         │
│  Hamming distance threshold: ≤ 3 bits      │
│  Cost: ~5ms (SimHash compute + LMDB scan)  │
│  Action: REJECT if near-duplicate found    │
└──────────────────────┬─────────────────────┘
                       │ PASS
                       ▼
┌────────────────────────────────────────────┐
│  Embedding Inference                       │
│  qwen3-embedding:0.6b via Ollama           │
│  Cost: ~100-150ms (GPU, RTX 3090)          │
│  Output: 1024-dim float vector             │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│  L2: Semantic Duplicate Check              │
│  ANN search in Hopfield / cold store       │
│  Cosine similarity threshold: ≥ 0.97       │
│  Cost: ~10-20ms (Hopfield lookup)          │
│  Action: REJECT if semantically identical  │
└──────────────────────┬─────────────────────┘
                       │ PASS
                       ▼
┌────────────────────────────────────────────┐
│  CRDT Write                                │
│  OR-Set.add(memory_id)                     │
│  LWW-Register.set(content, timestamp)      │
│  Cost: ~1ms                                │
└──────────────────────┬─────────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
┌─────────────────────┐  ┌─────────────────────┐
│  Hopfield Write     │  │  LMDB Write          │
│  Update weight      │  │  memory record       │
│  matrix with new    │  │  access log init     │
│  pattern            │  │  SimHash index       │
│  Cost: ~5ms         │  │  Cost: ~2ms          │
└─────────────────────┘  └─────────────────────┘
              │
              ▼ (async, non-blocking)
┌─────────────────────┐
│  Cold Store Write   │
│  (Qdrant or custom) │
│  Cost: ~20ms        │
│  Does not block ACK │
└─────────────────────┘
              │
              ▼
         ACK to hook
         (< 200ms total)
```

---

## L0: Exact Hash Check

```rust
fn l0_check(text: &str, db: &LmdbDatabase) -> DedupResult {
    let normalized = normalize(text);  // lowercase, strip whitespace, canonical unicode
    let hash = sha256(&normalized);

    match db.get(&format!("hash:{}", hash)) {
        Some(_) => DedupResult::Reject(DedupReason::ExactDuplicate),
        None => {
            db.put(&format!("hash:{}", hash), &memory_id);
            DedupResult::Pass
        }
    }
}
```

**Normalization**: lowercase, unicode NFC, collapse whitespace, strip leading/trailing. The goal is to catch "The server is down" and "the server is down." as the same memory.

---

## L1: Near-Duplicate Check (SimHash)

SimHash maps variable-length text to a fixed-length fingerprint where similar texts have fingerprints with low Hamming distance.

```rust
fn l1_check(text: &str, db: &LmdbDatabase) -> DedupResult {
    let fingerprint = simhash64(text);

    // Check all stored SimHashes for Hamming distance ≤ 3
    // In practice: use banding technique to avoid full scan
    // 64-bit hash → 4 bands of 16 bits → only check band matches
    for band_index in 0..4 {
        let band = extract_band(fingerprint, band_index);
        let candidates = db.get_by_band(band_index, band);
        for candidate_fp in candidates {
            if hamming_distance(fingerprint, candidate_fp) <= 3 {
                return DedupResult::Reject(DedupReason::NearDuplicate);
            }
        }
    }

    db.store_simhash(fingerprint, &memory_id);
    DedupResult::Pass
}
```

**Threshold**: ≤ 3 bits Hamming distance on a 64-bit hash ≈ 95% similarity. Tunable.

---

## L2: Semantic Duplicate Check

Requires embedding — happens after embedding inference.

```rust
fn l2_check(embedding: &[f32], hopfield: &HopfieldLayer) -> DedupResult {
    let (nearest, similarity) = hopfield.nearest_neighbor(embedding);

    if similarity >= 0.97 {
        return DedupResult::Reject(DedupReason::SemanticDuplicate { existing: nearest });
    }

    DedupResult::Pass
}
```

**Threshold**: 0.97 cosine similarity. Memories above this threshold are essentially the same memory stated differently. Tunable — may need calibration on the actual corpus.

---

## CRDT Write

```rust
fn crdt_write(memory: &Memory, crdt_state: &mut CrdtState) {
    // Add to OR-Set (handles concurrent adds and deletes)
    crdt_state.memory_set.add(memory.id, memory.created_at);

    // Set content with LWW semantics
    crdt_state.content_register.set(memory.id, memory.content, now());

    // Initialize G-Counter for access frequency
    crdt_state.access_counters.init(memory.id);

    // Persist CRDT state to LMDB
    crdt_state.flush_to_lmdb();
}
```

---

## Async Cold Store Write

The cold store write is non-blocking. The hook acknowledgement is sent before cold store write completes.

```rust
fn write_memory(memory: Memory) -> WriteResult {
    // Synchronous: dedup, embed, Hopfield, LMDB
    let result = synchronous_write_pipeline(&memory)?;

    // Async: cold store (non-blocking)
    tokio::spawn(async move {
        cold_store.write(&memory).await;
    });

    Ok(result)  // ACK returned before cold store write
}
```

Cold store write failures are retried with exponential backoff. They are not surfaced to the hook caller — the memory is already durable in LMDB and Hopfield.

---

## Write Path Latency Budget

| Stage | Target | Notes |
|---|---|---|
| L0 hash check | < 2ms | LMDB read, near-instant |
| L1 SimHash check | < 5ms | Compute + banded scan |
| Embedding inference | < 150ms | GPU bottleneck, dominates |
| L2 semantic check | < 20ms | Hopfield lookup |
| CRDT write | < 2ms | LMDB write |
| Hopfield write | < 5ms | Weight matrix update |
| LMDB record write | < 2ms | Memory-mapped |
| **Total (sync)** | **< 186ms** | Before cold store write |
| Cold store write | ~20ms | Async, non-blocking |

---

## What Gets Written

Each memory record in LMDB:
```
{
  id: UUID,
  text: string,
  embedding: float[1024],          // or just the hash if embedding stored in cold store
  embedding_model: string,         // model version used (for re-embedding detection)
  source: "edit" | "session" | "manual",
  session_id: UUID,
  created_at: timestamp,
  l0_hash: bytes[32],             // SHA-256 of normalized text
  l1_hash: uint64,                // SimHash fingerprint
  tags: string[],                 // extracted by hook, not LLM
  decay_lambda: float,            // initial decay rate (uniform for now)
}
```

---

## What Is NOT Written

- **Importance scores** — never
- **Priority rankings** — never
- **LLM-assigned relevance weights** — never
- **Predicted future access frequency** — never

The system learns relevance from demonstrated behavior, not predicted behavior.
