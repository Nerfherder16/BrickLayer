//! K-means bootstrap — seeds initial CO_RETRIEVED edges from corpus analysis.
//!
//! Q200 Phase 3: Cold-start mitigation. Without bootstrap edges, the behavioral
//! graph has no signal to amplify. K-means clustering (K=200) identifies memory
//! neighborhoods, then seeds synthetic CO_RETRIEVED edges based on importance tiers:
//!
//! - importance >= 0.8 → 15 synthetic edges
//! - importance >= 0.6 → 7 synthetic edges
//! - importance >= 0.4 → 3 synthetic edges

use std::sync::Arc;

use anyhow::Result;
use tracing::{info, warn};
use crate::graph::co_retrieved::CoRetrievedGraph;
use crate::storage::{LmdbStore, SqliteStore};

/// Run K-means bootstrap to seed CO_RETRIEVED edges.
///
/// This is a one-shot job run after migration from Recall 1.0.
/// All synthetic events are tagged with `source=BootstrapMigration`.
pub async fn bootstrap_kmeans(
    db: Arc<LmdbStore>,
    sql: Arc<SqliteStore>,
    graph: Arc<CoRetrievedGraph>,
    k: usize,
) -> Result<()> {
    info!(k = k, "Starting K-means bootstrap");

    // Load all embeddings from LMDB
    let all_embeddings = db.all_embeddings()?;
    if all_embeddings.is_empty() {
        warn!("No embeddings found — skipping bootstrap");
        return Ok(());
    }

    let n = all_embeddings.len();
    info!(memories = n, "Loaded embeddings for bootstrap");

    // Simple K-means clustering
    let clusters = simple_kmeans(
        &all_embeddings.iter().map(|(_, e)| e.clone()).collect::<Vec<_>>(),
        k.min(n),
        10, // max iterations
    );

    // Group memories by cluster
    let mut cluster_members: Vec<Vec<usize>> = vec![Vec::new(); k.min(n)];
    for (idx, cluster_id) in clusters.iter().enumerate() {
        cluster_members[*cluster_id].push(idx);
    }

    let mut total_edges = 0u64;

    // For each cluster, seed edges between members based on importance
    for members in &cluster_members {
        if members.len() < 2 {
            continue;
        }

        for &idx in members {
            let (uuid, _) = &all_embeddings[idx];
            let record = db.get_memory(uuid)?;
            let importance = record.as_ref().map(|r| r.importance).unwrap_or(0.5);

            let max_edges = if importance >= 0.8 {
                15
            } else if importance >= 0.6 {
                7
            } else if importance >= 0.4 {
                3
            } else {
                0
            };

            // Connect to other members in the same cluster
            for &other_idx in members.iter().filter(|&&o| o != idx).take(max_edges) {
                let (other_uuid, _) = &all_embeddings[other_idx];

                // Seed with initial weight of 0.3
                graph.load_edge(*uuid, *other_uuid, 0.3);
                let _ = db.update_co_edge(uuid, other_uuid, 0.3);
                let _ = sql.record_co_event(
                    uuid,
                    other_uuid,
                    None,
                    "BootstrapMigration",
                );

                total_edges += 1;
            }
        }
    }

    info!(
        total_edges = total_edges,
        clusters = cluster_members.iter().filter(|m| !m.is_empty()).count(),
        "K-means bootstrap complete"
    );

    Ok(())
}

/// Simple K-means clustering. Returns cluster assignment for each point.
fn simple_kmeans(points: &[Vec<f32>], k: usize, max_iter: usize) -> Vec<usize> {
    let n = points.len();
    let dim = points[0].len();

    if n <= k {
        return (0..n).collect();
    }

    // Initialize centroids with first k points (simple, not k-means++)
    let mut centroids: Vec<Vec<f32>> = points[..k].to_vec();
    let mut assignments = vec![0usize; n];

    for _iter in 0..max_iter {
        // Assign points to nearest centroid
        let mut changed = false;
        for (i, point) in points.iter().enumerate() {
            let mut best_cluster = 0;
            let mut best_dist = f32::MAX;
            for (c, centroid) in centroids.iter().enumerate() {
                let dist = euclidean_distance_sq(point, centroid);
                if dist < best_dist {
                    best_dist = dist;
                    best_cluster = c;
                }
            }
            if assignments[i] != best_cluster {
                assignments[i] = best_cluster;
                changed = true;
            }
        }

        if !changed {
            break;
        }

        // Update centroids
        let mut sums = vec![vec![0.0f32; dim]; k];
        let mut counts = vec![0usize; k];
        for (i, point) in points.iter().enumerate() {
            let c = assignments[i];
            counts[c] += 1;
            for (j, val) in point.iter().enumerate() {
                sums[c][j] += val;
            }
        }
        for c in 0..k {
            if counts[c] > 0 {
                for j in 0..dim {
                    centroids[c][j] = sums[c][j] / counts[c] as f32;
                }
            }
        }
    }

    assignments
}

/// Squared Euclidean distance between two vectors.
fn euclidean_distance_sq(a: &[f32], b: &[f32]) -> f32 {
    a.iter()
        .zip(b.iter())
        .map(|(ai, bi)| (ai - bi) * (ai - bi))
        .sum()
}
