//! Health signal computation.
//!
//! S1: Top-K Consistency — run the same query twice, measure overlap.
//!     High consistency = stable index. Low = something is wrong.
//!
//! S2: Edge Density — average CO_RETRIEVED edges per memory.
//!     Indicates how much behavioral signal the graph has accumulated.
//!
//! S3: Bootstrap Bias — ratio of synthetic (bootstrap) edge weight to total.
//!     Should decrease over time as organic events accumulate.
//!
//! S4: Write Latency p95 — 95th percentile of write-path latency.
//!     Monitored via a ring buffer of recent write durations.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

/// Ring buffer of recent write latencies (in microseconds) for p95 computation.
pub struct LatencyTracker {
    /// Fixed-size ring buffer.
    buffer: Mutex<Vec<u64>>,
    /// Buffer capacity.
    capacity: usize,
    /// Total writes tracked.
    total_writes: AtomicU64,
}

impl LatencyTracker {
    /// Create a new latency tracker with the given capacity.
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: Mutex::new(Vec::with_capacity(capacity)),
            capacity,
            total_writes: AtomicU64::new(0),
        }
    }

    /// Record a write latency in microseconds.
    pub fn record(&self, latency_us: u64) {
        let mut buf = self.buffer.lock().unwrap();
        if buf.len() >= self.capacity {
            buf.remove(0);
        }
        buf.push(latency_us);
        self.total_writes.fetch_add(1, Ordering::Relaxed);
    }

    /// Compute p95 latency in milliseconds.
    pub fn p95_ms(&self) -> f64 {
        let mut buf = self.buffer.lock().unwrap().clone();
        if buf.is_empty() {
            return 0.0;
        }
        buf.sort();
        let idx = ((buf.len() as f64) * 0.95) as usize;
        let idx = idx.min(buf.len() - 1);
        buf[idx] as f64 / 1000.0
    }

    /// Total writes tracked.
    pub fn total_writes(&self) -> u64 {
        self.total_writes.load(Ordering::Relaxed)
    }
}

impl std::fmt::Debug for LatencyTracker {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LatencyTracker")
            .field("capacity", &self.capacity)
            .field("total_writes", &self.total_writes.load(Ordering::Relaxed))
            .finish()
    }
}

/// Compute S1: Top-K consistency ratio.
///
/// Run the same query twice and measure the overlap in results.
/// Returns overlap / k (1.0 = perfectly stable, 0.0 = completely unstable).
///
/// TODO: Phase 5 — needs query + index access, implement in handler.
pub fn compute_topk_consistency(results_a: &[uuid::Uuid], results_b: &[uuid::Uuid]) -> f64 {
    if results_a.is_empty() || results_b.is_empty() {
        return 0.0;
    }

    let set_a: std::collections::HashSet<_> = results_a.iter().collect();
    let overlap = results_b.iter().filter(|u| set_a.contains(u)).count();
    overlap as f64 / results_a.len().max(results_b.len()) as f64
}

/// Compute S2: Edge density.
///
/// Average edges per memory = total_edges / total_memories.
pub fn compute_edge_density(total_edges: u64, total_memories: u64) -> f64 {
    if total_memories == 0 {
        return 0.0;
    }
    total_edges as f64 / total_memories as f64
}

/// Compute S3: Bootstrap bias.
///
/// Ratio of synthetic (bootstrap) edge weight to total edge weight.
/// Should trend toward 0 as organic CO_RETRIEVED events accumulate.
pub fn compute_bootstrap_bias(synthetic_weight: f64, total_weight: f64) -> f64 {
    if total_weight == 0.0 {
        return 0.0;
    }
    synthetic_weight / total_weight
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_latency_p95() {
        let tracker = LatencyTracker::new(100);
        // Record 100 values: 1000us to 100000us
        for i in 1..=100 {
            tracker.record(i * 1000);
        }
        let p95 = tracker.p95_ms();
        // p95 of 1..100 ms should be ~95ms
        assert!(p95 >= 90.0 && p95 <= 100.0, "p95 = {p95}");
    }

    #[test]
    fn test_topk_consistency_identical() {
        let a = vec![uuid::Uuid::new_v4()];
        let b = a.clone();
        assert_eq!(compute_topk_consistency(&a, &b), 1.0);
    }

    #[test]
    fn test_edge_density() {
        assert_eq!(compute_edge_density(1000, 100), 10.0);
        assert_eq!(compute_edge_density(0, 100), 0.0);
        assert_eq!(compute_edge_density(100, 0), 0.0);
    }

    #[test]
    fn test_bootstrap_bias() {
        assert_eq!(compute_bootstrap_bias(50.0, 100.0), 0.5);
        assert_eq!(compute_bootstrap_bias(0.0, 100.0), 0.0);
        assert_eq!(compute_bootstrap_bias(0.0, 0.0), 0.0);
    }
}
