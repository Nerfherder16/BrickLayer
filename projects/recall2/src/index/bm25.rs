//! BM25 full-text search index via tantivy.
//!
//! Provides keyword/identifier matching that dense embeddings miss.
//! Q231/Q247: BM25 retrieval for identifier-heavy queries (function names,
//! file paths, config keys) dramatically improves recall vs. dense-only.

use std::path::Path;

use anyhow::Result;
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::{Schema, Value, STORED, TEXT};
use tantivy::{doc, Index, IndexReader, IndexWriter, ReloadPolicy};
use uuid::Uuid;

use crate::error::Recall2Error;

/// BM25 full-text search index backed by tantivy.
pub struct BM25Index {
    index: Index,
    reader: IndexReader,
    writer: IndexWriter,
    schema: Schema,
}

impl std::fmt::Debug for BM25Index {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("BM25Index").finish()
    }
}

impl BM25Index {
    /// Open or create the BM25 index at `data_dir/tantivy/`.
    pub fn open_or_create(data_dir: &str) -> Result<Self> {
        let path = Path::new(data_dir).join("tantivy");
        std::fs::create_dir_all(&path)?;

        let mut schema_builder = Schema::builder();
        schema_builder.add_text_field("uuid", STORED);
        schema_builder.add_text_field("content", TEXT | STORED);
        schema_builder.add_text_field("tags", TEXT);
        let schema = schema_builder.build();

        let index = if path.join("meta.json").exists() {
            Index::open_in_dir(&path)?
        } else {
            Index::create_in_dir(&path, schema.clone())?
        };

        let reader = index
            .reader_builder()
            .reload_policy(ReloadPolicy::OnCommitWithDelay)
            .try_into()?;

        // 50MB heap for the writer
        let writer = index.writer(50_000_000)?;

        Ok(Self {
            index,
            reader,
            writer,
            schema,
        })
    }

    /// Index a memory for full-text search.
    pub fn index_memory(&mut self, uuid: &Uuid, content: &str, tags: &[String]) -> Result<()> {
        let uuid_field = self.schema.get_field("uuid").unwrap();
        let content_field = self.schema.get_field("content").unwrap();
        let tags_field = self.schema.get_field("tags").unwrap();

        let tags_str = tags.join(" ");

        self.writer.add_document(doc!(
            uuid_field => uuid.to_string(),
            content_field => content,
            tags_field => tags_str,
        ))?;

        self.writer.commit()?;

        Ok(())
    }

    /// Search for memories matching the query text.
    ///
    /// Returns (uuid, bm25_score) pairs sorted by descending score.
    pub fn search(&self, query_text: &str, k: usize) -> Result<Vec<(Uuid, f32)>> {
        let content_field = self.schema.get_field("content").unwrap();
        let tags_field = self.schema.get_field("tags").unwrap();
        let uuid_field = self.schema.get_field("uuid").unwrap();

        let query_parser = QueryParser::for_index(&self.index, vec![content_field, tags_field]);
        let query = query_parser
            .parse_query(query_text)
            .map_err(|e| Recall2Error::Index(format!("Query parse error: {e}")))?;

        let searcher = self.reader.searcher();
        let top_docs = searcher.search(&query, &TopDocs::with_limit(k))?;

        let mut results = Vec::with_capacity(top_docs.len());
        for (score, doc_addr) in top_docs {
            let doc: tantivy::TantivyDocument = searcher.doc(doc_addr)?;
            if let Some(uuid_val) = doc.get_first(uuid_field) {
                if let Some(uuid_str) = uuid_val.as_str() {
                    if let Ok(uuid) = uuid_str.parse::<uuid::Uuid>() {
                        results.push((uuid, score));
                    }
                }
            }
        }

        Ok(results)
    }
}
