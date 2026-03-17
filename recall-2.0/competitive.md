# Competitive Landscape — Recall 2.0

What exists today. Where each system fails. What Recall 2.0 must be better at.

**Last updated**: 2026-03-16

---

## The Field

| System | Approach | Storage | Graph | Decay | Reinforce | Consolidate |
|---|---|---|---|---|---|---|
| MemGPT / Letta | Page-in/page-out from context | Custom + archival | No | Importance score | No | No |
| mem0 | Four-operation LLM consolidation | Vector + graph | Partial | No | No | On write only |
| Zep / Graphiti | Bi-temporal knowledge graph | Neo4j + vector | Yes | No | No | Entity extraction only |
| LangChain Memory | Multiple backends | Various | No | No | No | No |
| Recall 1.0 | FastAPI + 4-store hybrid | Qdrant+Neo4j+Redis+PG | Yes | Scheduled importance | No | Scheduled LLM |

**Correct on all five operations**: none of the above.

---

## System-by-System Breakdown

### MemGPT / Letta
**What it does**: Treats the context window as main memory and external storage as disk. Pages memories in and out based on importance scores.

**Where it fails**:
- Importance scores are write-time priors — wrong primitive for eviction decisions
- Page-in/page-out is an explicit LLM operation — adds latency to every context switch
- No behavioral learning — doesn't get better at knowing what to page in over time
- Single machine assumed — no concurrent write handling
- No decay — memories are either in context or in archive, no gradient

**What it gets right**: Context window as a first-class resource. The paging metaphor is useful even if the implementation is wrong.

---

### mem0
**What it does**: LLM chooses ADD/UPDATE/DELETE/NOOP for each new piece of information against existing memories. More precise than merge-all consolidation.

**Where it fails**:
- Every write requires an LLM call to decide operation — expensive, slow, adds model dependency to the write path
- No decay — memories persist until explicitly deleted
- No retrieval reinforcement
- No behavioral graph — memories are isolated records
- Importance-based retrieval ranking

**What it gets right**: The four-operation consolidation model is better than naive append-only. NOOP is a meaningful operation — not everything needs to be stored.

---

### Zep / Graphiti
**What it does**: Bi-temporal knowledge graph — stores what was known and when it was known. Entity extraction, relationship mapping, invalidation with timestamps.

**Where it fails**:
- Graph is static — edges don't strengthen with use
- No decay — bi-temporal means you never forget, you only invalidate
- No retrieval reinforcement
- Entity extraction quality depends entirely on LLM quality — garbage in, garbage out
- Complex infrastructure requirement — Neo4j is heavyweight

**What it gets right**: Bi-temporal invalidation ("what did we know at time T?") is a genuinely useful capability that Recall 1.0 doesn't have. Never-delete-only-invalidate is the correct data model for a system that needs auditability.

---

### LangChain Memory
**What it does**: Multiple memory backends (conversation buffer, summary, entity, vector store). Composable but shallow.

**Where it fails**:
- No coherent architecture — multiple backends with different assumptions
- No decay, no reinforcement, no consolidation
- No cross-session persistence as a first-class concern
- Not designed for multi-machine operation

**What it gets right**: Composability. Different memory types for different use cases is the right instinct even if the execution is shallow.

---

### Recall 1.0
**What it does**: FastAPI + Qdrant (vectors) + Neo4j (graph) + Redis (volatile) + PostgreSQL (metadata). Full session lifecycle, hooks, MCP interface, spreading activation, decay worker.

**Where it fails** (the honest assessment):
- Four-store coherence is complex and fragile — divergence is a known failure mode
- Decay is a scheduled ARQ worker — wrong model (P3 violation)
- No retrieval reinforcement — CO_RETRIEVED graph was never wired in
- Importance scores still used for eviction and routing
- Multi-machine consistency handled by idempotency keys but not CRDTs — still has coordination overhead
- Health monitoring measures infrastructure, not retrieval quality

**What it gets right**:
- Hook infrastructure — UserPromptSubmit, PostToolUse, Stop hooks are correct and proven
- MCP interface — `recall_search`, `recall_search_full`, `recall_timeline` are the right API surface
- Session lifecycle — session start/end as first-class events is correct
- Multi-store approach — the four stores serve different purposes and that intuition is right even if the specific tools aren't

---

## What "Best" Requires

To be the best memory system designed to date, Recall 2.0 must be the first system that:

1. Handles all five operations (write, decay, retrieve, reinforce, consolidate) correctly
2. Uses no importance scores anywhere
3. Has retrieval reinforcement built into the storage substrate
4. Has physics-based continuous decay
5. Handles multi-machine consistency without coordination protocols
6. Has background consolidation as a first-class autonomous process
7. Monitors retrieval quality, not just infrastructure health

---

## Areas Not Yet Analyzed

- [ ] **A-MEM / Zettelkasten-inspired systems** — memory evolution when new memories link to old ones
- [ ] **GraphRAG** — community/cluster summaries from graph structure
- [ ] **HyDE** — hypothetical document embedding for query-document gap
- [ ] **Stanford Generative Agents** — reflection, three-factor retrieval
- [ ] **Voyager / ReAct memory** — agent loop memory patterns
- [ ] **Neuroscience-grounded systems** — any academic implementations of hippocampal-neocortical transfer models
- [ ] **Vector database native memory** — Pinecone's memory layer, Weaviate's memory module
- [ ] **Continual learning literature** — EWC, PackNet, progressive neural networks — the catastrophic forgetting problem is the same problem

---

## What Recall 2.0 Can Claim That No Competitor Currently Can

*Added 2026-03-16. These claims are backed by Wave 25-29 research (Q209-Q233). Each claim identifies a genuine gap in the current competitive landscape as of 2026.*

| Claim | Why it's defensible | Competitor gap |
|---|---|---|
| **Token-aware retrieval** — memory injection respects context window budget; max memories computable from window size at query time | No competitor has published a token injection budget model or exposes a token-count parameter on retrieval | mem0, Zep, MemGPT all return flat K memories with no regard for context window consumption |
| **Adversarial-robust write path** — stored memories are screened for injection patterns and SourceTrust-gated to prevent hallucinated facts from dominating retrieval | No competitor has a documented threat model for their memory system | All competitors accept agent writes at face value with no poisoning detection |
| **Active consolidation** — memory set does not grow indefinitely; related memories are automatically merged into abstractions on a background schedule | No competitor has shipped automatic consolidation without human review | All competitors are pure accretion systems — memories are only added, never merged |
| **Agent-native working memory** — ephemeral task-scoped memory is a distinct tier from persistent long-term memory, with automatic promotion on task success | All competitors use one endpoint for both ephemeral and persistent memory | No production framework separates working memory from long-term memory at the API level |
| **Temporal coherence** — any memory state at any past time is queryable; "what did the agent know at T?" is always answerable | mem0/Zep/MemGPT have no bi-temporal support; retrieval reflects only the current state | Required for HIPAA, SEC, FDA 21 CFR Part 11 audit — none of the competitors can enter regulated verticals without this |
| **Memory diff** — every session produces a queryable delta of what was learned, stored, and updated | No competitor surfaces a session-to-session memory delta | Users have no visibility into what the agent's memory state changed between sessions |
