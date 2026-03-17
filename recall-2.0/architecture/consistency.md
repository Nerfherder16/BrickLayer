# Multi-Machine Consistency — Recall 2.0

P4: consistency without coordination. CRDTs make conflict resolution a mathematical property of the data structure — not application logic, not a coordination protocol.

**Last updated**: 2026-03-16

---

## The Setup

Two machines write to Recall simultaneously:
- **casaclaude**: 192.168.50.19 — primary workstation, Docker host
- **proxyclaude**: separate machine, also running Claude Code

Both machines hook into Recall on PostToolUse and Stop events. Both generate memories. Both need to see each other's memories.

Recall 1.0 handles this with idempotency keys — duplicate writes from different machines are detected by UUID. This is necessary but not sufficient: it handles exact duplicates, not concurrent modifications to the same memory.

---

## Why Not Traditional Distributed Consistency

**Master/replica**: One machine is primary, the other is secondary. Writes go to primary, replicate to secondary. Problem: if primary is unreachable, casaclaude can't write memories while it's away from the homelab network. Not acceptable for a personal memory system.

**Two-phase commit (2PC)**: Both machines must agree before any write commits. Problem: if proxyclaude is unreachable, no writes can proceed anywhere. Worse.

**Vector clocks**: Track causal ordering of writes. Detect conflicts. Surface them for manual resolution. Problem: conflicts require human intervention. Memory systems generate many writes. Manual resolution is not viable.

**CRDTs**: Data structures that always converge to the same state regardless of write order, without coordination. Conflicts are mathematically impossible for the chosen data types. This is the correct answer.

---

## CRDT Type Selection

### Memory Collection: OR-Set (Observed-Remove Set)

An OR-Set supports add and remove operations where:
- `add(element)` tags the element with a unique token
- `remove(element)` removes all tags for that element
- Two sets merge by taking the union of all tags, minus removed tags
- If the same element is added on two machines and removed on one, the add from the non-removing machine wins (observed adds beat removes)

```rust
struct MemoryOrSet {
    // Each memory has a set of unique "add tokens"
    // A memory exists if it has at least one token
    // A memory is deleted if all its tokens have been removed
    adds: HashMap<MemoryId, HashSet<Token>>,
    removes: HashMap<MemoryId, HashSet<Token>>,
}

impl MemoryOrSet {
    fn add(&mut self, memory_id: MemoryId) -> Token {
        let token = Token::new_unique();  // UUID
        self.adds.entry(memory_id).or_default().insert(token);
        token
    }

    fn remove(&mut self, memory_id: MemoryId, tokens: HashSet<Token>) {
        self.removes.entry(memory_id).or_default().extend(tokens);
    }

    fn contains(&self, memory_id: &MemoryId) -> bool {
        let add_tokens = self.adds.get(memory_id).map(|t| t.clone()).unwrap_or_default();
        let remove_tokens = self.removes.get(memory_id).map(|t| t.clone()).unwrap_or_default();
        !add_tokens.is_subset(&remove_tokens)
    }

    fn merge(&mut self, other: &MemoryOrSet) {
        // Merge adds: union of all tokens
        for (id, tokens) in &other.adds {
            self.adds.entry(*id).or_default().extend(tokens);
        }
        // Merge removes: union of all remove tokens
        for (id, tokens) in &other.removes {
            self.removes.entry(*id).or_default().extend(tokens);
        }
    }
}
```

### Memory Content: LWW-Register (Last-Write-Wins Register)

For the content of a memory (the text itself), LWW semantics: the most recent write wins.

```rust
struct LwwRegister<T> {
    value: T,
    timestamp: HybridLogicalClock,  // HLC, not wall clock — monotonic, not susceptible to clock skew
    replica_id: ReplicaId,           // tiebreaker when timestamps are equal
}

impl<T: Clone> LwwRegister<T> {
    fn set(&mut self, value: T, ts: HybridLogicalClock, replica_id: ReplicaId) {
        if ts > self.timestamp || (ts == self.timestamp && replica_id > self.replica_id) {
            self.value = value;
            self.timestamp = ts;
            self.replica_id = replica_id;
        }
    }

    fn merge(&mut self, other: &LwwRegister<T>) {
        self.set(other.value.clone(), other.timestamp, other.replica_id);
    }
}
```

**Hybrid Logical Clock (HLC)**: Wall clock + logical counter. Advances with wall clock but guarantees monotonicity even when wall clock skews backward. Better than pure wall clock for LWW.

### Access Frequency: G-Counter (Grow-Only Counter)

Access count should only increase. G-Counter: each replica maintains its own counter, merge by taking the max per replica.

```rust
struct GCounter {
    counts: HashMap<ReplicaId, u64>,
}

impl GCounter {
    fn increment(&mut self, replica_id: ReplicaId) {
        *self.counts.entry(replica_id).or_default() += 1;
    }

    fn total(&self) -> u64 {
        self.counts.values().sum()
    }

    fn merge(&mut self, other: &GCounter) {
        for (replica_id, count) in &other.counts {
            let local = self.counts.entry(*replica_id).or_default();
            *local = (*local).max(*count);
        }
    }
}
```

### Co-Retrieval Count: G-Counter

Same as access frequency. Co-retrieval counts per memory pair only increase.

---

## Sync Protocol

CRDTs don't require a sync protocol — but they do need deltas to propagate between replicas.

### When Sync Happens
- On network reconnect (machines back on same network)
- Periodic background sync when both machines reachable (every N minutes)
- On-demand via explicit sync command

### What Gets Synced

CRDT state deltas, not full state:

```
casaclaude → proxyclaude:
  {
    "or_set_delta": { adds: {...new adds since last sync}, removes: {...} },
    "lww_deltas": { memory_id: { value, timestamp, replica_id }, ... },
    "gcounter_deltas": { memory_id: { counts: {casaclaude_id: 5} }, ... },
    "since": HLC timestamp
  }
```

Both sides apply the delta and respond with their own delta since the peer's last known state.

### Conflict Free by Construction

There are no conflicts in this model. LWW-Register: latest timestamp wins — both replicas converge to the same content after exchange. OR-Set: union of all adds and removes — both converge. G-Counter: max per replica — both converge.

The only "conflict" is semantic: two machines write slightly different content for what should be the same memory at the same time. LWW resolves this by timestamp — one version wins. The losing version is gone. This is acceptable for a personal memory system where the human is the same person on both machines.

---

## Open Questions (OD-04)

1. **LWW content conflict**: casaclaude writes "The RTX 3090 is at 192.168.50.62" and proxyclaude writes "The RTX 3090 is at 192.168.50.63" within the same millisecond. LWW resolves by replica_id tiebreaker — one machine always wins. Is this semantically correct? What if both IPs were correct at different points in time?

2. **Delete-then-add race**: Memory deleted on casaclaude while proxyclaude is reading it. OR-Set handles this: delete tombstone propagates, read on proxyclaude returns the memory until the tombstone arrives. This is eventual consistency — is eventual consistency correct for memory operations?

3. **Abstraction invalidation**: Consolidation on casaclaude generates an abstraction from 5 source memories. Meanwhile, proxyclaude deletes two of those source memories. When CRDT state syncs, the abstraction now has two invalid source links. How should the system handle dangling abstraction links?

---

## Rust Implementation

- Crate: `crdts` (provides G-Counter, OR-Set, LWW-Register, Map)
- HLC: `hybrid-logical-clock` crate, or implement from the Kulkarni-Demirbas paper
- Serialization: `serde` + `bincode` for compact CRDT state
- LMDB persistence: CRDT state written to LMDB under `crdt:*` prefix after each local operation
