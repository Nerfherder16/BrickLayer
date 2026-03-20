//! HTTP request handlers for the Recall 2.0 API.
//!
//! Write path: L0 check -> L1 check -> embed -> L2 check -> store -> index
//! Read path: embed query -> hybrid search -> score -> return

use std::sync::Arc;
use std::time::Instant;

use axum::extract::{Path, State};
use axum::Json;
use chrono::Utc;
use tracing::{debug, info, warn};
use uuid::Uuid;

use crate::api::types::*;
use crate::dedup::{sha256_content_hash, SimHash};
use crate::error::{Recall2Error, Recall2Result};
use crate::graph::{compute_score, CoRetrievedEvent};
use crate::index::hybrid_search;
use crate::provenance::SourceProvenance;
use crate::AppState;

/// Store a new memory.
///
/// Write path:
/// 1. L0 SHA-256 exact dedup check
/// 2. Embed via fastembed-rs
/// 3. L1 SimHash near-dup check
/// 4. L2 HNSW ANN semantic dedup check
/// 5. Store in LMDB + SQLite
/// 6. Index in HNSW + BM25
pub async fn store_memory(
    State(state): State<Arc<AppState>>,
    Json(req): Json<StoreRequest>,
) -> Recall2Result<Json<StoreResponse>> {
    let start = Instant::now();
    debug!(content_len = req.content.len(), "Store memory request");

    // Determine provenance
    let provenance = if let Some(ref prov_str) = req.provenance {
        SourceProvenance::from_str_lossy(prov_str)
    } else if let Some(ref hook) = req.hook_type {
        SourceProvenance::from_hook_type(hook)
    } else {
        SourceProvenance::default()
    };

    // L0: Exact dedup via SHA-256
    let content_hash = sha256_content_hash(&req.content);
    if let Some(existing_uuid_str) = state.db.get_by_hash(&content_hash)
        .map_err(|e| Recall2Error::Storage(e.to_string()))? {
        info!(hash = %content_hash, "L0 exact duplicate detected");
        return Ok(Json(StoreResponse {
            uuid: existing_uuid_str.parse().unwrap_or_default(),
            status: "duplicate".to_string(),
            dedup_level: Some("L0_exact".to_string()),
            existing_uuid: existing_uuid_str.parse().ok(),
        }));
    }

    // Embed the content
    let embedding = state.embedder.embed_single(&req.content)
        .map_err(|e| Recall2Error::Embedding(e.to_string()))?;

    // L1: SimHash near-dup check
    let simhash = SimHash::new(state.embedder.dimension());
    if let Some(existing_uuid) = simhash.find_near_duplicate(
        &embedding,
        &state.db,
        state.config.dedup.simhash_hamming_threshold,
    ) {
        info!(existing = %existing_uuid, "L1 SimHash near-duplicate detected");
        return Ok(Json(StoreResponse {
            uuid: existing_uuid,
            status: "duplicate".to_string(),
            dedup_level: Some("L1_simhash".to_string()),
            existing_uuid: Some(existing_uuid),
        }));
    }

    // L2: HNSW ANN semantic dedup check
    {
        let index = state.index.read().await;
        let near_dupes = index.find_near_duplicates(
            &embedding,
            state.config.dedup.hnsw_cosine_threshold,
        );
        if let Some((existing_uuid, similarity)) = near_dupes.first() {
            info!(
                existing = %existing_uuid,
                similarity = similarity,
                "L2 HNSW semantic duplicate detected"
            );
            return Ok(Json(StoreResponse {
                uuid: *existing_uuid,
                status: "duplicate".to_string(),
                dedup_level: Some("L2_semantic".to_string()),
                existing_uuid: Some(*existing_uuid),
            }));
        }
    }

    // All dedup checks passed — store the memory
    let uuid = Uuid::new_v4();
    let record = MemoryRecord {
        uuid,
        content: req.content.clone(),
        content_hash: content_hash.clone(),
        tags: req.tags.clone(),
        importance: req.importance,
        provenance,
        metadata: req.metadata.clone(),
        created_at: Utc::now(),
        access_count: 0,
        last_accessed: None,
    };

    // Store in LMDB
    state.db.store_memory(&record)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;
    state.db.put_content_hash(&content_hash, &uuid)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;
    state.db.store_embedding(&uuid, &embedding)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;

    // Register SimHash bands
    simhash.register_bands(&embedding, &uuid, &state.db)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;

    // Store in SQLite
    state.sql.insert_memory(&record)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;

    // Index in HNSW
    {
        let mut index = state.index.write().await;
        index.add_point(uuid, embedding);
    }

    // Index in BM25
    {
        let mut fts = state.fts.write().await;
        fts.index_memory(&uuid, &req.content, &req.tags)
            .map_err(|e| Recall2Error::Index(e.to_string()))?;
    }

    let elapsed = start.elapsed();
    info!(uuid = %uuid, elapsed_ms = elapsed.as_millis(), "Memory stored");

    Ok(Json(StoreResponse {
        uuid,
        status: "stored".to_string(),
        dedup_level: None,
        existing_uuid: None,
    }))
}

/// Search for memories.
///
/// Read path:
/// 1. Embed query via fastembed-rs
/// 2. Parallel: HNSW top-K + BM25 top-K
/// 3. RRF fusion
/// 4. Behavioral scoring
/// 5. Emit CO_RETRIEVED events
/// 6. Return scored results
pub async fn search_memories(
    State(state): State<Arc<AppState>>,
    Json(req): Json<SearchRequest>,
) -> Recall2Result<Json<SearchResponse>> {
    let start = Instant::now();
    debug!(query = %req.query, limit = req.limit, "Search request");

    // Embed the query
    let query_embedding = state.embedder.embed_single(&req.query)
        .map_err(|e| Recall2Error::Embedding(e.to_string()))?;

    // HNSW search
    let hnsw_results = {
        let index = state.index.read().await;
        index.search(&query_embedding, req.limit * 2) // over-fetch for fusion
    };

    // BM25 search
    let bm25_results = {
        let fts = state.fts.read().await;
        fts.search(&req.query, req.limit * 2)
            .map_err(|e| Recall2Error::Index(e.to_string()))?
    };

    // Hybrid fusion
    let fused = hybrid_search(&bm25_results, &hnsw_results, req.limit * 2);

    // Score and build results
    let mut memories: Vec<MemoryResult> = Vec::new();
    let mut result_uuids: Vec<Uuid> = Vec::new();

    for scored in &fused {
        let record = match state.db.get_memory(&scored.uuid)
            .map_err(|e| Recall2Error::Storage(e.to_string()))? {
            Some(r) => r,
            None => continue,
        };

        // Compute behavioral score
        let co_gravity = state.graph.get_gravity(&scored.uuid);
        let final_score = compute_score(
            scored.cosine_similarity,
            co_gravity,
            record.importance,
            &record.provenance,
            &state.config.scoring,
        );

        // Record access
        let _ = state.sql.record_access(&scored.uuid);

        memories.push(MemoryResult {
            uuid: record.uuid,
            content: record.content,
            score: final_score,
            tags: record.tags,
            importance: record.importance,
            provenance: record.provenance.as_str().to_string(),
            created_at: record.created_at,
            metadata: record.metadata,
        });

        result_uuids.push(scored.uuid);
    }

    // Sort by final score and truncate
    memories.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    memories.truncate(req.limit);

    // Emit CO_RETRIEVED events for all pairs in the result set
    let final_uuids: Vec<Uuid> = memories.iter().map(|m| m.uuid).collect();
    for i in 0..final_uuids.len() {
        for j in (i + 1)..final_uuids.len() {
            let event = CoRetrievedEvent {
                a: final_uuids[i],
                b: final_uuids[j],
                session_id: req.session_id.clone(),
            };
            if let Err(e) = state.co_retrieved_tx.try_send(event) {
                warn!(error = %e, "CO_RETRIEVED channel full, dropping event");
            }
        }
    }

    let total_memories = {
        let index = state.index.read().await;
        index.len()
    };

    let elapsed = start.elapsed();
    info!(
        results = memories.len(),
        query_time_ms = elapsed.as_millis(),
        "Search complete"
    );

    Ok(Json(SearchResponse {
        memories,
        query_time_ms: elapsed.as_millis() as u64,
        total_memories,
    }))
}

/// Get a single memory by UUID.
pub async fn get_memory(
    State(state): State<Arc<AppState>>,
    Path(uuid_str): Path<String>,
) -> Recall2Result<Json<MemoryResult>> {
    let uuid: Uuid = uuid_str
        .parse()
        .map_err(|_| Recall2Error::NotFound(format!("Invalid UUID: {uuid_str}")))?;

    let record = state
        .db
        .get_memory(&uuid)
        .map_err(|e| Recall2Error::Storage(e.to_string()))?
        .ok_or_else(|| Recall2Error::NotFound(format!("Memory not found: {uuid}")))?;

    Ok(Json(MemoryResult {
        uuid: record.uuid,
        content: record.content,
        score: 0.0, // not from search
        tags: record.tags,
        importance: record.importance,
        provenance: record.provenance.as_str().to_string(),
        created_at: record.created_at,
        metadata: record.metadata,
    }))
}

/// Health endpoint.
pub async fn get_health(
    State(state): State<Arc<AppState>>,
) -> Recall2Result<Json<HealthResponse>> {
    let memory_count = state
        .sql
        .memory_count()
        .map_err(|e| Recall2Error::Storage(e.to_string()))?;

    let edge_count = state.graph.edge_count() as i64;

    // TODO: Phase 5 — implement real health signal computation
    let signals = HealthSignals {
        s1_topk_consistency: 0.0,
        s2_edge_density: 0.0,
        s3_bootstrap_bias: 0.0,
        s4_write_latency_p95_ms: 0.0,
    };

    Ok(Json(HealthResponse {
        status: "ok".to_string(),
        memory_count,
        edge_count,
        signals,
    }))
}

/// Admin: trigger migration from Recall 1.0.
pub async fn admin_migrate(
    State(_state): State<Arc<AppState>>,
    Json(req): Json<MigrateRequest>,
) -> Recall2Result<Json<MigrateResponse>> {
    info!(source = %req.source_url, "Migration requested");

    // TODO: Phase 1 — implement migration
    // See migration::importer for the actual implementation
    warn!("Migration not yet implemented");

    Ok(Json(MigrateResponse {
        status: "not_implemented".to_string(),
        memories_migrated: 0,
        edges_seeded: 0,
    }))
}

/// Admin: rebuild HNSW index from LMDB embeddings.
pub async fn admin_rebuild_index(
    State(state): State<Arc<AppState>>,
) -> Recall2Result<Json<serde_json::Value>> {
    info!("HNSW index rebuild requested");

    let new_index = crate::index::HnswIndex::load_or_build(
        &state.config.storage.data_dir,
        &state.config.hnsw,
        &state.db,
    )
    .map_err(|e| Recall2Error::Index(e.to_string()))?;

    let point_count = new_index.len();
    *state.index.write().await = new_index;

    info!(points = point_count, "HNSW index rebuilt");

    Ok(Json(serde_json::json!({
        "status": "rebuilt",
        "points": point_count,
    })))
}
