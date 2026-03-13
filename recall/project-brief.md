# Recall — Autoresearch Project Brief

## What Recall Is

Recall is a self-hosted memory system for Claude Code. It stores, retrieves, and manages
memories across Claude Code sessions via a set of hooks that fire automatically. The system
uses semantic search (Qdrant), graph relationships (Neo4j), caching (Redis), audit logging
(PostgreSQL), and local LLM inference (Ollama) to provide persistent, queryable memory.

**Live instance**: http://192.168.50.19:8200
**Source**: C:/Users/trg16/Dev/Recall
**GitHub**: https://github.com/Nerfherder16/System-Recall

## Architecture

```
Claude Code hooks
    │
    ▼
FastAPI backend (port 8200)
    ├── /store      — write a memory
    ├── /search     — semantic + graph search
    ├── /health     — system health
    └── /ops/*      — admin operations (consolidate, decay, etc.)
    │
    ├── Qdrant       — vector embeddings for semantic search
    ├── Neo4j        — graph for entity relationships + causal links
    ├── Redis        — TTL cache, dedup keys, session state
    ├── PostgreSQL   — audit log, signal history, reranker training data
    └── Ollama       — qwen3:14b (reranker), qwen3-embedding:0.6b (embeddings)
```

## Key Modules

| Module | Path | Purpose |
|--------|------|---------|
| Route handlers | `src/api/routes/` | FastAPI endpoints |
| Retrieval pipeline | `src/core/retrieval.py` | Semantic retrieval orchestration |
| Embedding generation | `src/core/embeddings.py` | Ollama embedding calls + cache |
| Memory consolidation | `src/core/consolidation.py` | Dedup/merge near-duplicate memories |
| ML reranker | `src/core/reranker.py` | Score reranking via qwen3:14b |
| Write guard | `src/core/write_guard.py` | Prevent duplicate stores |
| Auto-linker | `src/core/auto_linker.py` | Auto-create Neo4j relationships |
| Signal classifier | `src/core/signal_classifier.py` | Classify memory importance |
| Workers | `src/workers/` | Background task workers |

## Existing Test Infrastructure

| Suite | Path | What it tests |
|-------|------|---------------|
| Integration tests | `tests/integration/` | Live API (pytest, hits 192.168.50.19:8200) |
| Core unit tests | `tests/core/` | Module-level unit tests |
| Load test runner | `monitor/loadtest/` | Persona-based load tests |
| Stress suite | `tests/simulation/suites/` | stress, retrieval_quality, durability |

## Research Goal

Stress-test the Recall system to find its failure boundaries across three axes:
1. **Performance** — at what load does it degrade or fail?
2. **Correctness** — do guarantees (dedup, isolation, decay) hold under concurrency?
3. **Quality** — does the source code have latent bugs (N+1, race conditions, cache errors)?
