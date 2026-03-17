"""
constants.py — Immutable thresholds for frontier discovery.

DO NOT modify. These define what counts as a genuine discovery vs. noise.
"""

# --- Idea quality thresholds ---
BREAKTHROUGH_THRESHOLD = 0.60  # novelty × evidence × feasibility ≥ this = BREAKTHROUGH
PROMISING_THRESHOLD = 0.30  # ≥ this but < BREAKTHROUGH = PROMISING
MIN_EVIDENCE_SCORE = 0.40  # below this = SPECULATIVE regardless of novelty
MIN_NOVELTY_SCORE = 0.65  # below this = INCREMENTAL (someone already built it)

# --- Verdict thresholds ---
BREAKTHROUGH_COUNT_FOR_HEALTHY = 3  # need this many BREAKTHROUGH ideas for HEALTHY
SPECULATIVE_COUNT_FOR_WARNING = 5  # too many speculative findings = unfocused research

# --- Scoring weights ---
WEIGHT_NOVELTY = 0.40  # most important: is this genuinely new?
WEIGHT_EVIDENCE = 0.35  # second: is it validated somewhere?
WEIGHT_FEASIBILITY = 0.25  # third: can we actually build it?
