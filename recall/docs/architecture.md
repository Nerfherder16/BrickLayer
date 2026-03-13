# Recall System Architecture

## Overview

Recall is a FastAPI-based memory system that provides persistent, queryable memory for
Claude Code sessions. Memories are stored as text + embeddings, linked in a graph, cached
for fast retrieval, and ranked by relevance using an ML model.

## Service Stack

| Service | Role | Port |
|---------|------|------|
| FastAPI (Recall) | REST API, orchestration | 8200 |
| Qdrant | Vector database, semantic search | 6333 |
| Neo4j | Graph database, entity/causal links | 7474/7687 |
| Redis | Cache, dedup keys, session state | 6379 |
| PostgreSQL | Audit log, signal history, training data | 5432 |
| Ollama | LLM inference (qwen3:14b + qwen3-embedding:0.6b) | 11434 (remote) |

Ollama runs on a separate GPU host at 192.168.50.62:11434 (RTX 3090).

## Key API Endpoints

```
POST /store                  — Store a new memory
POST /search                 — Semantic + graph search
GET  /health                 — System health check (all backends)
POST /ops/consolidate        — Trigger memory deduplication
POST /ops/decay              — Apply importance decay
GET  /ops/stats              — System statistics
POST /rehydrate              — Session memory rehydration
```

## Retrieval Pipeline (src/core/retrieval.py)

1. Embed query via Ollama (qwen3-embedding:0.6b)
2. Vector search in Qdrant (top-K candidates)
3. Graph expansion in Neo4j (related entities)
4. Score fusion (vector score + graph score + recency)
5. ML reranking via qwen3:14b
6. Return top-N results

## Write Pipeline

1. Signal classification (src/core/signal_classifier.py) — score importance
2. Write guard check (src/core/write_guard.py) — Redis-based dedup
3. Embedding generation (src/core/embeddings.py) — Ollama, with TTL cache
4. Qdrant upsert — vector store
5. Neo4j upsert — graph node + auto-link (src/core/auto_linker.py)
6. PostgreSQL audit log — immutable record

## Memory Lifecycle

```
Store → Signal classify → Write guard → Embed → Vector store → Graph store → Audit
                                                                      ↓
Retrieve ← Rerank ← Score fusion ← Graph expand ← Vector search ← Query embed
                                                                      ↓
                                                              Decay → Consolidate
```

## Domain Isolation

Memories are partitioned by `domain` field. Cross-domain reads are blocked at the query
layer. Domain isolation is enforced in both Qdrant (filter on domain) and Neo4j
(node property constraint).

## Concurrency Model

- FastAPI runs with multiple async workers (uvicorn)
- Write guard uses Redis atomic SETNX for dedup locking
- Consolidation is a background operation triggered via /ops/consolidate
- Embeddings are cached in Redis with TTL to avoid redundant Ollama calls
