//! HTTP API layer — axum router with Recall 1.0-compatible endpoints.
//!
//! Existing hooks (recall-retrieve.js, observe-edit.js, recall-session-summary.js)
//! work without modification against these endpoints.

pub mod compat;
pub mod handlers;
pub mod types;

use std::sync::Arc;

use axum::routing::{get, post};
use axum::Router;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

use crate::AppState;

/// Build the axum router with all API routes.
pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        // Core endpoints (Recall 1.0 compatible)
        .route("/store", post(handlers::store_memory))
        .route("/search", post(handlers::search_memories))
        .route("/memory/{uuid}", get(handlers::get_memory))
        // Health and admin
        .route("/health", get(handlers::get_health))
        .route("/admin/migrate", post(handlers::admin_migrate))
        .route("/admin/rebuild-index", post(handlers::admin_rebuild_index))
        // Recall 1.0 compatibility aliases
        .route("/recall/store", post(handlers::store_memory))
        .route("/recall/search", post(handlers::search_memories))
        // Middleware
        .layer(TraceLayer::new_for_http())
        .layer(CorsLayer::permissive())
        .with_state(state)
}
