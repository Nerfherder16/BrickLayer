"""
discover_skill_candidates.py

Queries Recall for high-frequency, high-importance patterns that may warrant
formalization as skills. Outputs candidates to .mas/skill_candidates.json.
Skill creation still goes through skill-forge — this is discovery only.

Usage:
    python masonry/scripts/discover_skill_candidates.py
    python masonry/scripts/discover_skill_candidates.py --min-importance 0.75 --min-count 3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bl.recall_bridge import search_prior_findings

CANDIDATE_FILE = Path(".mas/skill_candidates.json")

_STOP_WORDS = {"the", "a", "is", "in", "of", "to", "and", "for", "that", "with", "was", "are"}


def discover_candidates(min_importance: float = 0.7, min_count: int = 3) -> list[dict]:
    """
    Find patterns in Recall that appear >= min_count times with >= min_importance.
    Returns ranked list of candidate skill descriptions.
    """
    candidates: list[dict] = []

    for domain in ("autoresearch", "agent-performance", "bricklayer-trace"):
        results = search_prior_findings(
            query="successful pattern high confidence repeated",
            domain=domain,
            limit=50,
        )
        high_importance = [
            r for r in results
            if r.get("importance", 0) >= min_importance
            and r.get("verdict") not in ("FAILURE", "REGRESSION", "INCONCLUSIVE")
        ]
        candidates.extend(high_importance)

    # Cluster by summary word-overlap (3+ significant words in common)
    clusters: list[list[dict]] = []
    used: set[int] = set()
    for i, c in enumerate(candidates):
        if i in used:
            continue
        words_i = set(c.get("content", "").lower().split()) - _STOP_WORDS
        cluster = [c]
        for j in range(i + 1, len(candidates)):
            if j in used:
                continue
            words_j = set(candidates[j].get("content", "").lower().split()) - _STOP_WORDS
            if len(words_i & words_j) >= 3:
                cluster.append(candidates[j])
                used.add(j)
        if len(cluster) >= min_count:
            clusters.append(cluster)
            used.add(i)

    skill_candidates = []
    for cluster in sorted(clusters, key=len, reverse=True):
        skill_candidates.append({
            "frequency": len(cluster),
            "avg_importance": round(
                sum(r.get("importance", 0.5) for r in cluster) / len(cluster), 3
            ),
            "representative_summary": cluster[0].get("content", "")[:120],
            "sample_verdicts": list({r.get("verdict") for r in cluster[:5] if r.get("verdict")}),
            "suggested_skill_name": None,  # skill-forge names it
            "source_tags": list({
                t for r in cluster[:5] for t in r.get("tags", [])
                if t.startswith("agent:") or t.startswith("project:")
            }),
        })

    return skill_candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover skill candidates from Recall patterns")
    parser.add_argument("--min-importance", type=float, default=0.7)
    parser.add_argument("--min-count", type=int, default=3)
    args = parser.parse_args()

    candidates = discover_candidates(args.min_importance, args.min_count)

    CANDIDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_FILE.write_text(json.dumps(candidates, indent=2), encoding="utf-8")

    print(f"[discover_skill_candidates] {len(candidates)} candidates → {CANDIDATE_FILE}")
    for c in candidates[:5]:
        print(
            f"  freq={c['frequency']} importance={c['avg_importance']:.2f} "
            f"summary={c['representative_summary'][:80]}"
        )
