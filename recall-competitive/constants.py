"""
constants.py — Immutable competitive scoring thresholds.

DO NOT modify this file. These are the ground-truth benchmarks that
define what "competitive" means for a self-hosted AI memory system.
"""

# =============================================================================
# SCORING THRESHOLDS
# =============================================================================

# Average capability score (across all dimensions) required for each verdict
FAILURE_THRESHOLD = 0.50  # avg score ≤ this → FAILURE (not competitive)
WARNING_THRESHOLD = 0.65  # avg score ≤ this → WARNING (gaps need work)
# avg score > WARNING_THRESHOLD → HEALTHY (competitive in this category)

# Single-dimension critical gap threshold
# Any one dimension at or below this triggers at least a WARNING
CRITICAL_GAP_THRESHOLD = 0.25

# If this many dimensions hit the critical gap threshold → automatic FAILURE
FATAL_GAP_COUNT = 3

# =============================================================================
# DIMENSION WEIGHTS
# Dimensions are grouped into 5 categories. Within each category scores are
# averaged, then category averages are weighted to produce the overall score.
# =============================================================================

# Category weights (must sum to 1.0)
WEIGHT_RETRIEVAL = 0.25  # Core intelligence — how well does it find memories?
WEIGHT_LIFECYCLE = 0.20  # Memory health — creation, decay, consolidation, pruning
WEIGHT_DEVELOPER_EX = 0.25  # How easy is it to integrate and extend?
WEIGHT_OPERATIONS = 0.15  # How hard is it to run?
WEIGHT_PRODUCT = 0.15  # End-user experience and discoverability

# =============================================================================
# COMPETITIVE BASELINE
# These are approximate scores for the strongest competitor in each dimension.
# Used to compute "gap to leader" in simulation output.
# mem0 is the current benchmark leader for most developer-facing dimensions.
# =============================================================================

COMPETITOR_BASELINE = {
    # Retrieval
    "semantic_retrieval_quality": 0.80,  # mem0 / Zep are solid here
    "hybrid_retrieval": 0.70,  # mem0 supports BM25+vector
    "reranking_quality": 0.65,  # Zep has LLM reranking
    "query_understanding": 0.70,  # mem0 has query expansion
    "memory_dedup_effectiveness": 0.70,  # mem0 has content + semantic dedup
    # Lifecycle
    "importance_scoring": 0.75,  # mem0 has importance scoring
    "memory_decay": 0.50,  # rare in competitors — Recall ahead
    "auto_consolidation": 0.55,  # rare — Recall ahead
    "memory_hygiene": 0.50,  # rare — Recall ahead
    "graph_relationship_depth": 0.55,  # Letta has some graph; mem0 is shallow
    # Developer experience
    "sdk_ecosystem": 0.90,  # mem0 has Python + JS SDKs
    "api_surface_completeness": 0.80,  # mem0 REST + SDK
    "hook_integration_depth": 0.40,  # Recall is the clear leader here
    "multi_llm_support": 0.90,  # mem0 / Zep are LLM-agnostic
    "documentation_quality": 0.80,  # mem0 has proper docs site
    # Operations
    "self_hosting_simplicity": 0.75,  # mem0 is pip install + one config
    "multi_user_support": 0.85,  # mem0 / Zep have strong multi-tenant
    "observability": 0.60,  # varies; Zep has more ops tooling
    "performance_at_scale": 0.75,  # mem0 / Zep handle large stores
    # Product
    "dashboard_ux": 0.65,  # mem0 cloud has decent UI
    "memory_discoverability": 0.65,  # mem0 browse/search
    "import_export": 0.70,  # mem0 supports bulk ops
    "data_portability": 0.65,  # mem0 export to JSON
}
