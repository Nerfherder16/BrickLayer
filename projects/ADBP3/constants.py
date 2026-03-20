"""
constants.py — ADBP v3 Immutable System Rules

DO NOT modify this file. These values are ground-truth system constraints
derived from the ADBP design document and confirmed by Tim.

Agent modifies SCENARIO PARAMETERS in simulate.py only.
"""

# =============================================================================
# CREDIT ECONOMICS
# =============================================================================

CREDIT_PRICE = 1.00  # Employee pays $1.00 per credit → treasury inflow
BURN_COST_PER_CREDIT = 2.00  # Treasury pays $2.00 per credit burned (discretionary)
ANNUAL_INTEREST_RATE = 0.04  # 4% APR on treasury wallet balance
MONTHLY_INTEREST_RATE = ANNUAL_INTEREST_RATE / 12  # 0.3333% per month

# =============================================================================
# EMPLOYEE CONSTRAINTS
# =============================================================================

MAX_CREDITS_PER_EMPLOYEE = 5_000  # Hard monthly cap per employee

# =============================================================================
# ADMIN REVENUE
# =============================================================================

EMPLOYEE_FEE_RATE = 0.10  # 10% fee on credit purchases → admin revenue pool
# Distributed to vendors/employers pro-rata by
# recirculation share. Does NOT flow to treasury.

# =============================================================================
# NETWORK
# =============================================================================

ANNUAL_VELOCITY = 12  # B2B credit recirculation cycles per year (background)
# No direct treasury cash flow — context only.

# =============================================================================
# VERDICT THRESHOLDS
# Primary metric: backing_ratio = treasury_wallet / total_credits_outstanding
# Interpretation: how many dollars the treasury holds per $1 of credit face value
# =============================================================================

FAILURE_THRESHOLD = 0.50  # Backing ratio below 50% = FAILURE
WARNING_THRESHOLD = 0.75  # Backing ratio below 75% = WARNING
