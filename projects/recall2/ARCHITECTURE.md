# Recall 2.0 Architecture

## Origin

This architecture was derived from 256 questions of frontier research conducted in
`../../recall-arch-frontier/`. The 10 key breakthroughs from Wave 22 synthesis and
the failure mode fix map from Q200 informed every design decision.

## Component Map

```
                    +------------------+
                    |   axum HTTP API  |  Port 8200
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
        +-----+----+  +-----+----+  +------+-----+
        | Dedup    |  | Hybrid   |  | Scoring    |
        | Pipeline |  | Search   |  | Engine     |
        +-----+----+  +-----+----+  +------+-----+
              |              |              |
   +----------+----------+   |   +----------+----------+
   |          |          |   |   |          |          |
+--+---+ +---+----+ +---+---+---+---+ +----+---+ +---+----+
| SHA  | | Sim    | | HNSW  | BM25  | | CO_RET | | Prov   |
| 256  | | Hash   | | Index | Index | | Graph  | | enance |
+--+---+ +---+----+ +---+---+---+---+ +----+---+ +---+----+
   |          |          |       |          |          |
   +----------+----------+-------+----------+----------+
              |                             |
        +-----+----+                 +------+-----+
        |   LMDB   |                 |   SQLite   |
        | (heed)   |                 | (rusqlite) |
        +----------+                 +------------+
```

## Embedded Components (No External Services)

| Component | Crate | Purpose | Research Ref |
|-----------|-------|---------|--------------|
| LMDB | `heed` | Primary KV store for memories, edges, embeddings | Q197 |
| SQLite | `rusqlite` | Structured queries, migrations, analytics | Q200 |
| fastembed-rs | `fastembed` | INT8 embedded inference (BGE-small-en-v1.5, 384-dim) | Q189 |
| instant-distance | `instant-distance` | HNSW vector index (ef=200, M=16) | Q197 |
| tantivy | `tantivy` | BM25 full-text search | Q231, Q247 |
| DashMap | `dashmap` | Concurrent in-memory CO_RETRIEVED cache | Q200 |

## Data Flow: Write Path

```
Store Request
  -> L0 SHA-256 exact dedup check (LMDB content_hash db)
  -> L1 SimHash near-dup check (64-bit, 8 bands x 8 bits, H<=6)
  -> Embed via fastembed-rs (BGE-small, 384-dim INT8)
  -> L2 HNSW ANN dedup check (cosine >= 0.92 = duplicate)
  -> Store: LMDB memories + embeddings dbs
  -> Index: HNSW add_point + tantivy index_memory
  -> SQLite: insert memories row
```

## Data Flow: Retrieval Path

```
Search Request
  -> Embed query via fastembed-rs
  -> Parallel: HNSW top-K + BM25 top-K
  -> RRF fusion: rrf_score = 1/(rank_bm25 + 60) + 1/(rank_hnsw + 60)
  -> For each result: compute behavioral score
     score = (cosine * 0.6 + co_gravity * 0.2 + importance * 0.2) * provenance_mult
  -> Emit CO_RETRIEVED events for result set pairs
  -> Return scored results
```

## CO_RETRIEVED Graph

The behavioral graph learns which memories are useful together. When memories A and B
appear in the same search result set, a CO_RETRIEVED event fires. Over time, frequently
co-retrieved pairs develop strong edges, boosting each other in future searches.

- Events collected via mpsc channel (non-blocking write path)
- Flush worker batches events every 15 minutes to LMDB + SQLite
- Weight update: `w = w + lr * (1 - w)` (bounded increment, lr=0.1)
- K-means bootstrap (K=200) seeds initial edges from Recall 1.0 corpus

## Deduplication Pipeline

Three-level dedup prevents storing redundant memories:

- **L0 (Exact)**: SHA-256 of normalized content. O(1) LMDB lookup.
- **L1 (Near-dup)**: SimHash with 64 random hyperplanes, 8 bands x 8 bits.
  Hamming distance <= 6 = near-duplicate.
- **L2 (Semantic)**: HNSW ANN search, cosine similarity >= 0.92 = semantic duplicate.

## Source Trust Provenance

5 tiers with multiplicative scoring impact:

| Tier | Multiplier | Examples |
|------|-----------|----------|
| UserDirect | 0.90 | `/learn`, `/anchor`, `/never` commands |
| VerifiedSystem | 0.80 | Session summaries, verified facts |
| ToolOutput | 0.50 | observe-edit.js extractions |
| AgentGenerated | 0.40 | Agent-produced content |
| Derived | 0.30 | Inferred/synthesized content |

## Health Signals

| Signal | What It Measures |
|--------|-----------------|
| S1: Top-K Consistency | HNSW stability — same query returns stable results |
| S2: Edge Density | CO_RETRIEVED graph coverage per user |
| S3: Bootstrap Bias | Ratio of synthetic vs organic edge weight |
| S4: Write Latency | p95 write-path latency |

## Failure Mode Fix Map (from Q200)

| Failure Mode | Mitigation |
|-------------|------------|
| Cold-start empty graph | K-means bootstrap with tiered seeding |
| Stale embeddings after model change | Migration re-embeds entire corpus |
| HNSW index corruption | Periodic rebuild from LMDB source of truth |
| SimHash false negatives | L2 HNSW check catches what L1 misses |
| CO_RETRIEVED event storm | mpsc batching + session dedup |
