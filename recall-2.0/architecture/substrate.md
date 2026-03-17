# Storage Substrate — Recall 2.0

The storage layer is not a database. It is a physical substrate where memory dynamics — retrieval, reinforcement, and decay — happen as natural consequences of the substrate's operation, not as separate write calls.

**Last updated**: 2026-03-16

---

## The Core Insight

In Recall 1.0, retrieval, reinforcement, and decay are three separate systems:
- Retrieval: Qdrant ANN search
- Reinforcement: CO_RETRIEVED edges (never wired in)
- Decay: ARQ background worker (scheduled)

This is wrong. In biological memory, these are the same physical process. The substrate for Recall 2.0 must unify them.

**Modern Hopfield Networks** are the closest engineered analog. In a Hopfield network:
- Retrieval = pattern completion (energy minimization dynamics)
- Reinforcement = deepening energy wells around retrieved patterns
- Decay = flattening energy wells over time via weight decay

Three operations. Same substrate. Same physics.

---

## Layer 1: Hopfield Hot Layer

### What It Is
A dense associative memory network. Patterns (memories) are stored as energy wells in a high-dimensional weight matrix. Retrieval is a dynamical process — given a partial cue, the network settles into the nearest stored pattern.

### Why Modern Hopfield, Not Classical
- **Classical Hopfield** (1982): capacity ~0.14N patterns for N neurons, exponential crosstalk at high load
- **Modern Hopfield / Dense Associative Memory** (Ramsauer et al. 2020): capacity scales exponentially with neuron count, uses softmax energy function
- For 22K memories at 1024 dimensions: classical would saturate and produce spurious attractors; modern handles this capacity range

### Storage Formula
```
E(x) = -lse(β, Xᵀx) + ½xᵀx + β⁻¹ log N + ½Mβ

Where:
  x = current state vector (query)
  X = stored patterns matrix (memories)
  β = inverse temperature (sharpness of retrieval)
  N = number of stored patterns
  M = max norm of patterns
```

### Retrieval Dynamics
```
x(t+1) = X · softmax(β · Xᵀ · x(t))
```
One step of this update rule = one retrieval operation. The system converges to the nearest memory in the energy landscape.

### Reinforcement
Increase the energy well depth for retrieved patterns:
```
Δw_ij = η · x_i · x_j  (Hebbian update for retrieved pattern pair)
```
Reinforcement happens as a side effect of retrieval — no separate write call needed.

### Decay
Continuous multiplicative decay on all weights:
```
w_ij(t) = w_ij(0) · e^(-λt)
```
Applied at read time from timestamps — not via background process. Infrequently accessed memories fade from the energy landscape naturally.

### Implementation
- **Runtime**: PyTorch (GPU-accelerated on RTX 3090)
- **Location**: In-process with retrieval engine, OR separate PyTorch service (see OD-02)
- **Precision**: fp16 for the weight matrix (memory efficiency), fp32 for update computations
- **Serialization**: Checkpoint the weight matrix to disk periodically (LMDB or raw mmap file)

### Open Questions
- Online Hebbian updates vs. batch retrain (OD-03)
- Capacity planning: what is the maximum pattern count before spurious attractors become a problem?
- What is the right β (temperature) for this corpus?

---

## Layer 2: LMDB — Metadata and Access Logs

### What It Is
Lightning Memory-Mapped Database. Embedded key-value store with memory-mapped I/O. No server process. Reads are as fast as filesystem reads. Writes are serialized but extremely fast (memory-mapped, no syscall overhead after initial mmap).

### Why LMDB Instead of PostgreSQL
- PostgreSQL is a full RDBMS. Recall 2.0 doesn't need ACID transactions, joins, or a query planner.
- LMDB is faster than SQLite for read-heavy workloads with many concurrent readers.
- LMDB is embedded — no server process to manage, no network overhead.
- LMDB is memory-mapped — reads at filesystem speed, data is always consistent (no cache coherence issues).

### What Gets Stored Here
```
Keys:                           Values:
memory:{uuid}                   MemoryRecord (text, metadata, embedding hash)
access:{uuid}:{timestamp}       AccessEvent (session_id, context_hash)
session:{uuid}                  SessionRecord (start, end, summary_hash)
crdt:state:{key}                CRDTValue (serialized CRDT)
decay:params:{uuid}             DecayParams (λ, last_accessed)
coretrieval:{uuid}:{uuid}       CoRetrievalCount (integer counter)
```

### Rust Binding
- Crate: `heed` (safe Rust bindings for LMDB)
- One environment, multiple named databases (namespaces)
- LMDB supports multiple concurrent readers, single writer — fits the access pattern

### Schema Design
- All keys are byte strings. Use fixed prefixes for namespace isolation.
- Values are MessagePack-encoded structs (compact, fast, schema-optional).
- No foreign keys. Denormalized by design. Joins are application logic.

---

## Layer 3: Cold Vector Store

### Purpose
Full-corpus ANN search for semantic fallback when the Hopfield hot layer doesn't have a confident match. The cold store is the slow path — queried last, after session cache → LLPC working set → Hopfield hot layer.

### Current Candidate: Qdrant
- Pros: Tim knows it, it's maintained, it has filtering support, it's already running
- Cons: Not designed for this use case, no reinforcement semantics, another server to run

### Alternative: Custom HNSW in LMDB
- Build a Hierarchical Navigable Small World graph directly on top of LMDB
- No separate server, same embedded architecture as the rest of the substrate
- More complex to build, but eliminates the Qdrant dependency

### Alternative: Hopfield Handles Everything (No Cold Store)
- If the Hopfield hot layer can reliably store all 22K+ memories, cold store is unnecessary
- Requires resolving OD-01 (Hopfield capacity at corpus scale)

### Decision Pending
See OD-01. The cold store decision depends on empirical capacity testing of the Hopfield layer.

---

## Layer 4: CRDT State

### Purpose
Multi-machine consistency for the casaclaude and proxyclaude machines writing concurrently. CRDTs guarantee convergence without coordination protocols.

### Data Types Required

| Memory Operation | CRDT Type | Semantics |
|---|---|---|
| Memory collection | OR-Set | Add operations commute, delete tombstones prevent re-add |
| Access frequency | G-Counter | Increment-only, merge by taking max of each replica |
| Memory content | LWW-Register | Last-writer-wins on content field (timestamp is wall clock) |
| Co-retrieval count | G-Counter | Increment per co-retrieval event, merge by max |

### Implementation
- Crate: `crdts` (Rust)
- CRDT state persisted in LMDB under `crdt:*` key prefix
- Sync: CRDT deltas exchanged when machines are on same network
- Conflict resolution: mathematical property of the CRDT type — no application logic needed

### Known Edge Cases (OD-04)
- Two machines write same memory with slightly different content simultaneously → LWW-Register takes latest timestamp, content from that machine wins
- Memory deleted on one machine while accessed on another → OR-Set: delete tombstone propagates, access event on dead memory → no-op
- Access count incremented on both machines → G-Counter: merge takes max per replica → correct

---

## Substrate Invariants

These must hold at all times:

1. **No write to cold store without passing through Hopfield** — hot layer is always primary
2. **LMDB is the source of truth for metadata** — Hopfield weights are a cache, LMDB is durable
3. **Decay is never applied by a background job** — always computed from LMDB timestamps at read time
4. **CRDT state must converge** — any pair of replicas, given the same events in any order, must reach the same state
5. **No importance scores stored anywhere in the substrate** — not in LMDB, not in Hopfield, not in cold store
