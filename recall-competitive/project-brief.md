# Project Brief — Recall Competitive Analysis

**Authority tier**: Tier 1 — Human authority. Agents read this but never modify it.

## What This Project Does

This autoresearch session maps Recall's competitive position against the current market for
AI memory / persistent context systems. The goal is three outputs:

1. **Gap map** — where Recall falls short of best-in-class competitors
2. **Advantage map** — where Recall is genuinely ahead or uniquely positioned
3. **Improvement roadmap** — architectural and product changes that would make Recall
   the unambiguous best-in-class choice for self-hosted AI memory

This is NOT a bug-finding session. It is a competitive intelligence session. Findings
should be strategic and actionable — not micro-level implementation bugs.

---

## Recall Architecture (Current State)

Recall is a self-hosted, persistent memory system for Claude Code. It captures facts
from coding sessions automatically via hooks, stores them in a multi-store backend,
and retrieves them at the start of each new session.

### Storage Layer
- **Qdrant** — primary vector store (embeddings + payload metadata)
- **Neo4j** — knowledge graph (memory nodes + typed relationship edges)
- **PostgreSQL** — audit log, metrics snapshots, ML training data
- **Redis** — session state, ARQ task queue

### Intelligence Layer (Ollama, local)
- **Embedding model**: `qwen3-embedding:0.6b` (local, ~600M params)
- **LLM**: `qwen3:14b` for fact extraction, consolidation, synthesis
- **Signal classifier**: sklearn binary classifier (trained on audit feedback)
- **Reranker**: sklearn gradient boost (trained on retrieval feedback)

### Memory Lifecycle Pipeline
1. **Ingest** (observer.py) — LLM extracts facts from file edits → content-hash dedup →
   semantic dedup (cosine threshold) → store to Qdrant + Neo4j
2. **Decay** (decay.py) — daily importance decay based on age + access count + stability
3. **Consolidation** (consolidation.py) — hourly merge of near-duplicate semantic memories
4. **Hygiene** (hygiene.py) — daily soft-delete of stale low-importance memories (age > 30d, importance < 0.3, access_count == 0)
5. **GC** (gc.py) — daily hard-delete of superseded memories older than 30 days
6. **Dream consolidation** (dream_consolidation.py) — nightly cross-domain relationship discovery

### Retrieval Pipeline
1. Query → embed (Ollama) → Qdrant vector search
2. Optional domain filter, importance boost, recency boost
3. Reranker model scores candidates
4. Top-K returned with payload (content, domain, tags, importance, access_count)

### Integration Surface
- **Claude Code hooks**: `UserPromptSubmit` (retrieve), `PostToolUse/Write/Edit` (observe),
  `Stop` (session snapshot)
- **MCP server**: `recall_search`, `recall_store`, `recall_timeline` tools
- **REST API**: FastAPI on port 8200 — `/store`, `/search`, `/retrieve/{id}`, `/health`,
  `/admin/*`, `/observe/file-change`, `/dashboard/*`
- **React dashboard**: Vite + Tailwind + DaisyUI — memory browser, graph view,
  metrics panels, activity feed

### Deployment
- Docker Compose on CasaOS (homelab)
- All models run locally on RTX 3090 (192.168.50.62)
- No cloud dependencies — fully air-gapped capable

---

## Key Known Weaknesses (Pre-Research)

These are suspected going in — research should confirm, quantify, or refute:

1. **No SDK** — no Python or JS package; integration requires raw HTTP or hook config
2. **Single-LLM bias** — hooks are Claude Code specific; no first-class support for other LLMs
3. **Self-hosting complexity** — requires 4 separate services (Qdrant, Neo4j, Redis, Postgres) + Ollama
4. **No hybrid retrieval** — pure vector search; no BM25 or keyword fallback
5. **Multi-user support is shallow** — user_id field exists but isolation UX is minimal
6. **No import/export** — no way to bulk-import existing notes or export memories as structured data
7. **Documentation** — primarily README-driven; no proper docs site or SDK reference

---

## Key Known Strengths (Pre-Research)

1. **Dual-store intelligence** — combining Qdrant (fast semantic search) + Neo4j (graph traversal)
   is rare in this space; most competitors pick one
2. **Full lifecycle pipeline** — decay, consolidation, hygiene, GC, dream consolidation —
   more sophisticated than any competitor we're aware of
3. **Local-first** — all compute runs on homelab; zero API costs, full privacy
4. **Hook integration depth** — captures context automatically without user intervention;
   most competitors require explicit `remember()` calls
5. **Causal + temporal memory** — auto-links memories via causal edges (caused_by, supports, contradicts)
6. **Observable** — Prometheus metrics, audit log, dashboard — more operational visibility
   than most open-source alternatives

---

## Competitors to Analyze

**Primary** (most comparable):
- **mem0** (github.com/mem0ai/mem0) — self-hostable, LLM-agnostic, Python SDK, growing fast
- **Zep** (getzep.com) — temporal memory, session-aware, enterprise focus
- **Letta / MemGPT** — OS-inspired hierarchical memory tiers, stateful agents

**Secondary** (partial overlap):
- **Langchain memory** (ConversationBufferMemory, VectorStoreRetrieverMemory, etc.)
- **OpenAI memory** (GPT-4 built-in memory — cloud, closed)
- **Claude Projects** (knowledge base — cloud, closed)
- **Chroma + custom** (DIY vector memory pattern)

**Adjacent** (worth surveying):
- **Obsidian + AI plugins** (personal knowledge, manual)
- **Notion AI** (document-based, managed)
- **Rewind.ai** (activity capture — consumer)

---

## Research Constraints

- Prefer live web data over training data for current feature sets — competitors ship fast
- Flag anything that may have changed since mid-2024 as needing live verification
- Focus on what is **actionable for Tim** — self-hosted, privacy-first, Claude Code user
- Do NOT recommend cloud-only solutions as improvements; self-hosted is a hard requirement
- Findings should be specific enough to generate a GitHub issue or architecture decision
