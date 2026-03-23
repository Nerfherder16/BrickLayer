//! CO_RETRIEVED graph — DashMap-backed concurrent in-memory edge store.
//!
//! Weight update formula: `w = w + lr * (1 - w)` — bounded increment that
//! asymptotically approaches 1.0 but never exceeds it.
//! Q200 Phase 3: validated learning_rate=0.1 as optimal.

use dashmap::DashMap;
use uuid::Uuid;

/// A CO_RETRIEVED event — two memories appeared in the same search result set.
#[derive(Debug, Clone)]
pub struct CoRetrievedEvent {
    /// First memory UUID.
    pub a: Uuid,
    /// Second memory UUID.
    pub b: Uuid,
    /// Session ID for deduplication (same pair in same session = 1 event).
    pub session_id: Option<String>,
}

/// In-memory CO_RETRIEVED graph backed by DashMap for lock-free concurrent access.
#[derive(Debug)]
pub struct CoRetrievedGraph {
    /// Edge weights: (min(a,b), max(a,b)) -> weight.
    edges: DashMap<(Uuid, Uuid), f32>,
}

impl CoRetrievedGraph {
    /// Create a new empty graph.
    pub fn new() -> Self {
        Self {
            edges: DashMap::new(),
        }
    }

    /// Update edge weight with bounded increment.
    ///
    /// Formula: `w = w + learning_rate * (1 - w)`
    /// This ensures weights approach 1.0 asymptotically but never exceed it.
    pub fn update_weight(&self, a: &Uuid, b: &Uuid, learning_rate: f32) {
        let key = canonical_pair(a, b);
        let mut entry = self.edges.entry(key).or_insert(0.0);
        let w = *entry;
        *entry = w + learning_rate * (1.0 - w);
    }

    /// Get the CO_RETRIEVED gravity for a memory — mean weight of its edges.
    ///
    /// Used in the scoring formula: `score = (cos*0.6 + co_grav*0.2 + imp*0.2) * prov`.
    pub fn get_gravity(&self, uuid: &Uuid) -> f32 {
        let neighbors = self.get_neighbors(uuid, usize::MAX);
        if neighbors.is_empty() {
            return 0.0;
        }
        let sum: f32 = neighbors.iter().map(|(_, w)| w).sum();
        sum / neighbors.len() as f32
    }

    /// Get the top-k neighbors of a memory by edge weight.
    pub fn get_neighbors(&self, uuid: &Uuid, k: usize) -> Vec<(Uuid, f32)> {
        let mut neighbors: Vec<(Uuid, f32)> = self
            .edges
            .iter()
            .filter_map(|entry| {
                let ((a, b), weight) = entry.pair();
                if a == uuid {
                    Some((*b, *weight))
                } else if b == uuid {
                    Some((*a, *weight))
                } else {
                    None
                }
            })
            .collect();

        neighbors.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        neighbors.truncate(k);
        neighbors
    }

    /// Get the weight of a specific edge.
    pub fn get_weight(&self, a: &Uuid, b: &Uuid) -> f32 {
        let key = canonical_pair(a, b);
        self.edges.get(&key).map(|v| *v).unwrap_or(0.0)
    }

    /// Load an edge from persistent storage into the in-memory graph.
    pub fn load_edge(&self, a: Uuid, b: Uuid, weight: f32) {
        let key = canonical_pair(&a, &b);
        self.edges.insert(key, weight);
    }

    /// Total number of edges in the graph.
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

impl Default for CoRetrievedGraph {
    fn default() -> Self {
        Self::new()
    }
}

/// Canonicalize a pair so (a,b) and (b,a) map to the same key.
fn canonical_pair(a: &Uuid, b: &Uuid) -> (Uuid, Uuid) {
    if a < b {
        (*a, *b)
    } else {
        (*b, *a)
    }
}
