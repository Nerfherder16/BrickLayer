//! CO_RETRIEVED behavioral graph — learns which memories are useful together.
//!
//! When memories A and B appear in the same search result set, a CO_RETRIEVED event
//! fires. Over time, frequently co-retrieved pairs develop strong edges, boosting
//! each other in future searches.
//!
//! Q200 Phase 3: mpsc batching, bounded weight updates, K-means bootstrap.

mod bootstrap;
mod co_retrieved;
mod flush_worker;
mod scoring;

pub use bootstrap::bootstrap_kmeans;
pub use co_retrieved::{CoRetrievedEvent, CoRetrievedGraph};
pub use flush_worker::FlushWorker;
pub use scoring::compute_score;
