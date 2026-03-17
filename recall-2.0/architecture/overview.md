# Architecture Overview — Recall 2.0

Current thinking. Not final. Everything here is subject to change until it moves to `decisions/decided.md`.

**Last updated**: 2026-03-16

---

## High-Level System Map

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Code                          │
│         (UserPromptSubmit / PostToolUse / Stop hooks)       │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP / HTTP
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Surface                            │
│           store / retrieve / session / health               │
│                   (Go or Rust/Axum)                         │
└──────┬──────────────┬──────────────────────┬────────────────┘
       │              │                      │
       ▼              ▼                      ▼
┌────────────┐ ┌─────────────┐      ┌────────────────┐
│  Write     │ │  Retrieval  │      │  Background    │
│  Pipeline  │ │  Engine     │      │  Consolidation │
│  (Rust)    │ │  (Rust)     │      │  (Python/LLM)  │
└──────┬─────┘ └──────┬──────┘      └───────┬────────┘
       │              │                     │
       ▼              ▼                     │
┌─────────────────────────────────────────────────────────────┐
│                    Storage Substrate                        │
│                                                             │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │  Hopfield / Dense   │    │  LMDB                      │  │
│  │  Associative Memory │    │  (metadata, access logs,   │  │
│  │  (hot path)         │    │   session records)         │  │
│  │  PyTorch on RTX3090 │    │  (Rust — heed crate)       │  │
│  └─────────────────────┘    └────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │  Cold Vector Store  │    │  CRDT State                │  │
│  │  (full corpus ANN)  │    │  (multi-machine sync)      │  │
│  │  TBD — Qdrant       │    │  (Rust — crdts crate)      │  │
│  │  or custom?         │    └────────────────────────────┘  │
│  └─────────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Embedding Layer                            │
│              Python + PyTorch + Ollama                      │
│              qwen3-embedding:0.6b (or TBD)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### Write Pipeline
- Three-layer deduplication: L0 (exact hash) → L1 (SimHash near-duplicate) → L2 (semantic ANN)
- CRDT write to the shared state store
- Embed via Ollama if L0 and L1 pass
- Write to Hopfield hot layer + cold vector store
- Log access event to LMDB

### Retrieval Engine
- Multi-tier routing: Session cache → LLPC working set → Hopfield hot layer → Cold ANN
- Reinforcement on retrieval: update Hopfield weights, increment access counter in LMDB
- Decay computed from LMDB timestamps at read time — no background job
- Return results with activation levels, not importance scores

### Storage Substrate
- **Hopfield layer**: associative memory for hot working set. Retrieval = pattern completion. Reinforcement = energy well deepening. Decay = energy landscape flattening over time.
- **LMDB**: metadata, access logs, session records, CRDT state. Embedded, no server, memory-mapped.
- **Cold vector store**: full corpus ANN for semantic fallback. Qdrant or custom — TBD.
- **CRDT state**: OR-Set for memory collection, G-Counter for access frequency, LWW-Register for values.

### Background Consolidation
- Runs during idle time (no active requests for N minutes)
- Traverses memory clusters in Hopfield landscape
- Identifies patterns across episodic memories
- Generates summary/abstraction nodes via local LLM
- Writes abstractions back as first-class memories with source links
- Does NOT run on a schedule — purely event-driven (idle detection)

### Embedding Layer
- Remains Python/PyTorch — ecosystem lives here
- qwen3-embedding:0.6b on Ollama, RTX 3090 — current baseline
- Embedding model choice is an open question (see decisions/open.md)

### API Surface
- MCP tools: `recall_store`, `recall_retrieve`, `recall_search`, `recall_timeline`
- HTTP endpoints for hooks
- Health endpoint that reports retrieval quality signals, not just uptime
- Language: Go or Rust/Axum — TBD

---

## What This Replaces from Recall 1.0

| Recall 1.0 Component | Recall 2.0 Equivalent | Notes |
|---|---|---|
| Qdrant | Hopfield (hot) + Cold store (TBD) | Qdrant may survive as the cold store |
| Neo4j | Encoded in Hopfield weight matrix | Behavioral graph is implicit in weights |
| Redis | CRDT state + LMDB hot cache | No TTL-based expiry needed |
| PostgreSQL | LMDB | Metadata only, no ACID needed |
| ARQ decay worker | Timestamp arithmetic on read | No background process |
| Neo4j spreading activation | Hopfield dynamics | Same effect, correct substrate |
| CO_RETRIEVED flush worker | Hopfield reinforcement on retrieval | Same effect, automatic |

---

## Unresolved Architecture Questions

See `decisions/open.md` for the full list. Key ones:

- Is Qdrant the right cold vector store, or do we build custom?
- Where does the Hopfield layer live — in-process with the API, or as a separate service?
- How does the Hopfield network handle online learning (new memories added to an existing network)?
- What's the right capacity for the Hopfield hot layer vs. cold layer split?
- Does the CRDT model handle the full consistency requirement or are there edge cases?
