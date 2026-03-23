//! L0 exact deduplication — SHA-256 content hash.
//!
//! Normalization: lowercase, trim whitespace, collapse internal whitespace.
//! This catches exact duplicates before embedding is even computed.

use sha2::{Digest, Sha256};

/// Compute SHA-256 hash of normalized content.
///
/// Normalization steps:
/// 1. Trim leading/trailing whitespace
/// 2. Lowercase
/// 3. Collapse internal whitespace (multiple spaces/tabs/newlines → single space)
///
/// Returns lowercase hex string (64 chars).
pub fn sha256_content_hash(content: &str) -> String {
    let normalized = normalize_content(content);
    let mut hasher = Sha256::new();
    hasher.update(normalized.as_bytes());
    hex::encode(hasher.finalize())
}

/// Normalize content for consistent hashing.
fn normalize_content(content: &str) -> String {
    content
        .trim()
        .to_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_identical_content_same_hash() {
        let h1 = sha256_content_hash("Hello world");
        let h2 = sha256_content_hash("Hello world");
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_case_insensitive() {
        let h1 = sha256_content_hash("Hello World");
        let h2 = sha256_content_hash("hello world");
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_whitespace_normalization() {
        let h1 = sha256_content_hash("hello   world");
        let h2 = sha256_content_hash("  hello\t\nworld  ");
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_different_content_different_hash() {
        let h1 = sha256_content_hash("hello world");
        let h2 = sha256_content_hash("goodbye world");
        assert_ne!(h1, h2);
    }

    #[test]
    fn test_hash_length() {
        let h = sha256_content_hash("test");
        assert_eq!(h.len(), 64); // SHA-256 = 32 bytes = 64 hex chars
    }
}
