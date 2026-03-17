//! LMDB storage via heed — primary key-value store.
//!
//! Named databases:
//! - `memories`     — UUID string → MemoryRecord (JSON serialized)
//! - `content_hash` — SHA-256 hex → UUID string (L0 dedup)
//! - `simhash_bands`— band_key → Vec<UUID> (JSON serialized, L1 dedup)
//! - `co_edges`     — "co:{uuid_a}:{uuid_b}" → f32 (weight, big-endian bytes)
//! - `embeddings`   — UUID string → Vec<f32> (bincode serialized)
//!
//! Design rationale (Q200): LMDB provides ACID transactions, zero-copy reads,
//! and embedded operation — no network hop to an external database.

use std::path::Path;

use anyhow::Result;
use heed::types::{Bytes, Str};
use heed::{Database, Env, EnvOpenOptions};
use uuid::Uuid;

use crate::api::types::MemoryRecord;
use crate::error::Recall2Error;

/// Maximum LMDB map size: 10 GB. Sufficient for ~100K memories with embeddings.
const MAX_MAP_SIZE: usize = 10 * 1024 * 1024 * 1024;

/// Number of named databases in the LMDB environment.
const MAX_DBS: u32 = 8;

/// LMDB-backed key-value store.
#[derive(Debug)]
pub struct LmdbStore {
    env: Env,
    /// UUID → MemoryRecord (JSON)
    memories: Database<Str, Bytes>,
    /// SHA-256 hex → UUID
    content_hash: Database<Str, Str>,
    /// Band key → Vec<UUID> (JSON)
    simhash_bands: Database<Str, Bytes>,
    /// "co:{a}:{b}" → f32 weight (4 bytes big-endian)
    co_edges: Database<Str, Bytes>,
    /// UUID → Vec<f32> embedding (raw bytes, 384 × 4 = 1536 bytes)
    embeddings: Database<Str, Bytes>,
}

impl LmdbStore {
    /// Open the LMDB environment at `data_dir/lmdb/`.
    pub fn open(data_dir: &str) -> Result<Self> {
        let path = Path::new(data_dir).join("lmdb");
        std::fs::create_dir_all(&path)?;

        let env = unsafe {
            EnvOpenOptions::new()
                .map_size(MAX_MAP_SIZE)
                .max_dbs(MAX_DBS)
                .open(&path)?
        };

        let mut wtxn = env.write_txn()?;
        let memories = env
            .create_database::<Str, Bytes>(&mut wtxn, Some("memories"))?;
        let content_hash = env
            .create_database::<Str, Str>(&mut wtxn, Some("content_hash"))?;
        let simhash_bands = env
            .create_database::<Str, Bytes>(&mut wtxn, Some("simhash_bands"))?;
        let co_edges = env
            .create_database::<Str, Bytes>(&mut wtxn, Some("co_edges"))?;
        let embeddings = env
            .create_database::<Str, Bytes>(&mut wtxn, Some("embeddings"))?;
        wtxn.commit()?;

        Ok(Self {
            env,
            memories,
            content_hash,
            simhash_bands,
            co_edges,
            embeddings,
        })
    }

    /// Store a memory record.
    pub fn store_memory(&self, record: &MemoryRecord) -> Result<()> {
        let json = serde_json::to_vec(record)?;
        let mut wtxn = self.env.write_txn()?;
        self.memories
            .put(&mut wtxn, &record.uuid.to_string(), &json)?;
        wtxn.commit()?;
        Ok(())
    }

    /// Retrieve a memory record by UUID.
    pub fn get_memory(&self, uuid: &Uuid) -> Result<Option<MemoryRecord>> {
        let rtxn = self.env.read_txn()?;
        match self.memories.get(&rtxn, &uuid.to_string())? {
            Some(bytes) => Ok(Some(serde_json::from_slice(bytes)?)),
            None => Ok(None),
        }
    }

    /// Check L0 dedup: content hash → UUID.
    pub fn get_by_hash(&self, hash: &str) -> Result<Option<String>> {
        let rtxn = self.env.read_txn()?;
        Ok(self.content_hash.get(&rtxn, hash)?.map(|s| s.to_string()))
    }

    /// Store content hash → UUID mapping.
    pub fn put_content_hash(&self, hash: &str, uuid: &Uuid) -> Result<()> {
        let mut wtxn = self.env.write_txn()?;
        self.content_hash
            .put(&mut wtxn, hash, &uuid.to_string())?;
        wtxn.commit()?;
        Ok(())
    }

    /// Get UUIDs in a SimHash band bucket.
    pub fn get_simhash_band(&self, band_key: &str) -> Result<Vec<Uuid>> {
        let rtxn = self.env.read_txn()?;
        match self.simhash_bands.get(&rtxn, band_key)? {
            Some(bytes) => {
                let uuids: Vec<Uuid> = serde_json::from_slice(bytes)?;
                Ok(uuids)
            }
            None => Ok(Vec::new()),
        }
    }

    /// Add a UUID to a SimHash band bucket.
    pub fn add_to_simhash_band(&self, band_key: &str, uuid: &Uuid) -> Result<()> {
        let mut existing = self.get_simhash_band(band_key)?;
        existing.push(*uuid);
        let json = serde_json::to_vec(&existing)?;
        let mut wtxn = self.env.write_txn()?;
        self.simhash_bands.put(&mut wtxn, band_key, &json)?;
        wtxn.commit()?;
        Ok(())
    }

    /// Get CO_RETRIEVED edge weight between two memories.
    pub fn get_co_edge(&self, a: &Uuid, b: &Uuid) -> Result<f32> {
        let key = co_edge_key(a, b);
        let rtxn = self.env.read_txn()?;
        match self.co_edges.get(&rtxn, &key)? {
            Some(bytes) => {
                let arr: [u8; 4] = bytes.try_into().map_err(|_| {
                    Recall2Error::Storage("Invalid co-edge weight bytes".to_string())
                })?;
                Ok(f32::from_be_bytes(arr))
            }
            None => Ok(0.0),
        }
    }

    /// Update CO_RETRIEVED edge weight.
    pub fn update_co_edge(&self, a: &Uuid, b: &Uuid, weight: f32) -> Result<()> {
        let key = co_edge_key(a, b);
        let bytes = weight.to_be_bytes();
        let mut wtxn = self.env.write_txn()?;
        self.co_edges.put(&mut wtxn, &key, &bytes)?;
        wtxn.commit()?;
        Ok(())
    }

    /// Store embedding vector for a memory.
    pub fn store_embedding(&self, uuid: &Uuid, embedding: &[f32]) -> Result<()> {
        let bytes: Vec<u8> = embedding
            .iter()
            .flat_map(|f| f.to_le_bytes())
            .collect();
        let mut wtxn = self.env.write_txn()?;
        self.embeddings
            .put(&mut wtxn, &uuid.to_string(), &bytes)?;
        wtxn.commit()?;
        Ok(())
    }

    /// Retrieve embedding vector for a memory.
    pub fn get_embedding(&self, uuid: &Uuid) -> Result<Option<Vec<f32>>> {
        let rtxn = self.env.read_txn()?;
        match self.embeddings.get(&rtxn, &uuid.to_string())? {
            Some(bytes) => {
                let floats: Vec<f32> = bytes
                    .chunks_exact(4)
                    .map(|chunk| {
                        let arr: [u8; 4] = chunk.try_into().unwrap();
                        f32::from_le_bytes(arr)
                    })
                    .collect();
                Ok(Some(floats))
            }
            None => Ok(None),
        }
    }

    /// Iterate all embeddings — used for HNSW index rebuild.
    pub fn all_embeddings(&self) -> Result<Vec<(Uuid, Vec<f32>)>> {
        let rtxn = self.env.read_txn()?;
        let mut results = Vec::new();
        let iter = self.embeddings.iter(&rtxn)?;
        for item in iter {
            let (key, bytes) = item?;
            let uuid: Uuid = key.parse().map_err(|e| {
                Recall2Error::Storage(format!("Invalid UUID in embeddings db: {e}"))
            })?;
            let floats: Vec<f32> = bytes
                .chunks_exact(4)
                .map(|chunk| {
                    let arr: [u8; 4] = chunk.try_into().unwrap();
                    f32::from_le_bytes(arr)
                })
                .collect();
            results.push((uuid, floats));
        }
        Ok(results)
    }

    /// Get all CO_RETRIEVED neighbors for a memory.
    pub fn get_co_neighbors(&self, uuid: &Uuid) -> Result<Vec<(Uuid, f32)>> {
        let prefix = format!("co:{uuid}:");
        let rtxn = self.env.read_txn()?;
        let mut neighbors = Vec::new();
        let iter = self.co_edges.iter(&rtxn)?;
        for item in iter {
            let (key, bytes) = item?;
            if key.starts_with(&prefix) {
                let other_str = &key[prefix.len()..];
                if let Ok(other_uuid) = other_str.parse::<Uuid>() {
                    let arr: [u8; 4] = bytes.try_into().unwrap_or([0; 4]);
                    let weight = f32::from_be_bytes(arr);
                    neighbors.push((other_uuid, weight));
                }
            }
        }
        Ok(neighbors)
    }
}

/// Build canonical co-edge key — always ordered so (a,b) == (b,a).
fn co_edge_key(a: &Uuid, b: &Uuid) -> String {
    if a < b {
        format!("co:{a}:{b}")
    } else {
        format!("co:{b}:{a}")
    }
}
