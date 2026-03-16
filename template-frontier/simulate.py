"""
simulate.py — Frontier Discovery Scorer.

Tracks ideas discovered during the research loop. Each idea is scored on three dimensions:

  NOVELTY:      Does any production system implement this? (1.0 = no one anywhere)
  EVIDENCE:     Validated in an adjacent field? (1.0 = peer-reviewed + replicated)
  FEASIBILITY:  Buildable with the current stack? (1.0 = 1-2 week implementation)

primary_metric = mean quality of all BREAKTHROUGH ideas
  quality = (novelty × WEIGHT_NOVELTY) + (evidence × WEIGHT_EVIDENCE) + (feasibility × WEIGHT_FEASIBILITY)

Verdict:
  BREAKTHROUGH  ≥ 3 ideas above BREAKTHROUGH_THRESHOLD
  PROMISING     ≥ 1 idea above BREAKTHROUGH_THRESHOLD
  INCREMENTAL   All ideas below PROMISING_THRESHOLD
  SPECULATIVE   Too many ideas with evidence < MIN_EVIDENCE_SCORE

Usage:
    python simulate.py > run.log 2>&1
    grep "^verdict:\\|^primary_metric:\\|^breakthrough_count:" run.log

Agent modifies IDEAS dict as research findings arrive.
Each key is a short idea slug. Each value is (novelty, evidence, feasibility).
"""

import io
import sys

from constants import (
    BREAKTHROUGH_COUNT_FOR_HEALTHY,
    BREAKTHROUGH_THRESHOLD,
    MIN_EVIDENCE_SCORE,
    MIN_NOVELTY_SCORE,
    PROMISING_THRESHOLD,
    SPECULATIVE_COUNT_FOR_WARNING,
    WEIGHT_EVIDENCE,
    WEIGHT_FEASIBILITY,
    WEIGHT_NOVELTY,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — Agent modifies this section.
# Add an entry to IDEAS for every frontier idea discovered.
# Format: "idea_slug": (novelty, evidence, feasibility)
#
# Scoring guide:
#   novelty     1.0 = zero production implementations found anywhere
#               0.5 = exists in research but no production system
#               0.0 = widely implemented
#
#   evidence    1.0 = peer-reviewed, replicated, well-established in source field
#               0.5 = credible source field practice, limited formal study
#               0.0 = intuition only, no external validation
#
#   feasibility 1.0 = 1-2 week implementation with current stack
#               0.5 = 1-3 months, requires new library or component
#               0.0 = requires new hardware or years of research
# =============================================================================

SCENARIO_NAME = "Baseline — no ideas discovered yet"

IDEAS = {
    # "example_idea": (novelty, evidence, feasibility),
    # Agent adds entries here as research findings arrive.
}

# =============================================================================
# SCORING ENGINE — Do not modify below this line.
# =============================================================================


def score_idea(novelty: float, evidence: float, feasibility: float) -> float:
    return (
        novelty * WEIGHT_NOVELTY
        + evidence * WEIGHT_EVIDENCE
        + feasibility * WEIGHT_FEASIBILITY
    )


def classify_idea(novelty: float, evidence: float, feasibility: float) -> str:
    if novelty < MIN_NOVELTY_SCORE:
        return "INCREMENTAL"
    if evidence < MIN_EVIDENCE_SCORE:
        return "SPECULATIVE"
    q = score_idea(novelty, evidence, feasibility)
    if q >= BREAKTHROUGH_THRESHOLD:
        return "BREAKTHROUGH"
    if q >= PROMISING_THRESHOLD:
        return "PROMISING"
    return "SPECULATIVE"


def evaluate() -> dict:
    if not IDEAS:
        return {
            "primary_metric": 0.0,
            "breakthrough_count": 0,
            "promising_count": 0,
            "speculative_count": 0,
            "incremental_count": 0,
            "verdict": "FAILURE",
            "failure_reason": "No ideas discovered yet — run the research loop",
            "top_ideas": [],
        }

    scored = []
    counts = {"BREAKTHROUGH": 0, "PROMISING": 0, "SPECULATIVE": 0, "INCREMENTAL": 0}

    for slug, (n, e, f) in IDEAS.items():
        cls = classify_idea(n, e, f)
        q = score_idea(n, e, f)
        counts[cls] += 1
        scored.append((slug, cls, q, n, e, f))

    scored.sort(key=lambda x: x[2], reverse=True)

    breakthrough_ideas = [s for s in scored if s[1] == "BREAKTHROUGH"]
    primary = (
        sum(s[2] for s in breakthrough_ideas) / len(breakthrough_ideas)
        if breakthrough_ideas
        else 0.0
    )

    verdict = "INCREMENTAL"
    reasons = []

    if counts["BREAKTHROUGH"] >= BREAKTHROUGH_COUNT_FOR_HEALTHY:
        verdict = "BREAKTHROUGH"
    elif counts["BREAKTHROUGH"] >= 1:
        verdict = "PROMISING"
    elif counts["SPECULATIVE"] >= SPECULATIVE_COUNT_FOR_WARNING:
        verdict = "SPECULATIVE"
        reasons.append(
            f"{counts['SPECULATIVE']} speculative ideas — research needs better adjacent-field evidence"
        )

    return {
        "primary_metric": round(primary, 3),
        "breakthrough_count": counts["BREAKTHROUGH"],
        "promising_count": counts["PROMISING"],
        "speculative_count": counts["SPECULATIVE"],
        "incremental_count": counts["INCREMENTAL"],
        "verdict": verdict,
        "failure_reason": "; ".join(reasons) if reasons else "NONE",
        "top_ideas": scored[:5],
    }


if __name__ == "__main__":
    print(f"Frontier Discovery — {SCENARIO_NAME}")
    print(f"Total ideas tracked: {len(IDEAS)}")
    print("---")

    results = evaluate()

    for key, val in results.items():
        if key == "top_ideas":
            print("top_ideas:")
            for slug, cls, q, n, e, f in val:
                print(
                    f"  [{cls:12s}] {slug:40s}  quality={q:.3f}  N={n:.2f} E={e:.2f} F={f:.2f}"
                )
        else:
            print(f"{key}: {val}")

    print("---")
    print("All ideas:")
    for slug, (n, e, f) in IDEAS.items():
        cls = classify_idea(n, e, f)
        q = score_idea(n, e, f)
        bar = "█" * int(q * 20) + "░" * (20 - int(q * 20))
        print(f"  {bar} {q:.3f}  [{cls:12s}]  {slug}")
