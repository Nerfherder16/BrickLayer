//! Configuration loading from TOML files and environment variables.
//!
//! Defaults in `config/default.toml`. Override with `RECALL2_CONFIG` env var.

use anyhow::Result;
use serde::{Deserialize, Serialize};

/// Top-level application configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub server: ServerConfig,
    pub storage: StorageConfig,
    pub embedding: EmbeddingConfig,
    pub hnsw: HnswConfig,
    pub dedup: DedupConfig,
    pub scoring: ScoringConfig,
    pub graph: GraphConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub port: u16,
    pub host: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub data_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingConfig {
    pub model: String,
    pub batch_size: usize,
}

/// HNSW index parameters — tuned per Q197 research.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnswConfig {
    pub ef_construction: usize,
    pub m: usize,
    pub ef_search: usize,
}

/// Deduplication thresholds — validated in Q200 Phase 2.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DedupConfig {
    pub simhash_hamming_threshold: u32,
    pub hnsw_cosine_threshold: f32,
}

/// Behavioral scoring weights — Q200 Phase 3 formula.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoringConfig {
    pub cosine_weight: f32,
    pub co_retrieved_weight: f32,
    pub importance_weight: f32,
}

/// CO_RETRIEVED graph configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphConfig {
    pub flush_interval_secs: u64,
    pub learning_rate: f32,
    pub kmeans_k: usize,
}

impl AppConfig {
    /// Load configuration from default.toml, overridden by RECALL2_CONFIG if set.
    pub fn load() -> Result<Self> {
        let builder = config::Config::builder()
            .add_source(config::File::with_name("config/default").required(false))
            .add_source(
                config::File::with_name(
                    &std::env::var("RECALL2_CONFIG").unwrap_or_default(),
                )
                .required(false),
            )
            .add_source(config::Environment::with_prefix("RECALL2").separator("__"));

        let settings = builder.build()?;
        let app_config: AppConfig = settings.try_deserialize()?;
        Ok(app_config)
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            server: ServerConfig {
                port: 8200,
                host: "0.0.0.0".to_string(),
            },
            storage: StorageConfig {
                data_dir: "/data/recall2".to_string(),
            },
            embedding: EmbeddingConfig {
                model: "BGESmallENV15".to_string(),
                batch_size: 32,
            },
            hnsw: HnswConfig {
                ef_construction: 200,
                m: 16,
                ef_search: 50,
            },
            dedup: DedupConfig {
                simhash_hamming_threshold: 6,
                hnsw_cosine_threshold: 0.92,
            },
            scoring: ScoringConfig {
                cosine_weight: 0.6,
                co_retrieved_weight: 0.2,
                importance_weight: 0.2,
            },
            graph: GraphConfig {
                flush_interval_secs: 900,
                learning_rate: 0.1,
                kmeans_k: 200,
            },
        }
    }
}
