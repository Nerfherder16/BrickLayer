# Reminisce — Prior Art Analysis

**Status**: Reference document — revisit before major architecture decisions
**Last updated**: 2026-03-16
**Context**: Reminisce (ReminisceDB) was a prior attempt to rewrite Recall in Rust as a single-binary commercial memory engine. It was abandoned before shipping. This document captures what it got right, what it got wrong, and what carries forward to Recall 2.0.

---

## The Core Finding

Reminisce is approximately 65% of the correct architecture for Recall 2.0. The commercial infrastructure decisions are correct. The retrieval quality decisions need replacing.

**The commercial infrastructure Reminisce got right:**
- Single Rust binary (homelab + enterprise distribution)
- JWT auth + Argon2 password hashing
- Multi-tenant key isolation (`{user_id}:{memory_id}` prefix on every key)
- Stripe integration (stripe_customer_id, stripe_subscription_id, memory_limit enforced at write time)
- AWS KMS + AES-256-GCM (two-tier key management: local key for homelab, KMS for enterprise)
- CCPA compliance (profiling_opted_out flag, FIFO-compacted audit log)
- RocksDB 14-column-family schema (reasonable for multi-tenant isolation, per-CF tuning)

**The retrieval quality decisions Reminisce got wrong:**
- `score_memory()` uses `memory.importance` at 35% weight — P1 violation
- Two scheduled decay workers — P3 violation
- Brute-force DashMap vector index (TODO to swap for usearch, never happened — ships past stated 5K limit)

---

## What Reminisce Built: The Keeper Components

### Token-Level Buffer (TLB)
64-entry per-user LRU cosine pre-scan. Returns immediately if top_score ≥ 0.75 AND count ≥ min(limit, 3), before any HNSW or BM25 search. Recall 1.0 hits Qdrant on every single retrieval — no session-warm cache. TLB is the proof-of-concept for Recall 2.0's LLPC. The only difference: Recall 2.0's LLPC uses behavioral scoring (access frequency + recency + co-retrieval density) instead of LRU eviction. Behavioral scoring is strictly better. The concept is proven.

### QueryIntent Routing (6 classes)
- `TemporalCurrent` (recency_weight=0.9, candidate_multiplier=1.5)
- `TemporalHistorical` (recency_weight=0.3, candidate_multiplier=2.0)
- `Procedural` (recency_weight=0.5, candidate_multiplier=1.2)
- `Preference` (recency_weight=0.4, candidate_multiplier=1.0)
- `Factual` (recency_weight=0.2, candidate_multiplier=1.0)
- `General` (recency_weight=0.5, candidate_multiplier=1.0)

Recall 1.0 treats every query identically. Recall 2.0's retrieval routing (F-RT-04) should answer this with Reminisce's taxonomy as the baseline. The classifier ran from the query string alone — no separate model needed.

### MemoryCategory Half-Lives (per-memory λ base rates)
```
Infrastructure    = 14 days
ProjectContext    = 30 days
Architectural     = 90 days
CodingStyle       = 180 days
PersonalFact      = 365 days
Permanent         = no decay
```
These are category-level priors on decay rate. This is defensible and P1-compliant — it's not predicting future retrieval value (importance scoring), it's acknowledging that IP addresses go stale faster than coding preferences. Recall 2.0's per-memory λ formula should start from these base rates and adjust based on behavioral signals (access frequency, recency).

### RelationType Taxonomy (23 typed edges with decay multipliers)
```
DecidedBecause    (strength=0.8, decay_multiplier=0.9)
CausedBy          (strength=0.7, decay_multiplier=0.9)
Supersedes        (strength=0.9, decay_multiplier=0.85)
Contradicts       (strength=0.6, decay_multiplier=0.95)
AttemptedBefore   (strength=0.5, decay_multiplier=0.9)
RevertedDue       (strength=0.6, decay_multiplier=0.9)
Uses              (strength=0.5, decay_multiplier=1.0)
DeployedOn        (strength=0.7, decay_multiplier=0.9)
DependsOn         (strength=0.6, decay_multiplier=0.95)
... (23 types total)
```
Recall 1.0's Neo4j graph uses generic relationship types — everything decays the same, no semantic weight. These 23 types with decay multipliers are validated by 16K imported memories. Contradicts edges persist longer (0.95 multiplier) than Uses edges (1.0 = fastest decay). This is the right model. Copy the taxonomy into Recall 2.0's behavioral graph design before that architecture closes.

### SourceTrust (P1-compliant provenance weighting)
```
UserDirect      = 0.9 initial trust weight
VerifiedSystem  = 0.8
ToolOutput      = 0.5
AgentGenerated  = 0.4
```
This is NOT importance scoring. It's a write-time prior on source reliability, not predicted retrieval value. P1-compliant. Recall 1.0 and Recall 2.0's current write-path design don't have this. It's a gap. Add SourceTrust to the write path, store it in LMDB metadata, weight behavioral scores at retrieval time by source trust.

### Bi-temporal Validity
`valid_from`/`valid_until` (event time) + `stored_at`/`retired_at` (transaction time). Enables "what did I know about X on date Y?" — impossible in Recall 1.0's flat timestamp model. Reminisce's migration code correctly sets `stored_at` from the original Recall memory timestamp. This is the answer to Recall 2.0's provenance unknown (U-16).

### Migration Tooling
`src/migration/recall.rs` hits `/admin/export?include_superseded=true` JSONL endpoint and maps Recall memories to Reminisce MemoryInput. The migration path exists and was used (16K memories imported). Recall 2.0 needs the same pattern: read Recall 1.0's export, re-ingest into the new substrate. The code is the template.

### ACT-R Activation Formula (correct formula, wrong execution timing)
```
A_i = ln(Σ t_j^(-d))
```
Where t_j = elapsed seconds since j-th retrieval, d = decay rate. This is the cognitive science decay model from Carnegie Mellon's ACT-R theory. The formula is correct and close to Recall 2.0's exponential decay model. The problem: Reminisce runs it in a scheduled background worker (P3 violation). Move it to read-time and it's fully P3-compliant.

---

## What Reminisce Got Wrong

### P1 Violation: `score_memory()` importance weighting
```rust
let base_score = 0.35 * importance_normalized
              + 0.25 * confidence
              + 0.15 * activation
              + 0.15 * trust_weight
              + 0.05 * recency
              + 0.05 * source_bonus;
```
Importance is 35% of the retrieval score — the single largest factor. Despite having ACT-R activation, the scoring still centers on a write-time prior about future retrieval value. This is exactly what P1 prohibits. Recall 2.0's activation-only scoring (via Hopfield) is the fix. This is the core product differentiator: mem0, Zep, MemGPT all do importance scoring. Behavioral scoring is the moat.

### P3 Violation: Two scheduled decay workers
- `DecayWorker.run_pass()` — computes ACT-R activation on a timer, retires memories below threshold=-2.0
- A second `run_once()` — importance-based category decay, runs every 6 hours

Both run on timers. At 10K users, 20K background workers. Read-time decay (timestamp arithmetic at retrieval) requires zero background workers, always consistent, scales trivially.

### The vector index never graduated from Phase 1
`src/storage/hnsw.rs` is a brute-force `DashMap<u64, (Vec<f32>, f32)>` linear scan. Comment: "Phase 1 implementation: sufficient for <5000 vectors." At 16K memories imported, already past the stated threshold. The TODO to swap for `usearch (ScalarKind::F16)` was never completed. At 22K vectors this is ~90ms per retrieval (linear scan on float32). At 100K enterprise users with 22K memories each, catastrophic.

---

## The Scope Reframe

Reminisce started as a commercial product: Stripe, JWT, KMS, CCPA, multi-tenancy. This was the right call. Recall 2.0 follows the same commercial trajectory:

**Self-hosted free**: single binary, local key, community support
**Self-hosted pro**: Stripe billing, advanced consolidation, commercial license
**Cloud SaaS**: managed infrastructure, KMS, multi-region, SLA
**Enterprise**: SSO, audit log, compliance exports, dedicated support

The Gitea/Bitwarden/Outline model: open source self-hosted builds community and trust, cloud converts some percentage to paying customers, enterprise licenses for regulated industries.

**Architectural implication**: Every feature must work self-hosted. No cloud-only features. The cloud tier is managed infrastructure, not feature gating.

---

## Component-Level Carry-Forward Table

| Reminisce Component | Verdict | Action for Recall 2.0 |
|---|---|---|
| Single Rust binary | Correct | Yes — distribution strategy |
| JWT auth + Argon2 | Correct | Yes — copy directly |
| Multi-tenant key isolation | Correct | Yes — `{user_id}:` prefix on all keys |
| Stripe integration | Correct | Yes — metered billing model |
| AWS KMS + AES-256-GCM | Correct | Yes — two-tier key management |
| CCPA + FIFO audit log | Correct | Yes — compliance requirement |
| SourceTrust write-path annotation | Correct | Yes — add to Recall 2.0 write path |
| RelationType taxonomy (23 types) | Correct | Yes — copy and extend |
| MemoryCategory half-lives | Correct | Yes — as λ base rates in decay model |
| QueryIntent routing (6 classes) | Correct | Yes — extend with Recall 2.0 tier routing |
| TLB / LLPC concept | Correct | Yes — behavioral scoring instead of LRU |
| Bi-temporal validity | Correct | Yes — provenance answer |
| ACT-R formula | Correct formula, wrong timing | Yes — move to read-time |
| Migration tooling | Correct | Yes — retarget to Recall 2.0 substrate |
| 14-CF RocksDB schema | Viable | Evaluate vs LMDB + Hopfield at scale |
| `score_memory()` importance weighting | Wrong (P1) | Replace with behavioral scoring |
| Scheduled decay workers | Wrong (P3) | Replace with read-time computation |
| Brute-force DashMap vector index | Wrong | Replace with HNSW or Hopfield |

---

## What Neither System Has Yet

1. **CRDT sync for multi-instance deployment** — Enterprise Recall 2.0 runs N instances. OR-Set + LWW-Register + G-Counter for eventual consistency without coordination. Neither Recall 1.0 nor Reminisce has this.

2. **Consolidation as a product feature** — Reminisce has a consolidation worker but it's not customer-facing. "Your memory system learns from your patterns" is the product story. Needs a UI, user control, and quality metrics.

3. **Health dashboard as customer-facing ROI signal** — The retrieval quality metrics (tier distribution, reinforcement rate, behavioral graph density) are the "Recall is getting smarter" dashboard that enterprise customers pay for. Neither system surfaces this to users.

4. **Portability beyond Linux/RTX 3090** — `fastembed-rs` (Reminisce's optional ONNX dependency) is the right direction: embedded model inference without Ollama. Mac mini in a small office shouldn't need a separate GPU server.

---

## When to Revisit This Document

- Before finalizing the storage substrate (Hopfield vs RocksDB+HNSW)
- Before designing the write path (SourceTrust placement)
- Before designing the behavioral graph (RelationType taxonomy choice)
- Before designing the deployment model (single binary packaging)
- Before the commercial tier partition decision
- Before the migration plan from Recall 1.0
