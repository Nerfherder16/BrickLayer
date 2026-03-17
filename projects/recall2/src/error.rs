//! Error types for Recall 2.0.
//!
//! Uses `thiserror` for ergonomic error definitions.
//! All public functions return `Result<T, Recall2Error>` or `anyhow::Result<T>`.

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use serde_json::json;

/// Central error type for Recall 2.0 operations.
#[derive(Debug, thiserror::Error)]
pub enum Recall2Error {
    /// LMDB or SQLite storage operation failed.
    #[error("Storage error: {0}")]
    Storage(String),

    /// Embedding generation failed.
    #[error("Embedding error: {0}")]
    Embedding(String),

    /// Vector or text index operation failed.
    #[error("Index error: {0}")]
    Index(String),

    /// Requested memory not found.
    #[error("Not found: {0}")]
    NotFound(String),

    /// Memory rejected as duplicate (L0, L1, or L2).
    #[error("Duplicate detected at {level}: {detail}")]
    Duplicate { level: String, detail: String },

    /// Configuration error.
    #[error("Config error: {0}")]
    Config(String),

    /// Serialization/deserialization error.
    #[error("Serialization error: {0}")]
    Serialization(String),

    /// Migration error.
    #[error("Migration error: {0}")]
    Migration(String),

    /// Catch-all for unexpected errors.
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for Recall2Error {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            Recall2Error::NotFound(msg) => (StatusCode::NOT_FOUND, msg.clone()),
            Recall2Error::Duplicate { level, detail } => {
                (StatusCode::CONFLICT, format!("{level}: {detail}"))
            }
            Recall2Error::Config(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg.clone()),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };

        let body = json!({
            "error": message,
            "status": status.as_u16(),
        });

        (status, axum::Json(body)).into_response()
    }
}

/// Convenience type alias.
pub type Recall2Result<T> = Result<T, Recall2Error>;
