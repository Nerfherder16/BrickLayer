# Open Decisions — Recall 2.0

Questions that must be answered before building. Add freely. Move to `decided.md` when resolved.

**Last updated**: 2026-03-16

---

## Substrate Decisions

### OD-01: Is Qdrant the right cold vector store?
Qdrant is the current cold-path ANN store. It's well-maintained, has good filtering, and Tim knows it. But it's not designed for this use case, retrieval doesn't reinforce, and it's another server to run.

**Options**:
- A: Keep Qdrant as cold store — proven, maintained, Tim knows it
- B: Replace with a purpose-built persistent ANN index (HNSW in LMDB-backed custom store)
- C: Remove the cold store entirely — Hopfield handles everything
- D: Use a different managed vector DB (Weaviate, Pinecone local, etc.)

**What needs to be known**: Can a Hopfield network at 22K+ memories reliably replace ANN search without spurious attractors becoming a problem? If yes, C is viable.

---

### OD-02: Hopfield hot layer — in-process or separate service?
**Options**:
- A: In-process with the API server — lowest latency, single deployment, but couples the API lifecycle to the Hopfield model lifecycle
- B: Separate PyTorch service — cleaner boundary, can restart independently, adds one network hop

**What needs to be known**: How frequently does the Hopfield network need to be updated (new weights on reinforcement)? If updates are frequent and fast, in-process is correct. If updates require a training pass (minutes), separate service is correct.

---

### OD-03: Online learning in Hopfield — is it feasible?
Classical Hopfield networks use Hebbian learning — weights are set once from the stored patterns. Adding a new memory means recomputing weights. Modern Hopfield networks have better storage capacity but the same issue.

**Options**:
- A: Batch retrain on a schedule — accept some staleness for new memories
- B: Online Hebbian update — incremental weight update when new memory is stored (correct but may degrade over time due to interference)
- C: Hybrid — Hopfield for retrieval of existing patterns, buffer for recent memories not yet integrated

**What needs to be known**: What is the interference cost of online Hebbian updates at Tim's corpus scale? Does it exceed the staleness cost of batch retraining?

---

### OD-04: CRDT model — does it handle all write scenarios?
CRDTs guarantee conflict-free convergence for the data types they model. But not everything fits neatly into OR-Set / G-Counter / LWW-Register.

**Scenarios that need validation**:
- Two machines write the same memory with slightly different content at the same time → LWW-Register wins, but which machine's content?
- A memory is deleted on one machine while being accessed on another → OR-Set handles this, but what's the semantic?
- Access count is incremented on both machines for the same memory → G-Counter merges correctly

**What needs to be known**: Is there a scenario where CRDT convergence produces a semantically wrong result for memory operations?

---

### OD-05: What is the right embedding model?
Currently: `qwen3-embedding:0.6b` on Ollama, RTX 3090. 1024 dimensions.

**Questions**:
- Is 1024 dims right for the Hopfield layer capacity requirement?
- Is qwen3-embedding the best model at this parameter count for the use case?
- Should embeddings be domain-specific (separate models for code memories vs. conversation memories vs. factual memories)?
- What's the tradeoff between embedding quality and inference speed for the write path latency budget?

---

### OD-06: What is the "unit of memory"?
In Recall 1.0, a memory is a text record with an embedding. In Recall 2.0, it could be:
- A: Same as 1.0 — text + embedding (backward compatible, simple migration)
- B: An activation pattern in the Hopfield network — no explicit text record, just weights
- C: A structured record with text, embedding, metadata, AND an activation pattern (hybrid)
- D: Multiple representations — episodic (text), semantic (embedding), procedural (pattern) stored differently

**What needs to be known**: What retrieval use cases require explicit text? What use cases are better served by pure pattern completion?

---

## Interface Decisions

### OD-07: MCP backward compatibility
Should the Recall 2.0 MCP tools be backward compatible with Recall 1.0?

**Options**:
- A: Full backward compat — `recall_search`, `recall_search_full`, `recall_timeline` identical API
- B: New API, migration guide for hooks
- C: Both — v1 compat layer + new v2 tools

**Stakes**: Tim's existing hooks (`recall-retrieve.js`, `observe-edit.js`, `recall-session-summary.js`) all call Recall 1.0 endpoints. If not backward compatible, all hooks need to be rewritten on cutover.

---

### OD-08: Hook architecture — keep Node.js or migrate?
Current hooks are Node.js CommonJS scripts. This is correct for the Claude Code hook model but adds a runtime dependency.

**Options**:
- A: Keep Node.js — proven, works, Tim has working hooks
- B: Migrate to compiled binaries (Rust) — no Node.js dependency, faster startup, single file deploy
- C: Migrate to a different scripting approach

---

## Scope Decisions

### OD-09: Personal vs. multi-user
Recall 1.0 added multi-user support in Phase 13. Recall 2.0 — start personal-first or design for multi-user from the start?

**Tradeoff**: Multi-user from the start means more complex CRDT model (user namespace isolation), more complex health monitoring, harder to reason about during design. Personal-first means a rewrite to add users later.

---

### OD-10: Open source strategy
- A: Private — Tim's personal system, not released
- B: Open source — MIT or similar, released as a project
- C: Open core — core engine open, some components private

**What this affects**: API design (needs to be generalizable vs. Tim-specific), documentation requirements, infrastructure assumptions in the code.

---

### OD-11: Portability requirement
Must Recall 2.0 run on Tim's specific homelab (CasaOS, N100, RTX 3090 on separate Ollama host)?

Or must it run on:
- Any Linux server
- Any hardware with a GPU
- Cloud (Railway, Fly.io)
- Mac/Windows dev machines

**What this affects**: Deployment model, Docker vs. native, hardware assumptions in the Hopfield layer.

---

## Migration Decisions

### OD-12: Migration path from Recall 1.0
22,423 vectors in Qdrant. Existing Neo4j graph. PostgreSQL metadata. Session history.

**Options**:
- A: Hard cutover — import everything into Recall 2.0 format at launch, Recall 1.0 goes dark
- B: Gradual — run both in parallel, new writes go to 2.0, old data migrated in background
- C: Bridge layer — Recall 2.0 reads Recall 1.0 stores as a legacy backend, migrates lazily

**What this affects**: Launch timing, data integrity requirements during transition, complexity of the 2.0 code.

---

## Questions Added During Ideation

_Add new open decisions here as they come up:_

- [ ] What does the injection format look like — how do memories reach Claude's context window in a way that's more useful than Recall 1.0's text injection?
- [ ] What is the right idle threshold for triggering background consolidation?
- [ ] Should consolidation write back to the same memory collection or a separate "abstract memory" tier?
- [ ] What's the latency budget for the full write path (store call to memory persisted)?
- [ ] What's the latency budget for the hot retrieval path (query to results returned)?
- [ ] Does the system need a dashboard? If yes, rebuild from scratch or adapt Recall 1.0's React dashboard?

---

## Commercial Architecture Decisions
*(Added 2026-03-16 — scope reframe: Recall 2.0 targets homelab-to-enterprise, self-hosted to SaaS)*

### OD-13: Multi-tenant isolation model
Recall 2.0 must serve multiple users on a single instance (team tier) and eventually multi-tenant SaaS. The isolation model determines the entire storage architecture.

**Options:**
- A: **Key-prefix isolation** — all stores use `{user_id}:` prefix on every key. Single shared Hopfield matrix with user_id-partitioned embeddings. Simplest, lowest overhead, weakest isolation.
- B: **Per-user Hopfield instance** — each user gets a separate weight matrix, stored separately, loaded into VRAM on demand. Strongest isolation, highest VRAM overhead at scale.
- C: **Tenant-sharded instances** — separate Recall 2.0 process per tenant group. Strong isolation, high operational overhead, best for regulated enterprise.

**What needs to be known**: VRAM overhead per user for a 1024-dim Hopfield weight matrix at 22K patterns. Whether key-prefix isolation leaks timing information between users. Maximum user count before option B exhausts VRAM.

---

### OD-14: Deployment packaging strategy
The single-binary Rust approach (Reminisce model) vs. the container orchestration approach (Recall 1.0 model) determines the self-hosted distribution story.

**Options:**
- A: **Single Rust binary** — embeds LMDB, includes fastembed-rs for CPU inference, ships as a single executable. `docker run recall` or bare metal. Best for homelab.
- B: **Minimal container stack** — API server + LMDB volume. Still requires Ollama separately for GPU inference. Two containers max.
- C: **GPU-optional binary** — fastembed-rs for CPU inference by default, auto-detects Ollama for GPU acceleration if available. Single binary that degrades gracefully without GPU.

**What needs to be known**: fastembed-rs embedding quality vs qwen3-embedding:0.6b via Ollama. CPU inference latency for fastembed-rs on N100 hardware. Whether single binary is achievable with Rust given LMDB + HNSW + embedding dependencies.

---

### OD-15: SourceTrust integration in the write path
Reminisce implemented SourceTrust (UserDirect=0.9, VerifiedSystem=0.8, ToolOutput=0.5, AgentGenerated=0.4) as a write-time annotation that influenced retrieval scoring. This is P1-compliant because it's provenance (source reliability), not predicted retrieval value.

**Options:**
- A: **Write-time annotation only** — store source trust in LMDB metadata, surface it in retrieval results but don't weight behavioral scores by it.
- B: **Behavioral score modifier** — multiply the behavioral score by source trust at retrieval time. `effective_score = behavioral_score × source_trust`. Lower trust memories can still be retrieved if highly activated.
- C: **Threshold gate** — source trust below X (e.g., AgentGenerated < 0.4) requires higher behavioral activation to surface.

**What needs to be known**: Does source trust weighting violate P1 in option B? The argument that it doesn't: source trust is a property of the source, not a prediction about future retrieval value. The argument that it does: it creates a write-time gate on retrieval, functionally similar to importance scoring.

---

### OD-16: RelationType taxonomy and edge decay
Reminisce implemented 23 typed graph edges with per-type decay multipliers and default strengths. Recall 2.0's behavioral graph (co-retrieval tracking) needs an analogous taxonomy.

**Options:**
- A: **Adopt Reminisce's 23-type taxonomy** — proven by 16K imported memories, decay multipliers already calibrated.
- B: **Minimal taxonomy** — 5-7 types (Supersedes, Contradicts, Causes, Uses, RelatedTo). Simpler to implement and maintain.
- C: **Emergent taxonomy** — LLM generates relation type during consolidation based on content analysis. No fixed taxonomy.

**What needs to be known**: Whether Reminisce's 23 types are too granular for useful behavioral routing, or whether the granularity is what makes the decay multipliers meaningful. Whether option C produces consistent enough types for decay to work correctly.

---

### OD-17: Embedding portability (fastembed-rs vs Ollama dependency)
Recall 1.0 requires a separate Ollama server (GPU recommended). For homelab-to-enterprise scale, the embedding dependency must be flexible.

**Options:**
- A: **Ollama-only** — keep Ollama as the embedding provider. Requires a network call per embedding. GPU strongly recommended.
- B: **fastembed-rs primary, Ollama optional** — embed model inference runs in-process via fastembed-rs ONNX. Fall back to Ollama if GPU is available and configured.
- C: **Plugin model** — embedding provider is a trait/interface. First-party implementations: fastembed-rs, Ollama. Community implementations possible.

**What needs to be known**: fastembed-rs inference quality vs Ollama qwen3-embedding:0.6b. fastembed-rs latency on N100 (CPU only). Whether fastembed-rs and the Recall 2.0 binary compile cleanly together on Windows/Mac/Linux.

---

### OD-18: Commercial feature tier partition
**Updated 2026-03-16**: The system is valuable enough at all tiers that multi-user is NOT a differentiator reserved for enterprise — it is a paid-tier feature available from the first priced tier. Free tier is a limited trial to drive distribution and trust, not a functional long-term product. The entire system's value proposition (behavioral scoring, consolidation, team memory, vertical compliance) is unlocked at paid tiers.

**Principle**: Free tier exists for distribution and trust-building only. Pro tier is the primary product — solo and team users both land here. Enterprise tier captures regulated verticals (medical, financial, government) requiring compliance infrastructure.

**Revised partition:**

| Feature | Trial (Free) | Pro | Enterprise |
|---|---|---|---|
| Core store/retrieve | ✓ | ✓ | ✓ |
| Behavioral scoring (vs importance) | ✓ | ✓ | ✓ |
| Consolidation | ✗ | ✓ | ✓ |
| Health dashboard | ✗ | ✓ | ✓ |
| Memory limit | 1K memories | Unlimited | Unlimited |
| Multi-user / team | ✗ | ✓ (unlimited users) | ✓ (unlimited) |
| CRDT multi-instance sync | ✗ | ✓ | ✓ |
| Vertical memory type routing | ✗ | ✓ | ✓ |
| Retention policy engine | ✗ | ✓ (configurable) | ✓ (compliance-regime-aware) |
| Bi-temporal validity queries | ✗ | ✓ | ✓ |
| SSO / SAML | ✗ | ✗ | ✓ |
| Audit log export (HIPAA/FINRA) | ✗ | ✗ | ✓ |
| KMS key management | ✗ | ✗ | ✓ |
| Compliance regime config (HIPAA, SEC, GDPR) | ✗ | ✗ | ✓ |
| SLA / support | None | Email | Dedicated |

**Rationale for changes**:
- Multi-user moves to Pro (not Enterprise) — teams are the primary unit for every vertical, not an advanced feature
- Consolidation and health dashboard move to Pro (not Trial) — these are core product value, not distribution bait
- Trial memory limit drops to 1K — enough to experience the system, not enough to depend on it
- Retention policy engine is Pro+ — required for medical, trading, research, maintenance verticals
- Compliance regime config is Enterprise — HIPAA BAA, FINRA audit schema, ISO 55001 are enterprise sales items

**What needs to be known**: Whether 1K trial memories is enough for a meaningful first experience (vs. 5K). Whether "unlimited users" at Pro is viable without per-seat pricing — consider whether Pro should be per-seat or flat-rate. How Pro and Enterprise price points compare to Zep/mem0 enterprise pricing to validate the market exists.

---

### OD-19: License and open source strategy
**Options:**
- A: **MIT** — fully open. Maximum distribution. Zero commercial protection.
- B: **Apache 2.0** — patent protection, still fully open. Standard for infrastructure.
- C: **SSPL (Server Side Public License)** — MongoDB model. Forces cloud providers to open source their hosted version or buy a commercial license. Protects against AWS/GCP hosting your product without paying.
- D: **Business Source License (BSL)** — production use requires commercial license, source available for development/testing. Converts to Apache after 4 years. HashiCorp's model.
- E: **Open Core** — core engine is MIT, commercial features (SSO, audit, KMS, multi-tenant) are proprietary.

**What needs to be known**: Whether SSPL meaningfully deters cloud provider hosting at Recall 2.0's scale (probably not — AWS won't host a niche AI memory system). Whether BSL prevents community adoption. Whether open core correctly partitions the features. The Gitea/Bitwarden/Outline/Plausible precedents for self-hosted commercial products.

---

### OD-20: Migration fidelity from Recall 1.0 (importance → behavioral)
Recall 1.0 memories have importance scores (0.0-1.0) but no behavioral history. Recall 2.0 uses behavioral scoring (access frequency, recency, co-retrieval density) with no importance scores. Migration must bootstrap behavioral scores from available data.

**Options:**
- A: **Start fresh** — all memories get default behavioral scores. Importance scores discarded. System learns from scratch.
- B: **Importance → access_frequency proxy** — treat importance score as a proxy for initial access_frequency. A memory with importance=0.9 gets behavioral_score bootstrapped as if accessed 10 times; importance=0.1 gets 1 access. Approximate but preserves the signal.
- C: **Use access timestamps from Recall 1.0** — Recall 1.0 stores `last_accessed` and access counts. Use these directly as behavioral history. More faithful than option B but requires access timestamp data to be present and accurate.
- D: **Hybrid** — use access timestamps where available (option C), fall back to importance proxy (option B) for memories without timestamp history.

**What needs to be known**: How many Recall 1.0 memories have meaningful access timestamp history vs. just an initial importance score. Whether option B's importance-as-frequency proxy creates a behavioral signal that eventually converges on correct behavior or permanently biases the system. Reminisce's migration code used option A — 16K memories imported, all started fresh.

---

## Vertical Market Decisions
*(Added 2026-03-16 — expanded scope: Recall 2.0 serves not just personal/team AI memory but vertical markets with distinct memory requirements)*

The following verticals have been identified as targets, each with distinct requirements:
- **AI chatbot memory** — conversational continuity, session-scoped short-term memory
- **Medical / science lab** — mandatory retention, bi-temporal queries, HIPAA compliance, zero hallucination tolerance
- **Research AI** — hypothesis tracking, causal chain memory, literature supersession
- **Advisor / trading AI** — signal decay in hours, mandatory 7-year record hold, MiFID II / FINRA
- **Process / maintenance AI** — procedural memory (no decay), equipment state memory (fast decay), ISO 55001
- **Personalized AI** — preference + emotional valence memory, GDPR right-to-forget
- **Relationship intelligence AI** — interpersonal context, long-term event persistence, interaction history decay

---

### OD-21: Retention policy engine design
The current decay model (memories fade via behavioral scoring) and a mandatory retention model (memories cannot be deleted before a compliance-mandated date) are opposing requirements that must coexist in the same system.

**The core conflict**: GDPR requires deletion on user request. HIPAA and FINRA require mandatory hold (7 years minimum). A memory may be subject to both simultaneously (a medical AI assistant in a GDPR jurisdiction). The architecture must handle this without special-casing each compliance regime.

**Options:**
- A: **Per-memory retention policy field** — each memory record carries a `retention_policy` struct with `mandatory_hold_until` (date or null), `deletable_on_request` (bool), `compliance_regime` (enum). Deletion requests check the policy before executing. Simple, self-contained, auditable.
- B: **Separate policy registry** — retention policies are stored in a policy registry keyed by domain/tag, not on the memory record. Policies apply to all memories matching a domain/tag pattern. Flexible but requires policy evaluation on every delete request.
- C: **Composable policy objects** — policies are composable: `HIPAA_HOLD AND GDPR_DELETABLE` evaluates to "hold for 7 years, but flag for deletion review at end of hold period." Handles the HIPAA+GDPR conflict without special cases. Most correct, most complex.

**What needs to be known**: Whether Option A's per-memory struct is too rigid for the HIPAA+GDPR conflict case. Whether Option C's composable policies are implementable without a policy engine framework (too much complexity for v1). Whether the retention policy check at delete time adds unacceptable latency.

---

### OD-22: Memory type taxonomy and vertical routing
Different verticals require fundamentally different retrieval strategies for different memory types. The current design routes all retrieval through the same path (Hopfield hot layer → ANN cold store). A medical factual memory should never go through probabilistic Hopfield completion — it needs exact lookup. A trading signal memory needs recency-weighted retrieval that deprioritizes anything older than 4 hours. A relationship memory needs emotional valence as part of the retrieval score.

**Memory types identified:**

| Type | Decay rate | Retrieval strategy | Example verticals |
|---|---|---|---|
| Factual / declarative | None (or very slow) | Exact lookup, high confidence required | Medical, legal, research |
| Procedural | None | Exact lookup, version-tracked | Maintenance, medical |
| Episodic | Behavioral (standard) | Similarity + recency | Personal, chatbot |
| Signal / temporal | Aggressive (hours to days) | Recency-dominant, similarity secondary | Trading, process monitoring |
| Preference | Slow behavioral | Similarity + longitudinal pattern | Personalized AI, relationship |
| Relational / interpersonal | Event-anchored (key events persist) | Graph traversal + similarity | Relationship intelligence |
| Hypothesis / speculative | Supersession-based | Tracked against outcome, retracted on falsification | Research AI |

**Options:**
- A: **Memory type as a first-class field** — every memory record carries a `memory_type` enum. Retrieval routing checks type before choosing path. Type-specific decay rates applied at write time.
- B: **Domain-inferred type** — memory type inferred from domain tag at write time (domain="medical" → type=Factual, domain="trading" → type=Signal). No explicit type field needed; domain tag carries the semantics.
- C: **LLM-classified type at consolidation** — memory type assigned by LLM during consolidation pass, not at write time. Allows reclassification as context accumulates (a memory written as Episodic may be reclassified as Factual after the system learns it's consistently retrieved as ground truth).

**What needs to be known**: Whether Option B's domain-inferred typing is too coarse (a medical domain memory could be either Factual or Episodic — "patient was anxious today" is Episodic, "patient is allergic to penicillin" is Factual). Whether Option C's LLM classification latency at consolidation time is acceptable. Whether the retrieval routing logic for 7 memory types adds too much complexity for v1 (consider phased approach: Factual + Episodic in v1, others in v1.1).

---

### OD-23: Memory correction and edit path
Users will store wrong memories. Agents will hallucinate and store those hallucinations (SourceTrust=AgentGenerated=0.4, but still stored). There is no designed path to correct, edit, or retract a memory's content after write.

**The problem**: Recall 1.0 has no edit endpoint. You can add a new memory that supersedes the old one (via Neo4j Supersedes edge), but the original wrong memory still exists and still has retrieval weight. For medical and research verticals, a wrong factual memory that hasn't been fully suppressed is a correctness and liability risk.

**Options:**
- A: **Soft edit with version history** — editing a memory creates a new version record, the old version is retired (retired_at set), retrieval uses only the active version. Full audit trail preserved. Correct for compliance verticals.
- B: **Hard delete and re-insert** — editing deletes the old record entirely, inserts a new one. Simple. Destroys audit trail. Not compliant for HIPAA/FINRA.
- C: **Correction memory pattern** — no edit endpoint at all. Instead, a `CORRECTS` relation type is added to the graph, and a correction memory is stored with higher trust weight. The reranker suppresses the original. No schema changes needed. Consistent with the supersession model.
- D: **User-facing correction UI + API** — expose `/memories/{id}/edit` endpoint with version history (Option A) AND a "mark as incorrect" button in the dashboard that applies a SourceTrust penalty and adds a CORRECTS edge (Option C hybrid).

**What needs to be known**: Whether Option C (correction memory) suppresses the original reliably enough for medical-grade correctness, or whether retrieval can still surface the original in edge cases. Whether version history (Option A) significantly increases storage overhead at 22K+ memories. Which option the existing MCP tool surface can expose without a breaking change.

---

### OD-24: Re-embedding pipeline (model upgrade path)
Every vector in the store is tied to the embedding model that generated it. If the embedding model is upgraded (qwen3-embedding:0.6b → a higher-quality model), all stored vectors become incompatible with the new model's vector space. Semantic search across mixed-model vectors produces garbage results. No re-embedding pipeline is designed.

**Why this is load-bearing**: This is not a future problem. Embedding models are improving rapidly. The choice of embedding model at launch is effectively permanent unless a re-embedding path is designed now. At 22K memories, re-embedding takes ~22K × embedding_latency. At 150ms per embedding via Ollama, that's 55 minutes of blocking inference — acceptable for a migration but must be designed to run without downtime.

**Options:**
- A: **Big-bang re-embed** — scheduled maintenance window. Take Recall offline, re-embed all memories with new model, swap the collection, come back online. Simple but requires downtime. Unacceptable for SaaS.
- B: **Dual-index shadow write** — new memories write to both the old and new model's index. A background job re-embeds old memories into the new index. Retrieval uses the new index when coverage exceeds a threshold (e.g., 90%). Zero downtime. Complex.
- C: **Model-versioned collections** — each embedding model has its own named collection. Retrieval fans out across all model versions and merges results. Zero downtime, no re-embedding needed, but merged ANN results across different vector spaces is semantically invalid.
- D: **Embedding model as a first-class field on every record** — every memory stores which model generated its embedding. Re-embedding is an online background job that processes memories in order of last_accessed (most recent first). Retrieval uses whatever embedding is current for each memory. Degraded quality during migration but never invalid.

**What needs to be known**: Whether Option B's dual-index write path adds acceptable latency to the hot write path. Whether Option D's mixed-model retrieval degrades quality acceptably during migration (the top-K result set mixes embeddings from different spaces — this is incorrect by definition but may be "good enough" in practice). The re-embedding throughput at 22K memories on the RTX 3090.

---

### OD-25: Context window budget management for memory injection
The hook injects memories into Claude's context on every prompt. As the corpus grows and more memories become "relevant" to a query, the injected content grows. No ceiling is enforced. At large corpus sizes this produces two failure modes: (1) memories crowd out the actual task context, degrading output quality; (2) the injected memories themselves become too long to be useful (user reads "10 relevant memories" and skips them all).

**The problem is symmetric**: Too few memories injected = missed context. Too many = context crowding. The current design has no mechanism to manage this tradeoff dynamically.

**Options:**
- A: **Fixed K ceiling** — retrieve top-K where K is a config constant (default 5). Simple. Doesn't adapt to query complexity or available context window.
- B: **Token budget** — inject memories until a token budget (e.g., 2,000 tokens) is consumed. Memories ranked by behavioral score fill the budget in order. Adapts to memory length but not to query complexity.
- C: **Adaptive budget based on context** — estimate remaining context window space before injection, allocate a percentage (e.g., 15%) to memories, fill with top-ranked memories up to that allocation. Requires knowing the context window size and current usage — both available in the hook environment.
- D: **Tiered injection format** — LLPC (always-inject) memories get full text. MBC (on-demand) memories get compressed summaries (1-2 sentences). Same number of memories injected but lower token cost for the long-tail memories.

**What needs to be known**: Whether Option C's context window estimation is reliable in the Claude Code hook environment (does the hook have access to current context usage?). Whether Option D's compressed summaries degrade retrieval utility enough to matter. What the empirical token distribution of Recall 1.0 memories is at the 50th and 95th percentile (determines whether a 2,000-token budget is too tight or too loose at current corpus size).
