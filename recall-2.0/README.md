# Recall 2.0 — Design Workspace

**Status**: Ideation / Pre-Frontier
**Goal**: Design the best AI memory system ever built, from first principles, before writing a line of code.

This folder is a living design document. Add, edit, remove freely. Nothing here is final until it moves to `decisions/decided.md`.

---

## Folder Map

```
recall-2.0/
  README.md               ← this file — navigation + rules
  vision.md               ← what we're building and why (the north star)
  principles.md           ← non-negotiable axioms — design decisions that can't be violated
  competitive.md          ← what exists today and exactly where each system fails
  unknowns.md             ← known unknowns — things we need to figure out before building

  architecture/
    overview.md           ← high-level system map
    substrate.md          ← storage substrate (Hopfield, LMDB, etc.)
    write-path.md         ← write pipeline (dedup, consistency, concurrent writes)
    retrieval.md          ← retrieval architecture (tiers, routing, reinforcement)
    decay.md              ← decay model (continuous physics, not scheduled jobs)
    consolidation.md      ← background consolidation (the "sleep" equivalent)
    consistency.md        ← multi-machine consistency (CRDTs)
    injection.md          ← how memories reach Claude (context injection format)
    health.md             ← observability and retrieval quality monitoring

  decisions/
    decided.md            ← locked decisions with rationale
    open.md               ← active open questions — need resolution before building
    rejected.md           ← approaches considered and killed, and exactly why

  questions/
    frontier.md           ← growing question bank for the Frontier session
    research.md           ← questions needing external research (papers, benchmarks)
```

---

## How to Use This

- **Ideating**: add to `unknowns.md` or `questions/frontier.md` — don't filter, just capture
- **Deciding**: move from `decisions/open.md` → `decisions/decided.md` with rationale
- **Killing an idea**: move to `decisions/rejected.md` with the reason — preserves the thinking
- **Architecture changes**: edit the relevant `architecture/*.md` file directly
- **Principles**: `principles.md` is the highest authority — if a design decision violates a principle, the decision loses, not the principle

---

## Current State

Foundation is complete. Vision, principles, competitive analysis, full architecture docs, known unknowns, open decisions, and question bank are all in place.

**Pre-Frontier checklist:**
- [x] `vision.md` — complete
- [x] `principles.md` — 9 locked principles (P1-P9), 3 candidate principles (CP1-CP3)
- [x] `competitive.md` — all current systems analyzed (MemGPT, mem0, Zep, LangChain, Recall 1.0)
- [x] `unknowns.md` — 20 known unknowns across substrate, retrieval, consistency, migration, and open frontiers
- [x] `decisions/open.md` — 12 open decisions (OD-01 through OD-12)
- [x] `decisions/rejected.md` — 6 rejected approaches with rationale
- [x] `questions/frontier.md` — 47 Frontier questions across 10 domains
- [x] `questions/research.md` — 18 research questions (papers, benchmarks, implementations)
- [ ] **Remaining**: Answer open decisions in `decisions/open.md` based on empirical research before locking architecture
- [ ] **Remaining**: Competitive analysis gaps (A-MEM, GraphRAG, HyDE, continual learning literature) — see `competitive.md`
- [ ] **Remaining**: Decide on open architecture questions (OD-01 through OD-12) — many require benchmarking

**Ready to fire Frontier Wave 1.** The question bank covers all major architecture domains.
