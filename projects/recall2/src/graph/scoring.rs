//! Behavioral scoring formula.
//!
//! Q200 Phase 3-4: Final ranking score combines cosine similarity,
//! CO_RETRIEVED gravity, memory importance, and source provenance.
//!
//! `score = (cosine * 0.6 + co_gravity * 0.2 + importance * 0.2) * provenance_multiplier`

use crate::config::ScoringConfig;
use crate::provenance::SourceProvenance;

/// Compute the final behavioral score for a search result.
///
/// Components:
/// - `cosine`: Dense vector similarity (0.0 to 1.0)
/// - `co_gravity`: Mean CO_RETRIEVED edge weight (0.0 to 1.0)
/// - `importance`: Memory importance tier (0.0 to 1.0)
/// - `provenance`: Source trust tier (multiplier 0.3 to 0.9)
///
/// The weights default to 0.6 / 0.2 / 0.2 per Q200 Phase 3 validation.
pub fn compute_score(
    cosine: f32,
    co_gravity: f32,
    importance: f32,
    provenance: &SourceProvenance,
    config: &ScoringConfig,
) -> f32 {
    let base = cosine * config.cosine_weight
        + co_gravity * config.co_retrieved_weight
        + importance * config.importance_weight;

    base * provenance.multiplier()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scoring_user_direct_high_importance() {
        let config = ScoringConfig {
            cosine_weight: 0.6,
            co_retrieved_weight: 0.2,
            importance_weight: 0.2,
        };

        let score = compute_score(0.95, 0.5, 0.9, &SourceProvenance::UserDirect, &config);
        // (0.95*0.6 + 0.5*0.2 + 0.9*0.2) * 0.9 = (0.57 + 0.10 + 0.18) * 0.9 = 0.765
        assert!((score - 0.765).abs() < 0.01, "score = {score}");
    }

    #[test]
    fn test_scoring_derived_low_importance() {
        let config = ScoringConfig {
            cosine_weight: 0.6,
            co_retrieved_weight: 0.2,
            importance_weight: 0.2,
        };

        let score = compute_score(0.80, 0.1, 0.3, &SourceProvenance::Derived, &config);
        // (0.80*0.6 + 0.1*0.2 + 0.3*0.2) * 0.3 = (0.48 + 0.02 + 0.06) * 0.3 = 0.168
        assert!((score - 0.168).abs() < 0.01, "score = {score}");
    }

    #[test]
    fn test_provenance_ordering() {
        let config = ScoringConfig {
            cosine_weight: 0.6,
            co_retrieved_weight: 0.2,
            importance_weight: 0.2,
        };

        // Same cosine/gravity/importance, different provenance
        let user = compute_score(0.9, 0.5, 0.5, &SourceProvenance::UserDirect, &config);
        let derived = compute_score(0.9, 0.5, 0.5, &SourceProvenance::Derived, &config);

        assert!(user > derived, "UserDirect ({user}) should rank higher than Derived ({derived})");
    }
}
