# Design Principles — Recall 2.0

These are axioms. If a design decision violates a principle, the decision loses — not the principle.
Principles can only be changed by explicit human decision with documented rationale.

**Last updated**: 2026-03-16

---

## P1 — No Importance Scores

The system never uses LLM-assigned importance scores for any decision: eviction, routing, decay rate, retrieval ranking, or consolidation priority.

**Why**: Importance is a write-time prior. Causal relevance is a property of a memory-task pair that doesn't exist until retrieval time. A score assigned when a memory is created cannot encode its relevance to a future task that doesn't exist yet. All decisions must be based on demonstrated behavior (access frequency, co-retrieval patterns, recency of use) — not predicted importance.

---

## P2 — Retrieval Must Reinforce

Every successful retrieval operation must reinforce the retrieved memories. This is not a separate write call — it must be a property of the retrieval mechanism itself.

**Why**: Biological memory strengthens patterns through use. AI memory systems that treat retrieval as a read-only operation produce static memory with no learning signal from usage. A system that doesn't reinforce cannot improve with use.

---

## P3 — Decay Is Physics, Not Schedule

Memory activation decays continuously. Decay is computed from timestamps at read time — not applied by a background job on a schedule. No cron job, no ARQ worker, no scheduled decay pass.

**Why**: Scheduled decay is a discrete approximation of a continuous process. The approximation introduces timing artifacts, requires a running background process, and creates windows where memories that should have faded are still retrievable. Timestamp arithmetic on read is exact, stateless, and requires no infrastructure.

---

## P4 — Consistency Without Coordination

Multi-machine write conflicts are resolved by the data structure, not by a coordination protocol. No vector clocks, no leader election, no distributed locking, no outbox flush workers.

**Why**: Coordination protocols add latency, create failure modes, and require all machines to be reachable to make progress. CRDTs make conflict resolution a mathematical property of the data structure — conflicts are impossible by design. This is the correct solution to the distributed writes problem for a personal memory system.

---

## P5 — The Stack Serves the Problem

Technology choices are made based on what best serves each component's requirements. Tim's existing language preferences, familiarity, and tooling choices are inputs to the decision — not constraints on the decision. With AI as the primary implementer, the human's language preference is irrelevant to correctness.

**Why**: General-purpose tools (Qdrant, Neo4j, Redis, PostgreSQL) were not designed for this problem. Using them by default means inheriting their architectural mismatches. Each component gets the right tool — which may be Rust, Go, Julia, or Python depending on the requirement.

---

## P6 — Behavioral Evidence Over Semantic Similarity

The primary routing and retrieval signal is behavioral — what has been retrieved together, how often, in what contexts. Semantic similarity (cosine ANN) is the fallback for cold-path retrieval when behavioral evidence is insufficient.

**Why**: Semantic similarity is a proxy for relevance. Behavioral co-retrieval is a direct measurement of demonstrated relevance. Proxies are correct on average; measurements are correct for this specific corpus and this specific user.

---

## P7 — Background Consolidation Is Mandatory

The system runs a consolidation process during idle time that builds higher-order abstractions from raw memories. This is not optional and is not triggered manually. It runs continuously when the system is not otherwise occupied.

**Why**: Raw memories accumulate noise, redundancy, and low-level specificity. Useful long-term memory requires abstraction — patterns extracted from instances. Without background consolidation, memory systems degrade in precision over time as the corpus grows. This is the software equivalent of sleep.

---

## P8 — Health Measures Retrieval Quality, Not Infrastructure

The health system answers "is the memory system retrieving the right things?" — not "are the services reachable?" Infrastructure health is table stakes. Retrieval quality health is the actual product.

**Why**: A system where all services respond 200 OK but the retrieval algorithm is returning the wrong tier of memories is broken. Infrastructure monitoring doesn't catch this. Retrieval quality signals (precision at K, working-set coverage, behavioral graph density) are the correct metrics.

---

## P9 — Migration Path Is Not Optional

The system must provide a migration path from Recall 1.0. 22,423 existing vectors, existing Neo4j graph, existing PostgreSQL metadata. None of this is discarded.

**Why**: Tim's Recall 1.0 memories represent months of accumulated context. Starting fresh is not acceptable. The new system must either import the existing corpus or provide a bridge layer that makes Recall 1.0 data queryable through the new interface.

---

## Candidate Principles (Not Yet Decided)

These have been proposed but are not locked:

- **CP1**: The system should run entirely locally — no external API dependencies for core memory operations. (Open question: does embedding inference count? Ollama is local but it's still a model call.)
- **CP2**: The MCP interface contract must be backward compatible with Recall 1.0 so existing hooks work unchanged.
- **CP3**: The system should be buildable by a single developer (with AI assistance) — no components that require a team to maintain.
