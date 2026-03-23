//! Recall 2.0 — Self-hosted AI memory system.
//!
//! Single Rust binary replacing a 6-service Docker stack.
//! Architecture derived from 256 questions of frontier research.

use std::sync::Arc;

use anyhow::Result;
use tokio::sync::{mpsc, RwLock};
use tracing::{info, warn};

use recall2::api;
use recall2::config::AppConfig;
use recall2::embedding::EmbeddingEngine;
use recall2::graph::{CoRetrievedGraph, FlushWorker};
use recall2::index::{BM25Index, HnswIndex};
use recall2::storage::{LmdbStore, SqliteStore};
use recall2::AppState;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "recall2=info,tower_http=info".into()),
        )
        .init();

    info!("Recall 2.0 starting up");

    // Load configuration
    let config = AppConfig::load()?;
    info!(port = config.server.port, data_dir = %config.storage.data_dir, "Configuration loaded");

    // Ensure data directory exists
    std::fs::create_dir_all(&config.storage.data_dir)?;

    // Open LMDB
    let db = Arc::new(LmdbStore::open(&config.storage.data_dir)?);
    info!("LMDB opened");

    // Open SQLite and run migrations
    let sql = Arc::new(SqliteStore::open(&config.storage.data_dir)?);
    sql.run_migrations()?;
    info!("SQLite opened, migrations applied");

    // Initialize embedding engine (lazy — model downloads on first embed call)
    let embedder = Arc::new(EmbeddingEngine::new(&config.embedding)?);
    info!(model = %config.embedding.model, "Embedding engine initialized");

    // Build or load HNSW index
    let hnsw = HnswIndex::load_or_build(&config.storage.data_dir, &config.hnsw, &db)?;
    let index = Arc::new(RwLock::new(hnsw));
    info!("HNSW index ready");

    // Initialize BM25 full-text index
    let bm25 = BM25Index::open_or_create(&config.storage.data_dir)?;
    let fts = Arc::new(RwLock::new(bm25));
    info!("BM25 index ready");

    // Initialize CO_RETRIEVED graph
    let graph = Arc::new(CoRetrievedGraph::new());

    // Start CO_RETRIEVED flush worker
    let (co_tx, co_rx) = mpsc::channel(10_000);
    let flush_worker = FlushWorker::new(
        co_rx,
        Arc::clone(&graph),
        Arc::clone(&db),
        Arc::clone(&sql),
        config.graph.flush_interval_secs,
    );
    tokio::spawn(async move {
        if let Err(e) = flush_worker.run().await {
            warn!(error = %e, "CO_RETRIEVED flush worker exited with error");
        }
    });
    info!(
        interval_secs = config.graph.flush_interval_secs,
        "CO_RETRIEVED flush worker started"
    );

    // Build application state
    let state = Arc::new(AppState {
        db,
        sql,
        embedder,
        index,
        fts,
        graph,
        co_retrieved_tx: co_tx,
        config: config.clone(),
    });

    // Build axum router
    let app = api::router(state);

    // Start server
    let addr = format!("{}:{}", config.server.host, config.server.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    info!(addr = %addr, "Recall 2.0 listening");

    axum::serve(listener, app).await?;

    Ok(())
}
