//! Hybrid search — BM25 + dense retrieval with Reciprocal Rank Fusion.
//!
//! Q231/Q247: RRF fusion of BM25 and HNSW results yields +18.5% MRR improvement
//! for identifier-heavy queries (function names, file paths, config keys).
//!
//! RRF formula: `rrf_score = 1/(rank_bm25 + k) + 1/(rank_hnsw + k)` where k=60.

use std::collections::HashMap;

use uuid::Uuid;

/// A search result with RRF-fused score.
#[derive(Debug, Clone)]
pub struct ScoredResult {
    pub uuid: Uuid,
    pub rrf_score: f32,
    pub cosine_similarity: f32,
    pub bm25_score: f32,
}

/// RRF constant — standard value from the literature.
const RRF_K: f32 = 60.0;

/// Fuse BM25 and HNSW results using Reciprocal Rank Fusion.
///
/// Both input lists should be pre-sorted by their respective scores (descending).
/// Returns fused results sorted by RRF score (descending), limited to `k` results.
pub fn hybrid_search(
    bm25_results: &[(Uuid, f32)],
    hnsw_results: &[(Uuid, f32)],
    k: usize,
) -> Vec<ScoredResult> {
    let mut scores: HashMap<Uuid, ScoredResult> = HashMap::new();

    // Process BM25 results — rank is 1-indexed
    for (rank, (uuid, bm25_score)) in bm25_results.iter().enumerate() {
        let rrf_contrib = 1.0 / (rank as f32 + 1.0 + RRF_K);
        let entry = scores.entry(*uuid).or_insert(ScoredResult {
            uuid: *uuid,
            rrf_score: 0.0,
            cosine_similarity: 0.0,
            bm25_score: 0.0,
        });
        entry.rrf_score += rrf_contrib;
        entry.bm25_score = *bm25_score;
    }

    // Process HNSW results — rank is 1-indexed
    for (rank, (uuid, cosine_sim)) in hnsw_results.iter().enumerate() {
        let rrf_contrib = 1.0 / (rank as f32 + 1.0 + RRF_K);
        let entry = scores.entry(*uuid).or_insert(ScoredResult {
            uuid: *uuid,
            rrf_score: 0.0,
            cosine_similarity: 0.0,
            bm25_score: 0.0,
        });
        entry.rrf_score += rrf_contrib;
        entry.cosine_similarity = *cosine_sim;
    }

    let mut fused: Vec<ScoredResult> = scores.into_values().collect();
    fused.sort_by(|a, b| b.rrf_score.partial_cmp(&a.rrf_score).unwrap_or(std::cmp::Ordering::Equal));
    fused.truncate(k);
    fused
}
