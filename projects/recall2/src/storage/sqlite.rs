//! SQLite storage — structured queries, migration tracking, analytics.
//!
//! Complements LMDB: LMDB handles hot-path KV operations,
//! SQLite handles complex queries, reporting, and migration state.

use std::path::Path;

use anyhow::Result;
use chrono::Utc;
use rusqlite::Connection;
use std::sync::Mutex;
use uuid::Uuid;

use crate::api::types::MemoryRecord;

/// SQLite store with internal mutex for thread safety.
#[derive(Debug)]
pub struct SqliteStore {
    conn: Mutex<Connection>,
}

impl SqliteStore {
    /// Open SQLite database at `data_dir/recall2.db`.
    pub fn open(data_dir: &str) -> Result<Self> {
        let path = Path::new(data_dir).join("recall2.db");
        let conn = Connection::open(path)?;

        // Enable WAL mode for better concurrent read performance
        conn.execute_batch("PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;")?;

        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Run pending SQL migrations from the migrations/ directory.
    pub fn run_migrations(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        // Check if schema_migrations table exists
        let has_migrations: bool = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'",
                [],
                |row| row.get::<_, i64>(0),
            )
            .map(|c| c > 0)?;

        let current_version: i64 = if has_migrations {
            conn.query_row(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations",
                [],
                |row| row.get(0),
            )?
        } else {
            0
        };

        // Apply 001_initial if not yet applied
        if current_version < 1 {
            let sql = include_str!("../../migrations/001_initial.sql");
            conn.execute_batch(sql)?;
            tracing::info!(version = 1, "Applied migration 001_initial");
        }

        Ok(())
    }

    /// Insert a memory record into SQLite.
    pub fn insert_memory(&self, record: &MemoryRecord) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO memories (uuid, content, content_hash, tags, importance, provenance, metadata, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            rusqlite::params![
                record.uuid.to_string(),
                record.content,
                record.content_hash,
                serde_json::to_string(&record.tags)?,
                record.importance,
                record.provenance.as_str(),
                serde_json::to_string(&record.metadata)?,
                record.created_at.to_rfc3339(),
            ],
        )?;
        Ok(())
    }

    /// Record a memory access (increment count, update last_accessed).
    pub fn record_access(&self, uuid: &Uuid) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        let now = Utc::now().to_rfc3339();
        conn.execute(
            "UPDATE memories SET access_count = access_count + 1, last_accessed = ?1 WHERE uuid = ?2",
            rusqlite::params![now, uuid.to_string()],
        )?;
        Ok(())
    }

    /// Record a CO_RETRIEVED event.
    pub fn record_co_event(
        &self,
        a_id: &Uuid,
        b_id: &Uuid,
        session_id: Option<&str>,
        source: &str,
    ) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO co_events (a_id, b_id, session_id, source) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![
                a_id.to_string(),
                b_id.to_string(),
                session_id,
                source,
            ],
        )?;
        Ok(())
    }

    /// Query working set — most recently accessed memories.
    pub fn query_working_set(&self, limit: usize) -> Result<Vec<String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT uuid FROM memories WHERE last_accessed IS NOT NULL
             ORDER BY last_accessed DESC LIMIT ?1",
        )?;
        let uuids: Vec<String> = stmt
            .query_map(rusqlite::params![limit as i64], |row| row.get(0))?
            .collect::<std::result::Result<Vec<_>, _>>()?;
        Ok(uuids)
    }

    /// Get total memory count.
    pub fn memory_count(&self) -> Result<i64> {
        let conn = self.conn.lock().unwrap();
        conn.query_row("SELECT COUNT(*) FROM memories", [], |row| row.get(0))
            .map_err(Into::into)
    }

    /// Get total co-event count.
    pub fn co_event_count(&self) -> Result<i64> {
        let conn = self.conn.lock().unwrap();
        conn.query_row("SELECT COUNT(*) FROM co_events", [], |row| row.get(0))
            .map_err(Into::into)
    }

    /// Record a health snapshot.
    pub fn record_health_snapshot(
        &self,
        s1: f64,
        s2: f64,
        s3: f64,
        s4: f64,
        memory_count: i64,
        edge_count: i64,
    ) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO health_snapshots (s1_topk_consistency, s2_edge_density, s3_bootstrap_bias, s4_write_latency_p95_ms, memory_count, edge_count)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            rusqlite::params![s1, s2, s3, s4, memory_count, edge_count],
        )?;
        Ok(())
    }
}
