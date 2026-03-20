//! Health monitoring — 4 signals for operational visibility.
//!
//! Q200 Phase 5:
//! - S1: Top-K consistency ratio (HNSW stability)
//! - S2: CO_RETRIEVED edge density per user
//! - S3: Bootstrap bias (synthetic weight / total weight)
//! - S4: Write-path latency p95

pub mod signals;
