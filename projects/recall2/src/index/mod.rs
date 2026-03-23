//! Search indices — HNSW vector index, BM25 full-text, and hybrid fusion.
//!
//! Q231/Q247: Hybrid retrieval (BM25 + dense + RRF) provides +18.5% MRR
//! improvement for identifier-heavy queries over dense-only search.

mod bm25;
mod hnsw;
mod hybrid;

pub use bm25::BM25Index;
pub use hnsw::HnswIndex;
pub use hybrid::{hybrid_search, ScoredResult};
