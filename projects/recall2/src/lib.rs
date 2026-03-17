//! Recall 2.0 — library root.
//!
//! Re-exports all public modules for use by the binary and tests.

pub mod api;
pub mod config;
pub mod dedup;
pub mod embedding;
pub mod error;
pub mod graph;
pub mod health;
pub mod index;
pub mod migration;
pub mod provenance;
pub mod storage;

use std::sync::Arc;

use tokio::sync::{mpsc, RwLock};

use crate::config::AppConfig;
use crate::embedding::EmbeddingEngine;
use crate::graph::CoRetrievedGraph;
use crate::index::{BM25Index, HnswIndex};
use crate::storage::{LmdbStore, SqliteStore};

/// Shared application state, wrapped in `Arc` and passed to all handlers.
///
/// Design rationale (Q200): single shared state avoids the service-mesh overhead
/// of the original 6-container architecture.
#[derive(Debug)]
pub struct AppState {
    /// LMDB key-value store — memories, embeddings, content hashes, co-edges.
    pub db: Arc<LmdbStore>,

    /// SQLite — structured queries, migrations, analytics.
    pub sql: Arc<SqliteStore>,

    /// Embedding engine (fastembed-rs, BGE-small-en-v1.5, 384-dim).
    pub embedder: Arc<EmbeddingEngine>,

    /// HNSW vector index (instant-distance, ef=200, M=16).
    pub index: Arc<RwLock<HnswIndex>>,

    /// BM25 full-text search index (tantivy).
    pub fts: Arc<RwLock<BM25Index>>,

    /// CO_RETRIEVED behavioral graph (DashMap in-memory).
    pub graph: Arc<CoRetrievedGraph>,

    /// Channel sender for CO_RETRIEVED events — non-blocking write path.
    pub co_retrieved_tx: mpsc::Sender<graph::CoRetrievedEvent>,

    /// Application configuration.
    pub config: AppConfig,
}
