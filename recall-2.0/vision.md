# Vision — Recall 2.0

**Last updated**: 2026-03-16

---

## What We Are Building

The best AI memory system ever designed.

Not an improvement on Recall 1.0. Not a better RAG pipeline. Not a smarter vector database wrapper. A ground-up design that starts from what memory actually is and builds the right system for that problem — without inheriting assumptions from database engineering, from LLM tooling, or from any existing memory framework.

---

## What It Is Not

- **Not a cognitive mirror.** The system does not encode how Tim thinks so Claude thinks like Tim. Human cognition is evolutionarily optimized for the wrong environment. The goal is Tim's context + Claude's reasoning — not Tim's reasoning.
- **Not a RAG pipeline.** Retrieval-Augmented Generation is a search problem. Memory is not a search problem. Memory involves reinforcement, decay, consolidation, and interference — none of which RAG addresses.
- **Not a wrapper around existing databases.** Qdrant, Neo4j, Redis, PostgreSQL are general-purpose tools. They were not designed for this problem. Using them as the foundation means inheriting their architectural mismatches.
- **Not importance-score based.** Importance is a write-time prior assigned by an LLM based on how significant content seems at the moment of storage. It has no relationship to causal relevance at retrieval time. The best memory system does not use importance scores for any decision.

---

## The Five Core Operations

A memory system has exactly five jobs. Everything else is implementation detail.

| Operation | What it means | Where current systems fail |
|---|---|---|
| **Write** | Store information durably, deduplicate intelligently, handle concurrent writers | Handled tolerably by most systems |
| **Decay** | Forget the right things at the right rate | Scheduled cron jobs — wrong model |
| **Retrieve** | Surface relevant information with precision and speed | Handled tolerably, but static |
| **Reinforce** | Strengthen what gets used, weaken what doesn't | Almost entirely absent |
| **Consolidate** | Build higher-order structure from raw memories over time | Absent or LLM-summarization only |

The ideal system is one where **decay, retrieval, and reinforcement are the same physical operation** — not three separate systems bolted together.

---

## The Target

A system where:

1. Every retrieval automatically reinforces the retrieved memory and activates related ones — no separate write call
2. Decay is continuous and physics-based — computed from timestamps on read, not run on a schedule
3. Behavioral relationships between memories are encoded in the storage substrate, not as explicit graph edges in a separate database
4. Multi-machine consistency is guaranteed by the data structure, not by a coordination protocol
5. Background consolidation runs during idle time, building abstractions from raw memories without being triggered manually
6. No importance scores appear anywhere in the system
7. The health monitoring layer measures retrieval quality, not just infrastructure uptime

---

## The Primary User

Tim. One human. Two machines (casaclaude, proxyclaude) writing concurrently. One AI (Claude) reading and writing via hooks and MCP. The system must handle concurrent writes without coordination overhead, surface relevant memories within the Claude context window latency budget, and improve with use rather than just accumulating.

---

## Open Vision Questions

- [ ] Does this system have a public API for other users, or is it designed as a personal system only?
- [ ] What is the portability requirement? Must it run on Tim's specific homelab, or should it run anywhere?
- [ ] What is the migration path from Recall 1.0? Hard cutover or gradual transition?
- [ ] Is the MCP interface contract identical to Recall 1.0 (backward compatible) or redesigned?
- [ ] Open source? If so, what license and what's the adoption story?
