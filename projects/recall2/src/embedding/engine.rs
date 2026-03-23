//! Embedding engine wrapping fastembed-rs.
//!
//! Model: BGE-small-en-v1.5 — 384-dimensional, INT8 quantized.
//! Selected per Q189 research: best latency/quality tradeoff for single-binary deployment.
//! First call triggers model download (~30MB) if not cached.

use anyhow::Result;
use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};

use crate::config::EmbeddingConfig;
use crate::error::Recall2Error;

/// Embedding engine — thread-safe, wraps fastembed TextEmbedding.
pub struct EmbeddingEngine {
    model: TextEmbedding,
    batch_size: usize,
}

impl std::fmt::Debug for EmbeddingEngine {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("EmbeddingEngine")
            .field("batch_size", &self.batch_size)
            .finish()
    }
}

impl EmbeddingEngine {
    /// Create a new embedding engine from configuration.
    ///
    /// The model is initialized lazily — the ONNX model file is downloaded
    /// on first use if not already cached.
    pub fn new(config: &EmbeddingConfig) -> Result<Self> {
        let model = TextEmbedding::try_new(
            InitOptions::new(EmbeddingModel::BGESmallENV15)
                .with_show_download_progress(true),
        )
        .map_err(|e| Recall2Error::Embedding(format!("Failed to init embedding model: {e}")))?;

        Ok(Self {
            model,
            batch_size: config.batch_size,
        })
    }

    /// Embed a single text string.
    ///
    /// Returns a 384-dimensional f32 vector.
    /// Q189: BGE-small-en-v1.5 produces 384-dim embeddings, not 1024.
    pub fn embed_single(&self, text: &str) -> Result<Vec<f32>> {
        let embeddings = self
            .model
            .embed(vec![text.to_string()], None)
            .map_err(|e| Recall2Error::Embedding(format!("Embed failed: {e}")))?;

        embeddings
            .into_iter()
            .next()
            .ok_or_else(|| Recall2Error::Embedding("No embedding returned".to_string()).into())
    }

    /// Embed a batch of text strings.
    ///
    /// Respects the configured batch_size. For large inputs, processes in chunks.
    pub fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut all_embeddings = Vec::with_capacity(texts.len());

        for chunk in texts.chunks(self.batch_size) {
            let batch = chunk.to_vec();
            let embeddings = self
                .model
                .embed(batch, None)
                .map_err(|e| Recall2Error::Embedding(format!("Batch embed failed: {e}")))?;
            all_embeddings.extend(embeddings);
        }

        Ok(all_embeddings)
    }

    /// Return the embedding dimensionality.
    /// BGE-small-en-v1.5 = 384 dimensions.
    pub fn dimension(&self) -> usize {
        384
    }
}
