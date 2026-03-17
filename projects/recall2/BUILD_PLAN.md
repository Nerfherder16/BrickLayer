# Recall 2.0 Build Plan

5 phases, 35 days, 7 launch conditions. Derived from Q200 construction schedule.

## Phase 1: Foundation (Days 1-5)

Single binary + hook compatibility + migration scaffold.

- [ ] LMDB storage layer with named databases
- [ ] SQLite schema + migration runner
- [ ] fastembed-rs engine initialization (BGE-small-en-v1.5, 384-dim)
- [ ] HNSW index build/load/persist cycle
- [ ] tantivy BM25 index setup
- [ ] axum HTTP server with Recall 1.0-compatible endpoints
- [ ] Hybrid search (BM25 + HNSW + RRF fusion)
- [ ] Config loading from TOML
- [ ] End-to-end: store a memory, search for it, get it back

**Exit criteria**: `cargo test` passes, single binary starts, store+search works.

## Phase 2: Deduplication (Days 5-10)

L0 exact + L1 near-dup + L2 semantic dedup.

- [ ] L0: SHA-256 content hash with normalization
- [ ] L1: SimHash (64-bit, 8 bands x 8 bits, H<=6 threshold)
- [ ] L2: HNSW ANN check (cosine >= 0.92)
- [ ] Three-level pipeline in store handler
- [ ] Dedup metrics (rejected count per level)

**Exit criteria**: Duplicate content rejected at each level, unique content passes through.

## Phase 3: Behavioral Scoring (Days 10-21)

CO_RETRIEVED graph + scoring formula.

- [ ] CO_RETRIEVED event emission on search
- [ ] mpsc channel + flush worker (15-min batches)
- [ ] DashMap in-memory graph with bounded weight update
- [ ] Session deduplication (same pair in same session = 1 event)
- [ ] K-means bootstrap job (K=200, tiered seeding)
- [ ] Scoring formula: `(cos*0.6 + co_grav*0.2 + imp*0.2) * prov_mult`
- [ ] Integration: search results ranked by behavioral score

**Exit criteria**: Search results improve with usage patterns. Bootstrap seeds graph on migration.

## Phase 4: Source Trust Provenance (Days 21-28)

5-tier provenance system.

- [ ] SourceProvenance enum with multipliers
- [ ] Hook-type to provenance auto-mapping
- [ ] Provenance stored per memory in LMDB + SQLite
- [ ] Scoring formula includes provenance multiplier
- [ ] API returns provenance in search results

**Exit criteria**: UserDirect memories rank higher than Derived for same cosine similarity.

## Phase 5: Operational Layer (Days 28-35)

Health signals + dashboard compatibility.

- [ ] S1: Top-K consistency ratio
- [ ] S2: CO_RETRIEVED edge density
- [ ] S3: Bootstrap bias ratio
- [ ] S4: Write-path latency p95
- [ ] Health endpoint (`GET /health`)
- [ ] Admin endpoints (migrate, rebuild index, flush graph)
- [ ] Structured logging with tracing spans
- [ ] Graceful shutdown (flush pending CO_RETRIEVED events)

**Exit criteria**: All 4 health signals reporting. Graceful shutdown preserves data.

## 7 Launch Conditions

1. All existing hooks work without modification against Recall 2.0 API
2. Search quality >= Recall 1.0 (measured by MRR on test queries)
3. Write latency p95 < 50ms (excluding embedding time)
4. Cold start < 5 seconds (excluding model download)
5. Memory usage < 512MB for 25K memories
6. Zero data loss on graceful shutdown
7. Migration from Recall 1.0 completes without manual intervention
