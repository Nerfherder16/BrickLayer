//! Migration from Recall 1.0 — corpus import and CO_RETRIEVED bootstrap.
//!
//! Reads from Recall 1.0 PostgreSQL, generates embeddings via fastembed-rs,
//! stores in LMDB + SQLite, and seeds CO_RETRIEVED edges via K-means bootstrap.

pub mod importer;
