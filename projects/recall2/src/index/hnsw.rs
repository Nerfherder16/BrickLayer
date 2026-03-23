//! HNSW vector index via instant-distance.
//!
//! Parameters (Q197: optimal for 22K corpus):
//! - ef_construction = 200
//! - M = 16
//! - ef_search = 50
//!
//! The index is rebuilt from LMDB embeddings on startup if no persisted
//! index file exists. Periodic rebuilds can be triggered via admin API.

use std::path::Path;

use anyhow::Result;
use uuid::Uuid;

use crate::config::HnswConfig;
use crate::storage::LmdbStore;

/// HNSW vector index for approximate nearest neighbor search.
///
/// Wraps instant-distance with UUID-based point tracking.
/// Q197: ef=200, M=16 validated optimal for recall corpus of ~22K memories.
#[derive(Debug)]
pub struct HnswIndex {
    /// Ordered list of UUIDs corresponding to index point positions.
    point_ids: Vec<Uuid>,
    /// Stored embeddings for cosine similarity computation.
    point_embeddings: Vec<Vec<f32>>,
    /// HNSW configuration parameters.
    _config: HnswConfig,
}

impl HnswIndex {
    /// Load persisted index or build from LMDB embeddings.
    pub fn load_or_build(
        data_dir: &str,
        config: &HnswConfig,
        db: &LmdbStore,
    ) -> Result<Self> {
        let index_path = Path::new(data_dir).join("hnsw.bin");

        if index_path.exists() {
            // TODO: Phase 1 — implement index deserialization
            tracing::info!("HNSW index file found, rebuilding from LMDB (deserialization not yet implemented)");
        }

        // Build from LMDB embeddings
        let all_embeddings = db.all_embeddings()?;
        let point_ids: Vec<Uuid> = all_embeddings.iter().map(|(uuid, _)| *uuid).collect();
        let point_embeddings: Vec<Vec<f32>> =
            all_embeddings.into_iter().map(|(_, emb)| emb).collect();

        tracing::info!(
            points = point_ids.len(),
            ef = config.ef_construction,
            m = config.m,
            "HNSW index built from LMDB"
        );

        Ok(Self {
            point_ids,
            point_embeddings,
            _config: config.clone(),
        })
    }

    /// Add a new point to the index.
    pub fn add_point(&mut self, uuid: Uuid, embedding: Vec<f32>) {
        self.point_ids.push(uuid);
        self.point_embeddings.push(embedding);
    }

    /// Search for the k nearest neighbors to the query vector.
    ///
    /// Returns (uuid, cosine_similarity) pairs sorted by descending similarity.
    /// Uses brute-force scan as a correct baseline — will be replaced with
    /// instant-distance HNSW graph in Phase 1 optimization.
    pub fn search(&self, query: &[f32], k: usize) -> Vec<(Uuid, f32)> {
        if self.point_ids.is_empty() {
            return Vec::new();
        }

        let mut scored: Vec<(usize, f32)> = self
            .point_embeddings
            .iter()
            .enumerate()
            .map(|(i, emb)| (i, cosine_similarity(query, emb)))
            .collect();

        scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(k);

        scored
            .into_iter()
            .map(|(i, score)| (self.point_ids[i], score))
            .collect()
    }

    /// Find memories with cosine similarity >= threshold.
    /// Used for L2 semantic dedup (threshold = 0.92).
    pub fn find_near_duplicates(&self, embedding: &[f32], threshold: f32) -> Vec<(Uuid, f32)> {
        self.search(embedding, 10)
            .into_iter()
            .filter(|(_, score)| *score >= threshold)
            .collect()
    }

    /// Persist index to disk.
    pub fn save(&self, data_dir: &str) -> Result<()> {
        let _index_path = Path::new(data_dir).join("hnsw.bin");
        // TODO: Phase 1 — implement index serialization
        tracing::debug!("HNSW index save: not yet implemented");
        Ok(())
    }

    /// Return the number of indexed points.
    pub fn len(&self) -> usize {
        self.point_ids.len()
    }

    /// Check if the index is empty.
    pub fn is_empty(&self) -> bool {
        self.point_ids.is_empty()
    }
}

/// Compute cosine similarity between two vectors.
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return 0.0;
    }

    let mut dot = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;

    for (ai, bi) in a.iter().zip(b.iter()) {
        dot += ai * bi;
        norm_a += ai * ai;
        norm_b += bi * bi;
    }

    let denom = norm_a.sqrt() * norm_b.sqrt();
    if denom < f32::EPSILON {
        0.0
    } else {
        dot / denom
    }
}
