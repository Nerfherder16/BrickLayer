"""
simulate.py — Recall Competitive Position Scorer.

This file tracks Recall's capability scores across 5 categories and 22 dimensions.
The agent updates SCENARIO PARAMETERS as research findings land — raising scores
where Recall is confirmed strong, lowering them where gaps are discovered.

Usage:
    python simulate.py > run.log 2>&1
    grep "^verdict:\|^primary_metric:\|^failure_reason:\|^category_" run.log

Output format (grep-friendly):
    primary_metric:      <float>   overall weighted competitive score
    category_retrieval:  <float>
    category_lifecycle:  <float>
    category_devex:      <float>
    category_operations: <float>
    category_product:    <float>
    verdict:             <HEALTHY|WARNING|FAILURE>
    failure_reason:      <str or NONE>
    critical_gaps:       <comma-separated dimension names or NONE>
"""

import io
import sys

from constants import (
    COMPETITOR_BASELINE,
    CRITICAL_GAP_THRESHOLD,
    FAILURE_THRESHOLD,
    FATAL_GAP_COUNT,
    WARNING_THRESHOLD,
    WEIGHT_DEVELOPER_EX,
    WEIGHT_LIFECYCLE,
    WEIGHT_OPERATIONS,
    WEIGHT_PRODUCT,
    WEIGHT_RETRIEVAL,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — Agent modifies this section.
# Each score represents Recall's current capability on that dimension.
# 0.0 = not implemented / far behind all competitors
# 0.5 = present but behind best-in-class
# 0.8 = competitive / on par with leaders
# 1.0 = best-in-class, clear leader
#
# Update scores as research findings confirm or refute capabilities.
# Update SCENARIO_NAME to describe what changed this run.
# =============================================================================

SCENARIO_NAME = (
    "FINAL — Q2.3/Q2.4/Q3.2/Q3.4/Q4.4 applied; all 25 questions complete (2026-03-15)"
)

# --- Retrieval & Core Intelligence (weight: 25%) ---
SEMANTIC_RETRIEVAL_QUALITY = 0.73  # Q2.5: qwen3-embedding:0.6b scores 64.33 MTEB Multilingual / 61.83 MTEB English v2; beats BGE-M3 and OpenAI text-3-large; #1 Ollama embedding model (1.2M pulls)
HYBRID_RETRIEVAL = 0.10  # No BM25 — pure vector only
RERANKING_QUALITY = 0.42  # Q2.1: sklearn GBM fast but no cross-encoder semantics; mem0 Platform has named reranker (+150-200ms); self-hosted peers have none
QUERY_UNDERSTANDING = 0.45  # Q2.1: mem0 Platform keyword expansion + Zep graph BFS implicit expansion; Recall has zero expansion
MEMORY_DEDUP_EFFECTIVENESS = 0.65  # Q2.3: hash+cosine+background consolidation is most complete pipeline; BUT cosine threshold undocumented, no graph entity dedup (mem0 has configurable 0.7 default), no LLM-judged NOOP pass. mem0's LLM-judged dedup has documented false-DELETE bugs (#1674, #2165) — Recall's approach is more stable but less semantically aware.

# --- Memory Lifecycle Management (weight: 20%) ---
IMPORTANCE_SCORING = 0.75  # Multi-factor: decay, access, recency
MEMORY_DECAY = 0.88  # Q2.2: confirmed zero competitors implement automatic access-frequency decay; Graphiti issue #1300 (Mar 2026) flags absence; decay is an emerging frontier
AUTO_CONSOLIDATION = 0.85  # Q2.2: mem0 Update Phase is write-time/session-scoped only; Recall hourly cross-session consolidation architecturally unique; no competitor matches
MEMORY_HYGIENE = 0.75  # Q2.2: no competitor has soft-delete + GC pipeline; Dec 2025 survey confirms emerging frontier
GRAPH_RELATIONSHIP_DEPTH = 0.88  # Q2.4: Deep schema research confirms Recall CAUSED_BY/SUPPORTS/CONTRADICTS/SUPERSEDES unique in all production systems. mem0=freeform LLM strings, no typed traversal. Zep/Graphiti=default RELATES_TO; custom Pydantic edge types exist but causal/epistemic require user-defined — not built-in. Letta=no graph. MAGMA (arXiv:2601.03236, Jan 2026) validates causal graph as unimplemented orthogonal dimension in all competitors. Graphiti custom types narrow gap slightly vs prior finding.

# --- Developer Experience (weight: 25%) ---
SDK_ECOSYSTEM = 0.05  # Q3.1: mem0 2M PyPI downloads/month, full CRUD+history+reset, embedded mode (0 infra), TS SDK. Recall: zero published package, raw HTTP only. CRITICAL gap confirmed.
API_SURFACE_COMPLETENESS = 0.60  # REST API exists but undocumented publicly
HOOK_INTEGRATION_DEPTH = (
    0.88  # Q1.1: mem0 has no hook system; Recall automatic observation confirmed unique
)
MULTI_LLM_SUPPORT = 0.22  # Q3.2: mem0=15 named providers + LiteLLM (100+); Letta=10+ BYOK; Zep=OpenAI-compat (no full local); Recall=Ollama-only extraction, but MCP layer is IDE-agnostic (Cursor/Windsurf MCP connects today); hook capture is Claude Code-only
DOCUMENTATION_QUALITY = 0.10  # Q3.5: mem0=Mintlify+API ref+AI search+LLMs.txt; Zep=Fern+3-lang SDK+migration guide; Letta=Starlight+"Open in Claude"+per-page AI; Recall=GitHub README only, no hosted site, no API ref, no quickstart. FAILURE.

# --- Operations (weight: 15%) ---
SELF_HOSTING_SIMPLICITY = 0.30  # Q3.3: mem0=0 services (embedded) or 3 (full with graph); Letta=1 container (PostgreSQL+pgvector bundled); Zep CE=dead; Recall=5-6 services + GPU hardware dependency
MULTI_USER_SUPPORT = 0.35  # Q3.4: user_id field is schema-only; no RTBF API, no user management UI, no agent_id field, no per-user API key; mem0=4-dim isolation (user+agent+app+run); Zep=per-user graph with RTBF; homelab target is single-user but family/multi-agent isolation unaddressed
OBSERVABILITY = 0.65  # Prometheus metrics + audit log + dashboard
PERFORMANCE_AT_SCALE = 0.60  # Untested beyond single-user homelab

# --- Product / End-User Experience (weight: 15%) ---
DASHBOARD_UX = 0.60  # React dashboard; functional but not polished
MEMORY_DISCOVERABILITY = 0.55  # Search + browse; no faceted filters
IMPORT_EXPORT = 0.25  # No bulk import/export tools
DATA_PORTABILITY = 0.30  # No standardized export format

# =============================================================================
# SCORING ENGINE — Do not modify below this line.
# =============================================================================

DIMENSIONS = {
    # category → {dimension_name: score}
    "retrieval": {
        "semantic_retrieval_quality": SEMANTIC_RETRIEVAL_QUALITY,
        "hybrid_retrieval": HYBRID_RETRIEVAL,
        "reranking_quality": RERANKING_QUALITY,
        "query_understanding": QUERY_UNDERSTANDING,
        "memory_dedup_effectiveness": MEMORY_DEDUP_EFFECTIVENESS,
    },
    "lifecycle": {
        "importance_scoring": IMPORTANCE_SCORING,
        "memory_decay": MEMORY_DECAY,
        "auto_consolidation": AUTO_CONSOLIDATION,
        "memory_hygiene": MEMORY_HYGIENE,
        "graph_relationship_depth": GRAPH_RELATIONSHIP_DEPTH,
    },
    "devex": {
        "sdk_ecosystem": SDK_ECOSYSTEM,
        "api_surface_completeness": API_SURFACE_COMPLETENESS,
        "hook_integration_depth": HOOK_INTEGRATION_DEPTH,
        "multi_llm_support": MULTI_LLM_SUPPORT,
        "documentation_quality": DOCUMENTATION_QUALITY,
    },
    "operations": {
        "self_hosting_simplicity": SELF_HOSTING_SIMPLICITY,
        "multi_user_support": MULTI_USER_SUPPORT,
        "observability": OBSERVABILITY,
        "performance_at_scale": PERFORMANCE_AT_SCALE,
    },
    "product": {
        "dashboard_ux": DASHBOARD_UX,
        "memory_discoverability": MEMORY_DISCOVERABILITY,
        "import_export": IMPORT_EXPORT,
        "data_portability": DATA_PORTABILITY,
    },
}

CATEGORY_WEIGHTS = {
    "retrieval": WEIGHT_RETRIEVAL,
    "lifecycle": WEIGHT_LIFECYCLE,
    "devex": WEIGHT_DEVELOPER_EX,
    "operations": WEIGHT_OPERATIONS,
    "product": WEIGHT_PRODUCT,
}


def score_categories(dimensions: dict) -> dict:
    return {
        cat: sum(scores.values()) / len(scores) for cat, scores in dimensions.items()
    }


def weighted_overall(category_scores: dict) -> float:
    return sum(category_scores[cat] * CATEGORY_WEIGHTS[cat] for cat in category_scores)


def find_critical_gaps(dimensions: dict) -> list[str]:
    gaps = []
    for scores in dimensions.values():
        for name, score in scores.items():
            if score <= CRITICAL_GAP_THRESHOLD:
                gaps.append(name)
    return gaps


def gap_to_leader(dimensions: dict) -> list[tuple[str, float]]:
    """Returns (dimension, gap) sorted largest gap first."""
    gaps = []
    for scores in dimensions.values():
        for name, score in scores.items():
            leader = COMPETITOR_BASELINE.get(name, 0.0)
            delta = leader - score
            if delta > 0:
                gaps.append((name, round(delta, 2)))
    return sorted(gaps, key=lambda x: x[1], reverse=True)


def evaluate() -> dict:
    cat_scores = score_categories(DIMENSIONS)
    overall = weighted_overall(cat_scores)
    critical_gaps = find_critical_gaps(DIMENSIONS)
    top_gaps = gap_to_leader(DIMENSIONS)

    verdict = "HEALTHY"
    reasons = []

    if len(critical_gaps) >= FATAL_GAP_COUNT:
        verdict = "FAILURE"
        reasons.append(
            f"{len(critical_gaps)} dimensions below critical threshold "
            f"({CRITICAL_GAP_THRESHOLD}): {', '.join(critical_gaps)}"
        )
    elif overall <= FAILURE_THRESHOLD:
        verdict = "FAILURE"
        reasons.append(
            f"Overall score {overall:.2f} ≤ {FAILURE_THRESHOLD} failure threshold"
        )
    elif overall <= WARNING_THRESHOLD or critical_gaps:
        verdict = "WARNING"
        if overall <= WARNING_THRESHOLD:
            reasons.append(
                f"Overall score {overall:.2f} ≤ {WARNING_THRESHOLD} warning threshold"
            )
        if critical_gaps:
            reasons.append(f"Critical gaps: {', '.join(critical_gaps)}")

    return {
        "primary_metric": round(overall, 3),
        "category_retrieval": round(cat_scores["retrieval"], 3),
        "category_lifecycle": round(cat_scores["lifecycle"], 3),
        "category_devex": round(cat_scores["devex"], 3),
        "category_operations": round(cat_scores["operations"], 3),
        "category_product": round(cat_scores["product"], 3),
        "verdict": verdict,
        "failure_reason": "; ".join(reasons) if reasons else "NONE",
        "critical_gaps": ", ".join(critical_gaps) if critical_gaps else "NONE",
        "top_gaps_vs_leaders": top_gaps[:5],
    }


if __name__ == "__main__":
    print(f"Recall Competitive Position — {SCENARIO_NAME}")
    print("---")

    results = evaluate()

    for key, val in results.items():
        if key == "top_gaps_vs_leaders":
            print(f"{key}:")
            for dim, gap in val:
                leader_score = COMPETITOR_BASELINE.get(dim, 0)
                all_scores = {cat: scores for cat, scores in DIMENSIONS.items()}
                recall_score = next(
                    (scores[dim] for scores in DIMENSIONS.values() if dim in scores), 0
                )
                print(
                    f"  {dim}: Recall={recall_score:.2f}  Leader={leader_score:.2f}  gap=-{gap:.2f}"
                )
        else:
            print(f"{key}: {val}")

    print("---")
    print("Category breakdown:")
    cat_scores = score_categories(DIMENSIONS)
    for cat, score in cat_scores.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        leader_avg = sum(COMPETITOR_BASELINE.get(d, 0) for d in DIMENSIONS[cat]) / len(
            DIMENSIONS[cat]
        )
        print(f"  {cat:12s} {bar} {score:.2f}  (leader avg: {leader_avg:.2f})")
