//! Recall 1.0 corpus importer.
//!
//! Connects to Recall 1.0 PostgreSQL, reads all memories, generates
//! embeddings via fastembed-rs, stores in LMDB + SQLite, and triggers
//! K-means bootstrap for CO_RETRIEVED edge seeding.
//!
//! This is a one-shot migration job. Progress is tracked via tracing events.

use std::sync::Arc;

use anyhow::Result;
use tracing::{info, warn};

use crate::embedding::EmbeddingEngine;
use crate::graph::CoRetrievedGraph;
use crate::storage::{LmdbStore, SqliteStore};

/// Import corpus from Recall 1.0 PostgreSQL.
///
/// Steps:
/// 1. Connect to source PostgreSQL
/// 2. Read all memories
/// 3. For each memory: embed, store, index
/// 4. Run K-means bootstrap for CO_RETRIEVED edges
///
/// Returns (memories_migrated, edges_seeded).
pub async fn import_from_recall1(
    _source_url: &str,
    _db: Arc<LmdbStore>,
    _sql: Arc<SqliteStore>,
    _embedder: Arc<EmbeddingEngine>,
    _graph: Arc<CoRetrievedGraph>,
    _kmeans_k: usize,
) -> Result<(u64, u64)> {
    // TODO: Phase 1 — implement full migration pipeline
    //
    // The implementation will:
    //
    // 1. Connect to Recall 1.0 PostgreSQL using reqwest or a pg client
    //    (prefer reqwest hitting Recall 1.0's API to avoid a direct pg dependency)
    //
    // 2. Paginate through all memories:
    //    GET /recall/search?limit=100&offset=0 (or direct SQL if needed)
    //
    // 3. For each batch:
    //    a. Embed via fastembed-rs (batch embed for efficiency)
    //    b. Store in LMDB: memory record + embedding + content hash
    //    c. Register SimHash bands
    //    d. Store in SQLite: memories row
    //    e. Index in HNSW + BM25
    //
    // 4. After all memories imported, run K-means bootstrap:
    //    bootstrap_kmeans(db, sql, graph, kmeans_k).await
    //
    // 5. Report progress via tracing:
    //    info!(batch = n, total = total, "Migration progress")

    warn!("Migration not yet implemented — this is a scaffold");
    info!("To implement migration, see migration/importer.rs TODO");

    Ok((0, 0))
}
