//! Recall 1.0 compatibility layer.
//!
//! Maps Recall 1.0 API shapes to Recall 2.0 internals so existing hooks
//! (recall-retrieve.js, observe-edit.js, recall-session-summary.js) work
//! without modification.
//!
//! ## Field mapping differences
//!
//! | Recall 1.0 field | Recall 2.0 field | Notes |
//! |------------------|------------------|-------|
//! | `text` | `content` | Aliased in StoreRequest deserialization |
//! | `domain` | `tags[0]` | Domain becomes first tag |
//! | `source` | `hook_type` | Maps to provenance via `from_hook_type` |
//! | `score` | `score` | Same field, different formula |
//! | `results` | `memories` | Renamed in SearchResponse |

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::api::types::{SearchRequest, StoreRequest};

/// Recall 1.0 store request shape.
///
/// Used for backward compatibility detection and mapping.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recall1StoreRequest {
    /// Content text (Recall 1.0 uses "text" not "content").
    #[serde(alias = "content")]
    pub text: Option<String>,

    /// Domain category (becomes first tag in Recall 2.0).
    pub domain: Option<String>,

    /// Source/hook type (maps to provenance).
    pub source: Option<String>,

    /// Tags.
    #[serde(default)]
    pub tags: Vec<String>,

    /// Importance.
    #[serde(default = "default_importance")]
    pub importance: f32,

    /// Metadata.
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,
}

fn default_importance() -> f32 {
    0.5
}

impl Recall1StoreRequest {
    /// Convert to Recall 2.0 StoreRequest.
    pub fn into_v2(self) -> Option<StoreRequest> {
        let content = self.text?;
        let mut tags = self.tags;
        if let Some(domain) = self.domain {
            if !tags.contains(&domain) {
                tags.insert(0, domain);
            }
        }

        Some(StoreRequest {
            content,
            tags,
            importance: self.importance,
            metadata: self.metadata,
            hook_type: self.source,
            session_id: None,
            provenance: None,
        })
    }
}

/// Recall 1.0 search request shape.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recall1SearchRequest {
    /// Query text.
    pub query: Option<String>,

    /// Alternative: "text" field.
    pub text: Option<String>,

    /// Result limit.
    #[serde(default = "default_limit")]
    pub limit: usize,

    /// Domain filter.
    pub domain: Option<String>,
}

fn default_limit() -> usize {
    10
}

impl Recall1SearchRequest {
    /// Convert to Recall 2.0 SearchRequest.
    pub fn into_v2(self) -> Option<SearchRequest> {
        let query = self.query.or(self.text)?;
        let mut filters = crate::api::types::SearchFilters::default();
        if let Some(domain) = self.domain {
            filters.tags.push(domain);
        }

        Some(SearchRequest {
            query,
            limit: self.limit,
            filters,
            session_id: None,
        })
    }
}
