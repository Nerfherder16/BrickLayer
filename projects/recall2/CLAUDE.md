# Recall 2.0 — Session Context

## What This Is

Recall 2.0 is a self-hosted AI memory system — a single Rust binary that replaces the
6-service Docker stack of Recall 1.0 (Qdrant + Neo4j + PostgreSQL + Redis + Ollama + ARQ).

The architecture was derived from 256 questions of frontier research. Key references:

- Full synthesis: `../../recall-arch-frontier/findings/synthesis.md`
- Build plan / failure map: `../../recall-arch-frontier/findings/Q200.md`
- HNSW tuning: `../../recall-arch-frontier/findings/Q197.md`
- Hybrid retrieval validation: `../../recall-arch-frontier/findings/Q231.md`, `Q247.md`
- Embedding model selection: `../../recall-arch-frontier/findings/Q189.md`

## Key Architectural Decisions

| Decision | Choice | Research Backing |
|----------|--------|-----------------|
| Embedding model | BGE-small-en-v1.5 (384-dim, INT8) | Q189: best latency/quality for single-binary |
| Vector index | HNSW via instant-distance (ef=200, M=16) | Q197: optimal for 22K corpus |
| Hybrid retrieval | BM25 + dense + RRF fusion (k=60) | Q231/Q247: +18.5% MRR for identifiers |
| KV store | LMDB via heed | Q200: embedded, ACID, zero-copy reads |
| Structured queries | SQLite via rusqlite | Q200: migrations, analytics |
| Near-dup detection | SimHash 64-bit, 8 bands x 8 bits, H<=6 | Q200: Phase 2 validated threshold |
| Behavioral graph | CO_RETRIEVED with mpsc batching | Q200: Phase 3, bounded weight update |
| Scoring formula | cos*0.6 + co_grav*0.2 + imp*0.2 * prov | Q200: Phase 3-4 formula |
| Provenance tiers | 5 levels (0.9 to 0.3 multiplier) | Q200: Phase 4 |

## Build Phase Status

- [ ] Phase 1: Foundation (Days 1-5) — PENDING
- [ ] Phase 2: Deduplication (Days 5-10) — PENDING
- [ ] Phase 3: Behavioral Scoring (Days 10-21) — PENDING
- [ ] Phase 4: Source Trust Provenance (Days 21-28) — PENDING
- [ ] Phase 5: Operational Layer (Days 28-35) — PENDING

## Development Commands

```bash
# Build
cargo build

# Run tests
cargo test

# Run with debug logging
RUST_LOG=recall2=debug cargo run

# Release build
cargo build --release
```

## Crate Notes

- `heed` v0.20: uses `Env::open()` with `EnvOpenOptions`, named databases via `env.open_database()`
- `instant-distance` v0.6: `Builder::default()` then `.build(points)`, search via `search()`
- `fastembed` v4: `TextEmbedding::try_new(InitOptions { model_name: EmbeddingModel::BGESmallENV15, .. })`
- `tantivy` v0.21: schema builder pattern, `Index::create_in_dir()` or `Index::create_in_ram()`

## Build Strategy (LOCKED — Tim's explicit instruction)

**Infra-first, one-shot build.**

1. Design hook contract → design storage layout → design API contract → write phase build instructions
2. Each phase becomes a self-contained build instruction document so complete that the entire build can be executed in a single Claude session
3. **DO NOT write implementation code until all phase build instructions are finalized and locked**
4. Hooks are being redesigned from scratch (new hooks, parallel to Recall 1.0 — do not touch running system)
5. Recall 2.0 runs alongside Recall 1.0 during development; cut over when ready (new VM eventually)

Current status: **Hook design in progress**

## Code Retrieval — jCodeMunch First

Use `jcodemunch-mcp` for all symbol-level access in this codebase. Recall 2.0 is a Rust project — prefer targeted retrieval over reading whole files.

- `search_symbols` + `get_symbol_source` instead of `Read` for individual functions/structs/traits
- `get_blast_radius` before touching core modules (storage, scoring, retrieval)
- `get_call_hierarchy` to trace data flow through the pipeline
- Only use `Read` when full file context is genuinely needed

## Source Authority

This project follows the same authority hierarchy as BrickLayer:

| Tier | Source | Who edits |
|------|--------|-----------|
| Tier 1 | ARCHITECTURE.md, BUILD_PLAN.md | Human — ground truth |
| Tier 2 | Cargo.toml, config/ | Human + agent |
| Tier 3 | src/ | Agent — implementation |
