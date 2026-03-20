//! Storage layer — LMDB (primary KV) and SQLite (structured queries).
//!
//! LMDB handles hot-path reads/writes: memories, embeddings, content hashes, co-edges.
//! SQLite handles structured queries, migration tracking, and analytics.

mod lmdb;
mod sqlite;

pub use self::lmdb::LmdbStore;
pub use self::sqlite::SqliteStore;
