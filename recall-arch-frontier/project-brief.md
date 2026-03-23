# Project Brief — Recall Architecture Frontier

> **Human authority. Agents read this. Do not edit during the loop.**

## What this system does

Recall is a self-hosted memory system for Claude Code. It automatically stores and retrieves memories across AI assistant sessions via hooks. When a user submits a prompt, relevant memories are injected into context. When files are edited, facts are extracted and stored. When sessions end, summaries are persisted.

The goal is to give an AI assistant persistent, searchable memory without any manual curation.

## Core operations

1. **Store**: Accepts a text content blob + domain + tags + importance score. Embeds the content, stores in vector DB (Qdrant), stores metadata in PostgreSQL, optionally stores graph relationships in Neo4j.
2. **Retrieve (semantic)**: Given a query string, returns the top-k most relevant memories using vector similarity. Filtered by domain/tags. Ranked by similarity × importance.
3. **Retrieve (timeline)**: Returns memories in chronological order, optionally filtered by domain or tag.
4. **Retrieve (profile)**: Returns consolidated user profile facts extracted from session summaries.
5. **Rehydrate**: Context window restoration — given a session ID, retrieves the memory set that was relevant at the end of the last session.
6. **Health check**: Verifies all backing services are reachable and responding within SLA.

## Current stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API server | FastAPI (Python) | REST API, hook endpoints |
| Vector store | Qdrant | Embedding storage + ANN retrieval |
| Graph DB | Neo4j | Entity relationships, causal chains |
| Cache | Redis | TTL cache for hot memories, session state |
| Relational DB | PostgreSQL | Memory metadata, importance scores, timestamps |
| Embeddings | Ollama (qwen3-embedding:0.6b) | Local embedding generation |
| LLM | Ollama (qwen3:14b) | Fact extraction, profile synthesis |
| MCP server | Node.js | Claude Code integration layer |
| Hooks | JavaScript | recall-retrieve.js, observe-edit.js, recall-session-summary.js |

## Key invariants

- Retrieval must complete in < 500ms p95 (hooks run synchronously before every prompt)
- All data stays local — no external API calls for storage or retrieval
- The system must degrade gracefully when any single backing service is down
- Memory importance scores must be queryable for threshold filtering (don't surface low-importance noise)

## Known weaknesses

- **Retrieval signal is cosine similarity only** — one-dimensional, misses temporal relevance, recency bias, and contextual co-occurrence signals
- **No forgetting mechanism** — the store grows indefinitely; no decay, no consolidation, no eviction
- **Flat importance scores** — importance is set at write time and never updated based on retrieval patterns
- **Embedding model is small** — qwen3-embedding:0.6b has limited semantic capture vs. larger models
- **No retrieval feedback loop** — when a retrieved memory is used (or ignored), that signal isn't fed back to adjust future retrieval
- **Cold start problem** — new sessions start with zero context about what was recently relevant
- **Graph layer underutilized** — Neo4j is deployed but graph relationships are not actively used in retrieval ranking
- **Chunking is naive** — long memories are stored as single blobs rather than semantically chunked

## Explicit non-goals (Recall 1.0 only — see Scope Reframe below)

- Multi-user / multi-tenant architecture (Recall 1.0 is a personal memory system)
- Cloud deployment or SaaS model (Recall 1.0 is self-hosted only)
- Real-time collaboration features
- External API integrations for storage (no S3, no Pinecone, no OpenAI embeddings)

---

## Scope Reframe — Recall 2.0 Commercial Architecture

**Added 2026-03-16. This section overrides the non-goals above for Wave 23+ research.**

Recall 2.0 is NOT a personal-only system. It targets homelab-to-enterprise with a commercial model:

**Tiers**: self-hosted free → self-hosted pro (Stripe) → cloud SaaS → enterprise (KMS, SSO, audit)
**Distribution model**: Gitea/Bitwarden/Outline model — open source self-hosted builds community, cloud converts to revenue
**Deployment**: Single Rust binary (Reminisce proved this is the right model for self-hosted distribution)
**Prior art**: Reminisce (ReminisceDB) was a previous Rust-based attempt. It got commercial infrastructure right (JWT, Stripe, KMS, CCPA, multi-tenancy, RelationType taxonomy, SourceTrust, TLB). It got retrieval quality wrong (importance scoring in score_memory(), scheduled decay workers, no real HNSW). The full analysis is in `recall-2.0/reminisce.md`.

**Wave 23 research questions focus on**: multi-tenant isolation, single-binary deployment, SourceTrust integration, RelationType decay, commercial tier design, migration fidelity from importance-scored Recall 1.0 to behavioral-scored Recall 2.0.

**Wave 24 research questions focus on**: novel substrate discovery — is a vector space even the right retrieval substrate, what does physics say memory retrieval must be, multi-user isolation from first principles.

**Wave 25-29 research questions focus on**: agentic memory primitives (concurrent multi-agent writes, working memory distinct from long-term memory, token injection physics), adversarial integrity (memory poisoning via agent hallucination, prompt injection via stored memories, data poisoning detection), intelligent consolidation (sleep-analog background compaction, concept drift false-positive ceiling, automatic merge without human intervention), distribution moat (minimum viable agent memory SDK, memory diff as a session-to-session delta, memory attribution/provenance), and scale (HNSW quality cliffs from 22K to 1M vectors, hybrid sparse+dense retrieval, single-node vs. distributed architecture decision).

**Key constraint**: Every feature must work self-hosted. No cloud-only features. Cloud tier = managed infrastructure, not feature gating.

## Vertical Markets — Expanded Scope

**Added 2026-03-16. Multi-user and team features are priced-tier features, not enterprise-only.**

Recall 2.0 is not limited to solo developer use. The memory system architecture is directly applicable to:

| Vertical | Key memory requirement | Key compliance |
|---|---|---|
| AI chatbot | Session continuity, short-term episodic | Varies |
| Medical / science lab | Mandatory retention (7yr+), zero hallucination on factual memory, bi-temporal queries | HIPAA, FDA 21 CFR Part 11 |
| Research AI | Hypothesis tracking, causal chains, supersession on falsification | IRB, data governance |
| Advisor / trading AI | Signal decay (hours), mandatory 7-year record hold | SEC, FINRA, MiFID II |
| Process / maintenance AI | Procedural memory (no decay), equipment state (fast decay) | ISO 55001 |
| Personalized AI | Preference + emotional valence, right to forget | GDPR, COPPA |
| Relationship intelligence AI | Long-term event persistence, interpersonal context | GDPR, CCPA |

**Architectural requirements that verticals add** (not present in Recall 1.0 design):
- **Retention policy engine**: mandatory hold dates separate from behavioral decay scores
- **Memory type taxonomy**: Factual, Procedural, Episodic, Signal, Preference, Relational, Hypothesis — each with distinct decay rates and retrieval strategies
- **Bi-temporal validity**: "what did the system know on date X?" is required for medical and trading
- **SourceTrust per-vertical calibration**: trust weights are not universal constants — a VerifiedSystem in medical context (FHIR record) carries different weight than in chatbot context

These requirements are captured in OD-21 (retention policy engine) and OD-22 (memory type taxonomy) in `recall-2.0/decisions/open.md`.

## Forbidden tools for taboo-architect

The taboo-architect agent must not reference any of these by name or describe them under different words:

```
Qdrant
Weaviate
Pinecone
Chroma
Milvus
pgvector
FAISS
Annoy
Neo4j
Redis
PostgreSQL
SQLite
Ollama
LangChain
LlamaIndex
MemGPT
mem0
Zep
FastAPI
Pydantic
cosine similarity
dot product
ANN (approximate nearest neighbor)
HNSW
IVF
LSH
```

Start from: what is the physical requirement? What data structure satisfies those requirements? Then derive.

## Past misunderstandings

- The graph layer (Neo4j) is deployed but underutilized — agents should NOT assume graph-based retrieval is already working
- Importance scores are currently a single float, not a time-series — "importance decay" would require schema changes
- The embedding model runs on a separate GPU server (Ollama at 192.168.50.62) — network latency to the embedding server is part of the store/retrieve critical path
