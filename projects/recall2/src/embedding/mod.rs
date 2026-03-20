//! Embedding engine — fastembed-rs with BGE-small-en-v1.5.
//!
//! Produces 384-dimensional embeddings with INT8 quantization.
//! No external Ollama dependency — model runs in-process.

mod engine;

pub use engine::EmbeddingEngine;
