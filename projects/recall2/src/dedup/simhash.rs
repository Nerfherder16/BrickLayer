//! L1 near-duplicate detection via SimHash.
//!
//! 64 random hyperplanes project 384-dim embeddings to a 64-bit hash.
//! Banding (8 bands x 8 bits) enables efficient LMDB lookup.
//! Hamming distance <= 6 indicates near-duplicate.
//!
//! Q200 Phase 2: 64-bit SimHash with H<=6 threshold validated.

use uuid::Uuid;

use crate::storage::LmdbStore;

/// SimHash engine with 64 random hyperplanes for 384-dim embeddings.
#[derive(Debug)]
pub struct SimHash {
    /// 64 hyperplanes, each of dimension 384.
    hyperplanes: Vec<Vec<f32>>,
}

impl SimHash {
    /// Create a new SimHash with deterministic random hyperplanes.
    ///
    /// Uses a simple seeded LCG for reproducibility across restarts.
    pub fn new(dim: usize) -> Self {
        let mut hyperplanes = Vec::with_capacity(64);
        let mut seed: u64 = 42; // deterministic seed

        for _ in 0..64 {
            let mut plane = Vec::with_capacity(dim);
            for _ in 0..dim {
                // Simple LCG: next = (a * seed + c) mod m
                seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                // Map to [-1.0, 1.0]
                let val = ((seed >> 33) as f64 / (u32::MAX as f64)) * 2.0 - 1.0;
                plane.push(val as f32);
            }
            hyperplanes.push(plane);
        }

        Self { hyperplanes }
    }

    /// Compute the 64-bit SimHash of an embedding vector.
    ///
    /// Each bit is the sign of the dot product with the corresponding hyperplane.
    pub fn compute(&self, embedding: &[f32]) -> u64 {
        let mut hash: u64 = 0;

        for (i, plane) in self.hyperplanes.iter().enumerate() {
            let dot: f32 = embedding
                .iter()
                .zip(plane.iter())
                .map(|(a, b)| a * b)
                .sum();

            if dot >= 0.0 {
                hash |= 1u64 << i;
            }
        }

        hash
    }

    /// Compute Hamming distance between two SimHash values.
    ///
    /// Returns the number of differing bits (popcount of XOR).
    pub fn hamming_distance(a: u64, b: u64) -> u32 {
        (a ^ b).count_ones()
    }

    /// Generate the 8 band keys for LMDB lookup.
    ///
    /// 64 bits / 8 bands = 8 bits per band.
    /// Each band key is "simband:{band_index}:{band_value}".
    pub fn band_keys(hash: u64) -> [String; 8] {
        let mut keys = [
            String::new(),
            String::new(),
            String::new(),
            String::new(),
            String::new(),
            String::new(),
            String::new(),
            String::new(),
        ];

        for (i, key) in keys.iter_mut().enumerate() {
            let band_value = (hash >> (i * 8)) & 0xFF;
            *key = format!("simband:{i}:{band_value}");
        }

        keys
    }

    /// Check if a new embedding is a near-duplicate of any existing memory.
    ///
    /// Looks up band buckets in LMDB, retrieves candidate hashes,
    /// and checks Hamming distance <= threshold.
    ///
    /// Returns the UUID of the first near-duplicate found, if any.
    pub fn find_near_duplicate(
        &self,
        embedding: &[f32],
        db: &LmdbStore,
        threshold: u32,
    ) -> Option<Uuid> {
        let hash = self.compute(embedding);
        let keys = Self::band_keys(hash);

        // Collect candidates from all bands
        let mut candidates: Vec<Uuid> = Vec::new();
        for key in &keys {
            if let Ok(uuids) = db.get_simhash_band(key) {
                candidates.extend(uuids);
            }
        }

        // Deduplicate candidates
        candidates.sort();
        candidates.dedup();

        // Check Hamming distance for each candidate
        for candidate_uuid in &candidates {
            if let Ok(Some(candidate_emb)) = db.get_embedding(candidate_uuid) {
                let candidate_hash = self.compute(&candidate_emb);
                if Self::hamming_distance(hash, candidate_hash) <= threshold {
                    return Some(*candidate_uuid);
                }
            }
        }

        None
    }

    /// Register a new memory's SimHash bands in LMDB.
    pub fn register_bands(
        &self,
        embedding: &[f32],
        uuid: &Uuid,
        db: &LmdbStore,
    ) -> anyhow::Result<()> {
        let hash = self.compute(embedding);
        let keys = Self::band_keys(hash);

        for key in &keys {
            db.add_to_simhash_band(key, uuid)?;
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_identical_embeddings_same_hash() {
        let sh = SimHash::new(384);
        let emb = vec![0.1f32; 384];
        let h1 = sh.compute(&emb);
        let h2 = sh.compute(&emb);
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_hamming_distance_identical() {
        assert_eq!(SimHash::hamming_distance(0, 0), 0);
    }

    #[test]
    fn test_hamming_distance_one_bit() {
        assert_eq!(SimHash::hamming_distance(0b0001, 0b0000), 1);
    }

    #[test]
    fn test_hamming_distance_all_different() {
        assert_eq!(SimHash::hamming_distance(0, u64::MAX), 64);
    }

    #[test]
    fn test_band_keys_count() {
        let keys = SimHash::band_keys(0xDEADBEEFCAFEBABE);
        assert_eq!(keys.len(), 8);
        for (i, key) in keys.iter().enumerate() {
            assert!(key.starts_with(&format!("simband:{i}:")));
        }
    }

    #[test]
    fn test_similar_embeddings_low_hamming() {
        let sh = SimHash::new(384);
        let emb1 = vec![0.1f32; 384];
        let mut emb2 = emb1.clone();
        // Small perturbation
        emb2[0] = 0.11;
        emb2[1] = 0.09;

        let h1 = sh.compute(&emb1);
        let h2 = sh.compute(&emb2);

        let dist = SimHash::hamming_distance(h1, h2);
        // Similar embeddings should have low Hamming distance
        assert!(dist <= 10, "Expected low Hamming distance, got {dist}");
    }
}
