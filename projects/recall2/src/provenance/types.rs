//! Source provenance types and hook-type mapping.
//!
//! 5 tiers from highest trust (UserDirect, 0.9) to lowest (Derived, 0.3).
//! Hook event names auto-map to the appropriate tier.

use serde::{Deserialize, Serialize};

/// Source provenance tier — determines trust multiplier in scoring.
///
/// Q200 Phase 4: 5 tiers with multiplicative impact on retrieval score.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum SourceProvenance {
    /// Explicit user commands: /learn, /anchor, /never.
    /// Multiplier: 0.90
    UserDirect,

    /// Session summaries, verified system facts.
    /// Multiplier: 0.80
    VerifiedSystem,

    /// Tool output extractions (e.g., observe-edit.js).
    /// Multiplier: 0.50
    ToolOutput,

    /// Agent-produced content.
    /// Multiplier: 0.40
    AgentGenerated,

    /// Inferred or synthesized content.
    /// Multiplier: 0.30
    #[default]
    Derived,
}

impl SourceProvenance {
    /// Get the scoring multiplier for this provenance tier.
    pub fn multiplier(&self) -> f32 {
        match self {
            SourceProvenance::UserDirect => 0.90,
            SourceProvenance::VerifiedSystem => 0.80,
            SourceProvenance::ToolOutput => 0.50,
            SourceProvenance::AgentGenerated => 0.40,
            SourceProvenance::Derived => 0.30,
        }
    }

    /// Map a hook event type name to a provenance tier.
    ///
    /// Hook types from Recall 1.0:
    /// - "learn", "anchor", "never" → UserDirect
    /// - "session-summary", "stop" → VerifiedSystem
    /// - "observe-edit", "tool-output" → ToolOutput
    /// - "agent-generated" → AgentGenerated
    /// - Everything else → Derived
    pub fn from_hook_type(hook: &str) -> Self {
        match hook.to_lowercase().as_str() {
            "learn" | "anchor" | "never" | "user-direct" | "boost" => {
                SourceProvenance::UserDirect
            }
            "session-summary" | "stop" | "verified" | "verified-system" => {
                SourceProvenance::VerifiedSystem
            }
            "observe-edit" | "tool-output" | "post-tool" => SourceProvenance::ToolOutput,
            "agent-generated" | "agent" => SourceProvenance::AgentGenerated,
            _ => SourceProvenance::Derived,
        }
    }

    /// String representation for SQLite storage.
    pub fn as_str(&self) -> &'static str {
        match self {
            SourceProvenance::UserDirect => "UserDirect",
            SourceProvenance::VerifiedSystem => "VerifiedSystem",
            SourceProvenance::ToolOutput => "ToolOutput",
            SourceProvenance::AgentGenerated => "AgentGenerated",
            SourceProvenance::Derived => "Derived",
        }
    }

    /// Parse from string (e.g., from SQLite).
    pub fn from_str_lossy(s: &str) -> Self {
        match s {
            "UserDirect" => SourceProvenance::UserDirect,
            "VerifiedSystem" => SourceProvenance::VerifiedSystem,
            "ToolOutput" => SourceProvenance::ToolOutput,
            "AgentGenerated" => SourceProvenance::AgentGenerated,
            _ => SourceProvenance::Derived,
        }
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_multiplier_ordering() {
        assert!(SourceProvenance::UserDirect.multiplier() > SourceProvenance::VerifiedSystem.multiplier());
        assert!(SourceProvenance::VerifiedSystem.multiplier() > SourceProvenance::ToolOutput.multiplier());
        assert!(SourceProvenance::ToolOutput.multiplier() > SourceProvenance::AgentGenerated.multiplier());
        assert!(SourceProvenance::AgentGenerated.multiplier() > SourceProvenance::Derived.multiplier());
    }

    #[test]
    fn test_hook_type_mapping() {
        assert_eq!(SourceProvenance::from_hook_type("learn"), SourceProvenance::UserDirect);
        assert_eq!(SourceProvenance::from_hook_type("observe-edit"), SourceProvenance::ToolOutput);
        assert_eq!(SourceProvenance::from_hook_type("session-summary"), SourceProvenance::VerifiedSystem);
        assert_eq!(SourceProvenance::from_hook_type("unknown"), SourceProvenance::Derived);
    }

    #[test]
    fn test_roundtrip_str() {
        for prov in [
            SourceProvenance::UserDirect,
            SourceProvenance::VerifiedSystem,
            SourceProvenance::ToolOutput,
            SourceProvenance::AgentGenerated,
            SourceProvenance::Derived,
        ] {
            let s = prov.as_str();
            let roundtripped = SourceProvenance::from_str_lossy(s);
            assert_eq!(prov, roundtripped);
        }
    }
}
