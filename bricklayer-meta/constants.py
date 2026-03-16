"""
constants.py — Immutable campaign quality thresholds for bricklayer-meta.

DO NOT modify this file. These values represent ground-truth quality gates
derived from empirical observation of BrickLayer campaigns against Recall.

Unlike financial simulations, there is no treasury. The "asset" is information
density — the rate at which the campaign produces unique, trustworthy findings.
The "bankruptcy" condition is a campaign producing noise instead of signal.
"""

# =============================================================================
# PRIMARY METRIC THRESHOLDS — Campaign yield (unique actionable / total run)
# =============================================================================

# Below this, the campaign is producing mostly noise. Less than 1 in 4 questions
# yields a finding that is both novel AND trustworthy. The campaign is wasting
# compute and human review time on redundant or drifted verdicts.
CAMPAIGN_YIELD_FAILURE = 0.25

# Below this, the campaign is underperforming. Less than half of questions
# are productive. Acceptable in late waves (natural saturation) but not
# in Wave 1-2 where the failure space should still be open.
CAMPAIGN_YIELD_WARNING = 0.45

# =============================================================================
# SECONDARY METRIC THRESHOLDS
# =============================================================================

# Synthesis coherence: fraction of synthesis content that is novel vs. redundant
# with previous-wave synthesis. Below this, the synthesizer is just rephrasing
# prior findings with different words — STOP/PIVOT recommendation will be wrong.
SYNTHESIS_COHERENCE_FAILURE = 0.35

# Wave novelty floor: the minimum wave_yield across all waves. If any single wave
# produces < this fraction of actionable findings, that wave was fully saturated.
# The campaign should have stopped or pivoted before running it.
WAVE_NOVELTY_FLOOR_FAILURE = 0.15

# Fix loop regression rate: fraction of fix attempts that introduce a regression
# in a previously-HEALTHY question. Above this, fix-loop is net-negative —
# it resolves the immediate FAILURE but creates future ones silently.
FIX_REGRESSION_FAILURE = 0.20

# =============================================================================
# BEHAVIORAL CONSTANTS — Derived from BrickLayer source and Recall campaign data
# =============================================================================

# Observed verdict accuracy rates (from Recall campaign peer-review OVERRIDE rate):
# - Specialist agents (quantitative-analyst, probe-runner, etc.) produce OVERRIDE
#   at roughly 10-15% rate across 36 waves. True accuracy ≈ 1 - 0.125 = 0.875.
# - Generalist fallbacks (no matching agent, forge hasn't filled the gap) produce
#   OVERRIDE at roughly 35-40% rate. True accuracy ≈ 1 - 0.375 = 0.625.
BASE_SPECIALIST_ACCURACY = 0.875
BASE_GENERALIST_ACCURACY = 0.625

# Per-wave coverage saturation rate (reference: 7 questions/wave).
# Each wave, the fraction of questions exploring novel failure space decays by this
# amount × (actual_questions / 7). Calibrated so Wave 4 at 7 q/wave has ~55%
# uniqueness — consistent with synthesis notes "consistent with prior findings"
# first appearing around Wave 4-5 in the Recall campaign.
WAVE_SATURATION_RATE = 0.15

# Fraction of drifted verdicts caught by peer-reviewer.
# In practice, peer-reviewer runs async and doesn't always complete before the
# next question starts, and it confirms more than it overrides. Empirically,
# roughly 55% of genuinely wrong verdicts get an OVERRIDE eventually.
PEER_REVIEW_CORRECTION_RATE = 0.55
