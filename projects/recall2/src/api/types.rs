//! Request/response types for the HTTP API.
//!
//! Compatible with Recall 1.0 API shapes so existing hooks work without modification.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

use crate::provenance::SourceProvenance;

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

/// Store a new memory.
///
/// Compatible with Recall 1.0 `POST /store` body.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoreRequest {
    /// The memory content text.
    pub content: String,

    /// Tags for categorization and filtering.
    #[serde(default)]
    pub tags: Vec<String>,

    /// Importance score (0.0 to 1.0). Default: 0.5.
    #[serde(default = "default_importance")]
    pub importance: f32,

    /// Arbitrary metadata (JSON object).
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,

    /// Hook type — used to determine provenance tier automatically.
    #[serde(default)]
    pub hook_type: Option<String>,

    /// Session ID — used for CO_RETRIEVED deduplication.
    #[serde(default)]
    pub session_id: Option<String>,

    /// Explicit provenance override (optional).
    #[serde(default)]
    pub provenance: Option<String>,
}

fn default_importance() -> f32 {
    0.5
}

/// Search for memories.
///
/// Compatible with Recall 1.0 `POST /search` body.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchRequest {
    /// Natural language query text.
    pub query: String,

    /// Maximum number of results to return. Default: 10.
    #[serde(default = "default_limit")]
    pub limit: usize,

    /// Optional tag filters.
    #[serde(default)]
    pub filters: SearchFilters,

    /// Session ID — used for CO_RETRIEVED event emission.
    #[serde(default)]
    pub session_id: Option<String>,
}

fn default_limit() -> usize {
    10
}

/// Search filters.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SearchFilters {
    /// Filter by tags (AND logic — memory must have all specified tags).
    #[serde(default)]
    pub tags: Vec<String>,

    /// Filter by minimum importance.
    #[serde(default)]
    pub min_importance: Option<f32>,

    /// Filter by provenance tier.
    #[serde(default)]
    pub provenance: Option<String>,
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

/// Search response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResponse {
    /// Matching memories, sorted by score descending.
    pub memories: Vec<MemoryResult>,

    /// Query execution time in milliseconds.
    pub query_time_ms: u64,

    /// Total memories in the index (for context).
    pub total_memories: usize,
}

/// A single memory in search results.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryResult {
    pub uuid: Uuid,
    pub content: String,
    pub score: f32,
    pub tags: Vec<String>,
    pub importance: f32,
    pub provenance: String,
    pub created_at: DateTime<Utc>,
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Store response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoreResponse {
    pub uuid: Uuid,
    pub status: String,
    /// If duplicate, which level caught it.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dedup_level: Option<String>,
    /// If duplicate, the UUID of the existing memory.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub existing_uuid: Option<Uuid>,
}

/// Health response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub memory_count: i64,
    pub edge_count: i64,
    pub signals: HealthSignals,
}

/// Health signal values.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthSignals {
    pub s1_topk_consistency: f64,
    pub s2_edge_density: f64,
    pub s3_bootstrap_bias: f64,
    pub s4_write_latency_p95_ms: f64,
}

// ---------------------------------------------------------------------------
// Internal record type (stored in LMDB)
// ---------------------------------------------------------------------------

/// Full memory record — stored in LMDB as JSON.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryRecord {
    pub uuid: Uuid,
    pub content: String,
    pub content_hash: String,
    pub tags: Vec<String>,
    pub importance: f32,
    pub provenance: SourceProvenance,
    pub metadata: HashMap<String, serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub access_count: u64,
    pub last_accessed: Option<DateTime<Utc>>,
}

/// Migration request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MigrateRequest {
    /// PostgreSQL connection string for Recall 1.0 database.
    pub source_url: String,
}

/// Migration response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MigrateResponse {
    pub status: String,
    pub memories_migrated: u64,
    pub edges_seeded: u64,
}
