# Known Unknowns — Recall 2.0

Things we know we don't know. This file tracks the open questions that must be resolved before or during implementation — through research, experimentation, or decision.

Add freely. Move entries to `decisions/decided.md` when resolved.

**Last updated**: 2026-03-16

---

## Substrate Unknowns

### U-01: Hopfield Capacity at 22K+ Memories
**Question**: Modern Hopfield Networks claim exponential storage capacity. What does that actually mean at 22,423 memories × 1024 dimensions?

**Why it matters**: If capacity is insufficient, spurious attractors dominate retrieval and the hot layer becomes unreliable. This would require a hybrid approach (Hopfield for working set, cold ANN for full corpus).

**How to resolve**: Empirical test. Implement a minimal Hopfield layer, load 22K+ random embeddings of the correct dimensionality, measure spurious attractor rate under various query conditions.

**Blocking**: OD-01 (cold store decision), OD-03 (online learning decision)

---

### U-02: Online Hebbian Update Interference Rate
**Question**: What is the interference cost of online Hebbian updates on a Hopfield network at 22K+ patterns?

**Why it matters**: Batch retraining on a schedule means memories are "unlearned" (partially) and re-learned with each batch. Online updates avoid staleness but may cause catastrophic interference where new patterns overwrite old ones.

**How to resolve**: Empirical — measure retrieval precision before/after N online updates. Compare to baseline batch retrain.

**Related**: U-01, OD-03

---

### U-03: The Right β (Temperature) for This Corpus
**Question**: In the Modern Hopfield update rule, β controls the sharpness of pattern retrieval. What value is correct for the Recall 2.0 corpus?

**Why it matters**: High β → sharp retrieval (one pattern dominates), risk of missing related patterns. Low β → soft retrieval (many patterns contribute), risk of diffuse results. The right value depends on the embedding distribution and corpus structure.

**How to resolve**: Grid search β over {0.1, 0.5, 1.0, 2.0, 5.0, 10.0} on a sample retrieval task with known correct answers.

---

### U-04: SimHash Collision Rate on Real Memory Text
**Question**: What is the false-positive rate (near-duplicate detected when memories are actually distinct) for SimHash at Hamming distance ≤ 3 on real Recall text?

**Why it matters**: A too-aggressive SimHash threshold causes real memories to be rejected as duplicates. Too permissive causes redundant memories to accumulate.

**How to resolve**: Run SimHash at various thresholds on the existing 22K Recall 1.0 memories. Manually evaluate false positives and false negatives on a sample.

---

### U-05: Embedding Drift
**Question**: If the embedding model is upgraded (e.g., qwen3-embedding:0.6b → a newer model), all existing embeddings become incompatible with new ones. How should the system handle embedding model drift?

**Why it matters**: All retrieval depends on embeddings living in the same vector space. A model upgrade without re-embedding everything corrupts retrieval.

**How to resolve**: Three options:
1. Never upgrade embedding model (brittle)
2. Re-embed everything on upgrade (expensive but clean)
3. Maintain separate embedding spaces with a routing layer (complex)

This needs a decision before production use.

---

## Retrieval Unknowns

### U-06: Injection Format Impact on Claude's Behavior
**Question**: Does the format of memory injection (XML vs Markdown vs plain text) actually change how well Claude uses the memories?

**Why it matters**: The injection format is the final interface between the memory system and Claude's reasoning. If Claude ignores structured formats or treats all formats identically, format optimization is wasted effort.

**How to resolve**: A/B test. Same memories, different formats, measured by: does Claude's response incorporate the relevant memory or ignore it? Manual evaluation on a sample of sessions.

---

### U-07: Context Position Effect
**Question**: Does injecting memories closer to the user's question vs. at the top of context change recall/utilization by Claude?

**Why it matters**: Research on "lost in the middle" effects in LLMs suggests middle-context content is underweighted. If memories injected at the top are less used, injection position should change.

**How to resolve**: Controlled experiment — same memories, same queries, measure Claude's response quality with memories at position 0 vs. immediately before the user message.

---

### U-08: LLPC Optimal Size
**Question**: What is the right number of memories in the LLPC working set (the behavioral pre-cache before Hopfield)?

**Why it matters**: LLPC too large → bloom filter false positive rate too high, LLPC scan too slow. LLPC too small → behavioral working set misses, Hopfield queries more expensive.

**How to resolve**: Empirical — simulate retrieval patterns with LLPC sizes of 50, 100, 250, 500, 1000. Measure cache hit rate and latency.

---

### U-09: Consolidation Idle Threshold
**Question**: What is the right idle duration threshold to trigger background consolidation?

**Options considered**:
- 2 minutes: May trigger during brief pauses in active sessions
- 5 minutes: Reasonable default
- 15 minutes: Conservative, consolidation only runs during genuine idle periods
- 30 minutes: May not run often enough during active use days

**Why it matters**: Too short → consolidation competes with retrieval. Too long → abstractions lag behind reality.

**How to resolve**: Instrument the system, measure actual idle period distribution in Tim's usage, pick threshold that catches most idle periods without over-triggering.

---

## Consistency Unknowns

### U-10: LWW Timestamp Reliability
**Question**: casaclaude and proxyclaude clocks may drift. How much clock drift can the LWW-Register tolerate before producing semantically wrong results?

**Why it matters**: LWW picks the winner by timestamp. Clock skew means the "later" write by wall clock may not be the causally later write. Hybrid Logical Clocks reduce but don't eliminate this risk.

**How to resolve**: Measure actual clock skew between the two machines over time. Determine if HLC is sufficient or if NTP synchronization requirements are needed.

---

### U-11: OR-Set Tombstone Accumulation
**Question**: OR-Set tombstones (delete records) accumulate forever — a deleted memory's tombstone lives in the CRDT state indefinitely. At 22K+ memories with some deletion rate, how large does tombstone accumulation get?

**Why it matters**: Tombstone bloat increases CRDT state size, sync delta size, and merge time.

**How to resolve**: Model based on expected deletion rate. Implement tombstone compaction if needed (safe window: tombstones older than max-sync-delay can be collected).

---

## Migration Unknowns

### U-12: Recall 1.0 Embedding Compatibility
**Question**: All 22,423 Recall 1.0 memories are embedded with qwen3-embedding:0.6b at 1024 dimensions. Will these embeddings work directly in the Recall 2.0 Hopfield layer, or do they need re-embedding?

**Why it matters**: Re-embedding 22K memories takes significant time and GPU resources. If compatible, migration is much simpler.

**How to resolve**: Load a sample of 1.0 embeddings into the Hopfield layer and test retrieval precision. If precision is adequate, embeddings are compatible.

---

### U-13: Neo4j Behavioral Graph Migration
**Question**: Recall 1.0's Neo4j store has RELATED_TO edges between memories, but no CO_RETRIEVED edges (they were never wired in). What value, if any, can be extracted from the Neo4j graph for migration to the Recall 2.0 behavioral model?

**Why it matters**: The Neo4j graph represents months of relationship inference. If salvageable, it provides a behavioral graph head start.

**How to resolve**: Audit the actual Neo4j schema. Count RELATED_TO edges, assess their density and quality. Determine if they map to co-retrieval semantics.

---

## Dimension Unknowns

### U-14: Multi-Modal Memory
**Question**: Recall 1.0 stores text. Claude Code increasingly works with images, code, and structured data. Should Recall 2.0 support multi-modal memories?

**Options**:
- A: Text only — normalize everything to text before storage
- B: Code as a separate memory type with code-specific embeddings (code2vec, CodeBERT)
- C: Full multi-modal (image embeddings, code embeddings, text embeddings — separate Hopfield layers)

**Why it matters**: Code memories stored as text lose structural information. A bug fix in a specific function is different from a general comment about a file.

**Blocking on**: U-05 (embedding model selection), OD-05 (embedding model choice)

---

### U-15: Memory Provenance and Audit
**Question**: Should memories be traceable to their source — which session, which tool use, which specific edit triggered the memory?

**Why it matters**: When Claude retrieves a memory and acts on it, knowing where it came from enables auditing incorrect memories and improving the observe-edit hook.

**Current state**: Recall 1.0 stores session_id but not specific tool use provenance.

---

### U-16: Memory Confidence and Uncertainty
**Question**: Some memories are highly reliable (Tim's homelab IP addresses). Others are best-guesses (inferred patterns from partial information). Should Recall 2.0 represent memory confidence?

**Why it matters**: Claude acting on a low-confidence memory as if it's ground truth is dangerous. Surface confidence, and Claude can hedge appropriately.

**Related**: Contradictions surfacing in `architecture/health.md`. This extends to single-memory confidence, not just conflicts.

---

### U-17: Memory Scope and Isolation
**Question**: Are all memories global across all projects, or should memories be scoped to project contexts?

**Why it matters**: "The API endpoint is /api/v1/users" is only true within the context of a specific project. Retrieved in a different project context, it could be misleading.

**Current state**: Recall 1.0 stores project tags but retrieval doesn't enforce project isolation.

---

### U-18: Forgetting by Intent
**Question**: Should users be able to intentionally delete specific memories? What is the UX for this?

**Current state**: There's no intentional delete flow in Recall 1.0. The only "forgetting" is decay.

**Why it matters**: Incorrect memories should be removable. The CLAUDE.md `/wrong` skill exists but it's unclear how it interacts with Recall.

---

## Implementation Unknowns

### U-19: Rust vs Go for the API Surface
**Question**: The architecture shows "Go or Rust/Axum" for the API layer. Which is actually right?

**Arguments for Rust**: Shares ecosystem with Hopfield layer (if Hopfield is Rust-adjacent), compile-time correctness, better for embedded LMDB usage.
**Arguments for Go**: Simpler async model, faster iteration, net/http is mature, easier to hire for if ever open-sourced.

**Decision criteria**: Does the API layer need tight coupling with the Hopfield/LMDB layer? If yes → Rust. If they're separate services → Go is fine.

---

### U-20: Hopfield In-Process vs Separate Service
**Question**: Should the Hopfield PyTorch layer run in-process with the API server or as a separate service?

**Detailed in**: `decisions/open.md` OD-02. Listed here because it has implications for U-19 (if separate service, language choice for API doesn't matter).

---

## Research Gaps (Not Yet Analyzed)

- **Continual learning literature** — Elastic Weight Consolidation (EWC), PackNet, Progressive Neural Networks. The catastrophic forgetting problem in Hopfield is the same problem as catastrophic forgetting in neural networks. Solutions may apply.
- **Sleep-and-consolidation neuroscience** — Hippocampal-neocortical transfer during slow-wave sleep. Implementations in AI systems (Complementary Learning Systems theory).
- **A-MEM / Zettelkasten systems** — how memory links to itself over time, evolution of memory structure.
- **HyDE (Hypothetical Document Embedding)** — using LLM-generated hypothetical answers as query embeddings instead of the question itself. Could significantly improve cold-path retrieval.
- **Sparse vs Dense Hopfield** — classical Hopfield is fully connected (dense). Sparse variants have better interference properties at scale. Relevant to U-01.

---

## Agentic Memory — The 7 Unsolved Problems

*Added 2026-03-16. Every competitor (mem0, Zep, MemGPT) is "RAG over conversation history." None were designed for the seven constraints unique to agentic systems. These are the unsolved problems that Wave 25-29 research investigates.*

| Human memory system | Agentic memory system | Research wave |
|---|---|---|
| One writer at a time | Multiple agents writing simultaneously — concurrent write conflicts | Wave 25 (Q209-Q210) |
| Human knows what they know | Agent has bounded context window — injection token budget is a physics limit | Wave 25 (Q214) |
| Memory accuracy is mostly trustworthy | Agent-generated content has hallucination risk — SourceTrust gap can be exploited | Wave 26 (Q215) |
| Retrieval is fuzzy recall | Retrieval is token-budget-constrained injection — too many memories displace the prompt | Wave 25 (Q214) |
| Forgetting is passive decay | Forgetting must be GDPR-compliant on demand + adversarially resistant | Wave 26-27 |
| Memory is personal | Memory may be shared across agent swarm — concurrent writes, working vs. long-term tier | Wave 25 (Q211-213) |
| Uncertainty is implicit | Uncertainty must be explicit and propagate — SourceTrust, contradiction detection | Wave 26 (Q215-219) |

## 5 Differentiation Claims — What Recall 2.0 Can Prove No Competitor Can Claim

| Claim | Competitive gap today | Wave that proves/disproves it |
|---|---|---|
| **Token-aware retrieval** — injection respects context window budget | No competitor measures or limits injection token cost | Wave 25, Q214 |
| **Adversarial-robust** — memory poisoning is a first-class threat model | No competitor has documented attack vectors or mitigations | Wave 26, Q215-217 |
| **Active consolidation** — memory set does not grow indefinitely | No competitor implements automatic merge without human intervention | Wave 27, Q221+Q224 |
| **Agent-native working memory** — temporary scratchpad distinct from long-term | All competitors use one memory endpoint for both | Wave 25, Q212-213 |
| **Temporal coherence** — "what did I know at time T" is answerable | mem0/Zep/MemGPT have no bi-temporal query support | OD-21 + Wave 27, Q223 |
