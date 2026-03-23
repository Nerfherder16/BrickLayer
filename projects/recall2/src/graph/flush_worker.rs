//! CO_RETRIEVED flush worker — batches events from mpsc channel and
//! persists to LMDB + SQLite on a configurable interval (default 15 min).
//!
//! Q200 Phase 3: mpsc batching prevents write amplification from
//! high-frequency CO_RETRIEVED events during search bursts.

use std::collections::HashSet;
use std::sync::Arc;
use std::time::Duration;

use anyhow::Result;
use tokio::sync::mpsc;
use tracing::{info, warn};

use crate::graph::co_retrieved::{CoRetrievedEvent, CoRetrievedGraph};
use crate::storage::{LmdbStore, SqliteStore};

/// Flush worker that batches CO_RETRIEVED events and persists them periodically.
pub struct FlushWorker {
    rx: mpsc::Receiver<CoRetrievedEvent>,
    graph: Arc<CoRetrievedGraph>,
    db: Arc<LmdbStore>,
    sql: Arc<SqliteStore>,
    flush_interval: Duration,
}

impl FlushWorker {
    /// Create a new flush worker.
    pub fn new(
        rx: mpsc::Receiver<CoRetrievedEvent>,
        graph: Arc<CoRetrievedGraph>,
        db: Arc<LmdbStore>,
        sql: Arc<SqliteStore>,
        flush_interval_secs: u64,
    ) -> Self {
        Self {
            rx,
            graph,
            db,
            sql,
            flush_interval: Duration::from_secs(flush_interval_secs),
        }
    }

    /// Run the flush worker loop.
    ///
    /// Collects events from the mpsc channel, deduplicates within-session,
    /// updates the in-memory graph immediately, and persists to storage
    /// on the configured interval.
    pub async fn run(mut self) -> Result<()> {
        let mut pending_events: Vec<CoRetrievedEvent> = Vec::new();
        let mut flush_timer = tokio::time::interval(self.flush_interval);
        flush_timer.tick().await; // skip first immediate tick

        loop {
            tokio::select! {
                // Receive new events
                event = self.rx.recv() => {
                    match event {
                        Some(evt) => {
                            // Update in-memory graph immediately (non-blocking)
                            self.graph.update_weight(&evt.a, &evt.b, 0.1);
                            pending_events.push(evt);
                        }
                        None => {
                            // Channel closed — flush remaining and exit
                            if !pending_events.is_empty() {
                                self.flush(&mut pending_events);
                            }
                            info!("CO_RETRIEVED flush worker: channel closed, exiting");
                            return Ok(());
                        }
                    }
                }
                // Periodic flush
                _ = flush_timer.tick() => {
                    if !pending_events.is_empty() {
                        self.flush(&mut pending_events);
                    }
                }
            }
        }
    }

    /// Flush pending events to LMDB and SQLite.
    fn flush(&self, events: &mut Vec<CoRetrievedEvent>) {
        let total = events.len();

        // Session dedup: same (a,b) pair in same session = 1 event
        let mut seen: HashSet<(String, String, String)> = HashSet::new();
        let deduped: Vec<&CoRetrievedEvent> = events
            .iter()
            .filter(|e| {
                let session = e.session_id.clone().unwrap_or_default();
                let key = if e.a < e.b {
                    (e.a.to_string(), e.b.to_string(), session)
                } else {
                    (e.b.to_string(), e.a.to_string(), session)
                };
                seen.insert(key)
            })
            .collect();

        let mut edges_created = 0u64;
        let mut edges_updated = 0u64;

        for event in &deduped {
            // Persist to LMDB
            let current = self.db.get_co_edge(&event.a, &event.b).unwrap_or(0.0);
            let new_weight = current + 0.1 * (1.0 - current);

            if let Err(e) = self.db.update_co_edge(&event.a, &event.b, new_weight) {
                warn!(error = %e, "Failed to persist co-edge to LMDB");
                continue;
            }

            if current == 0.0 {
                edges_created += 1;
            } else {
                edges_updated += 1;
            }

            // Persist to SQLite
            if let Err(e) = self.sql.record_co_event(
                &event.a,
                &event.b,
                event.session_id.as_deref(),
                "organic",
            ) {
                warn!(error = %e, "Failed to record co-event in SQLite");
            }
        }

        info!(
            total_events = total,
            deduped_events = deduped.len(),
            edges_created = edges_created,
            edges_updated = edges_updated,
            "CO_RETRIEVED flush complete"
        );

        events.clear();
    }
}

// Debug impl for FlushWorker (mpsc::Receiver doesn't impl Debug)
impl std::fmt::Debug for FlushWorker {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("FlushWorker")
            .field("flush_interval", &self.flush_interval)
            .finish()
    }
}
