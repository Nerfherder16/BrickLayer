//! Source trust provenance — 5-tier system for memory trustworthiness.
//!
//! Q200 Phase 4: Provenance multipliers directly affect retrieval scoring.
//! UserDirect memories from explicit user commands rank highest;
//! Derived/inferred content ranks lowest.

mod types;

pub use types::SourceProvenance;
