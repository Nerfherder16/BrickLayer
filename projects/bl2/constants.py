"""
constants.py — Immutable system rules for BrickLayer 2.0 Engine campaign.

These represent the correctness contracts BL 2.0 must uphold.
"""

# =============================================================================
# CAMPAIGN HEALTH THRESHOLDS
# =============================================================================

# Fraction of questions that must be HEALTHY/FIXED/COMPLIANT for the engine to be
# considered production-ready
CAMPAIGN_HEALTHY_THRESHOLD = 0.70  # 70% clean = HEALTHY
CAMPAIGN_WARNING_THRESHOLD = 0.50  # 50–70% = WARNING, below 50% = FAILURE

# =============================================================================
# HEAL LOOP CONTRACTS
# =============================================================================

# Maximum cycles the self-healing loop may run before giving up
HEAL_LOOP_MAX_CYCLES = 3

# A heal loop that produces FIX_FAILED on all cycles is itself a FAILURE
# A heal loop that produces FIXED within max cycles is HEALTHY

# =============================================================================
# SESSION CONTEXT CONTRACTS
# =============================================================================

# session-context.md truncation window (chars)
SESSION_CONTEXT_WINDOW = 2000

# =============================================================================
# VERDICT COVERAGE
# =============================================================================

# Total expected distinct verdict types in BL 2.0
EXPECTED_VERDICT_COUNT = 26

# Verdicts that must appear in _PARKED_STATUSES (questions.py)
REQUIRED_PARKED = [
    "DIAGNOSIS_COMPLETE",
    "PENDING_EXTERNAL",
    "DONE",
    "INCONCLUSIVE",
    "FIXED",
    "FIX_FAILED",
    "COMPLIANT",
    "NON_COMPLIANT",
    "CALIBRATED",
    "BLOCKED",
]

# Verdicts that classify_failure_type() must NOT treat as failures
NON_FAILURE_VERDICTS = [
    "HEALTHY",
    "WARNING",
    "DIAGNOSIS_COMPLETE",
    "FIXED",
    "CALIBRATED",
    "COMPLIANT",
    "PARTIAL",
    "NOT_APPLICABLE",
    "IMPROVEMENT",
    "OK",
    "DEGRADED",
    "DEGRADED_TRENDING",
    "ALERT",
    "UNKNOWN",
    "PROMISING",
    "BLOCKED",
    "WEAK",
    "SUBJECTIVE",
]

# =============================================================================
# GRACEFUL-FAIL CONTRACTS
# =============================================================================

# Recall bridge timeout (seconds) — must fail fast enough not to block campaign
RECALL_HEALTH_TIMEOUT = 2.0
RECALL_OPERATION_TIMEOUT = 5.0
