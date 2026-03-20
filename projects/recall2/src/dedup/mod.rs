//! Deduplication pipeline — three levels of duplicate detection.
//!
//! L0: SHA-256 exact content hash (O(1) LMDB lookup)
//! L1: SimHash near-duplicate (64-bit, 8 bands x 8 bits, H<=6)
//! L2: HNSW ANN semantic dedup (cosine >= 0.92)
//!
//! Q200 Phase 2: Validated thresholds and band configuration.

mod exact;
mod simhash;

pub use exact::sha256_content_hash;
pub use simhash::SimHash;
