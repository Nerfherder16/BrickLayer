"""
BrickLayer → Training System schema mappings.

Isolated here so verdict weights and eligibility rules can be tuned
without touching the export logic.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Verdict → outcome classification
# ---------------------------------------------------------------------------

# Full pass — agent completed the task correctly
PASS_VERDICTS: frozenset[str] = frozenset({
    "HEALTHY",
    "FIXED",
    "COMPLIANT",
    "CALIBRATED",
    "IMPROVEMENT",
    "FRONTIER_VIABLE",
    "DIAGNOSIS_COMPLETE",
    "VALIDATED",
    "OPTIMIZED",
    "PREDICTED",
    "ALERT_RESOLVED",
})

# Partial pass — something was found but not a clean success or clean failure
# Value = partial_credit score (0.0–1.0)
PARTIAL_VERDICTS: dict[str, float] = {
    "WARNING":          0.70,
    "FRONTIER_PARTIAL": 0.60,
    "IMMINENT":         0.50,
    "PROBABLE":         0.50,
    "DEGRADED":         0.40,
    "INCONCLUSIVE":     0.30,
    "ALERT":            0.25,
}

# Full fail — agent either broke something or produced unusable output
FAIL_VERDICTS: frozenset[str] = frozenset({
    "FAILURE",
    "FIX_FAILED",
    "NON_COMPLIANT",
    "REGRESSION",
    "FRONTIER_BLOCKED",
})

# Verdicts that should never appear in SFT training data regardless of score
SFT_BLOCKED_VERDICTS: frozenset[str] = frozenset({
    "INCONCLUSIVE",
    "FIX_FAILED",
    "FRONTIER_BLOCKED",
})


def verdict_to_binary_pass(verdict: str) -> bool:
    """True for verdicts that represent task success."""
    return verdict.upper() in PASS_VERDICTS


def verdict_to_partial_credit(verdict: str) -> float:
    """
    Returns a 0.0–1.0 partial credit score.
    PASS verdicts = 1.0, FAIL verdicts = 0.0, partial verdicts = per-table value.
    """
    v = verdict.upper()
    if v in PASS_VERDICTS:
        return 1.0
    if v in FAIL_VERDICTS:
        return 0.0
    return PARTIAL_VERDICTS.get(v, 0.2)


# ---------------------------------------------------------------------------
# Confidence string → float
# ---------------------------------------------------------------------------

CONFIDENCE_MAP: dict[str, float] = {
    "high":      1.0,
    "medium":    0.7,
    "low":       0.3,
    "uncertain": 0.0,
}

NEEDS_HUMAN_THRESHOLD = 0.35  # matches findings.py


def confidence_str_to_float(confidence: str | float | None) -> float:
    """Normalise confidence from string label, numeric string, or raw float."""
    if confidence is None:
        return 0.5
    if isinstance(confidence, (int, float)):
        return float(confidence)
    s = str(confidence).strip().lower()
    # Handle numeric strings like "0.82" from scored_all.jsonl
    try:
        return max(0.0, min(1.0, float(s)))
    except ValueError:
        pass
    return CONFIDENCE_MAP.get(s, 0.5)


# ---------------------------------------------------------------------------
# Composite trajectory score
# ---------------------------------------------------------------------------

# Minimum trajectory_score for a trace to be SFT-eligible
SFT_MIN_SCORE: float = 0.82


def compute_trajectory_score(
    eval_score_0_100: int | float | None,
    verdict: str,
    confidence: str | float | None = None,
) -> float:
    """
    Produce a single 0.0–1.0 trajectory score from BL's scoring signals.

    Formula:
        base   = eval_score / 100  (from scored_all.jsonl, fallback = partial_credit)
        conf   = confidence_float  (dampens score when agent was uncertain)
        result = base * 0.8 + conf * 0.2

    Reasoning: eval_score already incorporates evidence quality and verdict
    clarity. Confidence is a secondary signal that slightly rewards agents
    that knew what they found vs. those that stumbled into a correct verdict.
    """
    partial = verdict_to_partial_credit(verdict)

    if eval_score_0_100 is not None:
        base = max(0.0, min(1.0, float(eval_score_0_100) / 100.0))
    else:
        base = partial

    conf = confidence_str_to_float(confidence)
    return round(base * 0.8 + conf * 0.2, 4)


def is_sft_eligible(
    verdict: str,
    trajectory_score: float,
    needs_human: bool = False,
) -> bool:
    """
    True if this trace should go into the SFT training dataset.

    Rules:
    - Minimum trajectory score met
    - Verdict is not in the blocked set (INCONCLUSIVE etc. add noise)
    - Agent was confident enough (needs_human=False means confidence >= 0.35)
    """
    if trajectory_score < SFT_MIN_SCORE:
        return False
    if verdict.upper() in SFT_BLOCKED_VERDICTS:
        return False
    if needs_human:
        return False
    return True


# ---------------------------------------------------------------------------
# Critic flag from verdict
# ---------------------------------------------------------------------------

def verdict_to_critic_flag(verdict: str) -> str:
    """Map BL verdict to training system critic flag vocabulary."""
    v = verdict.upper()
    if v in PASS_VERDICTS:
        return "good"
    if v in FAIL_VERDICTS:
        return "mistake"
    if v == "INCONCLUSIVE":
        return "waste"
    return "good"
