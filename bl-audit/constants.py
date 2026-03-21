"""
constants.py — Immutable system rules for this project.

DO NOT modify this file. These values represent the ground-truth system
constraints that the simulation validates against.

Replace all placeholder values with project-specific constants before
starting the research loop.
"""

# =============================================================================
# SYSTEM CONSTANTS — Replace with project-specific values.
# =============================================================================

# --- Core economics ---
SEED_CAPITAL = 2_000_000  # Initial capital available to the system

# --- Verdict thresholds ---
FAILURE_THRESHOLD = 6  # Primary metric below this = FAILURE
WARNING_THRESHOLD = 12  # Primary metric below this = WARNING

# --- System behavior constants ---
# Add project-specific constants here, e.g.:
# BURN_RATE = 0.01774            # ADBP: credit burn rate per velocity cycle
# RECIRCULATION_TO_MINT_RATIO = 2.0
# BASE_ANNUAL_VELOCITY = 12
