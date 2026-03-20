"""
constants.py — ADBP v2 Immutable System Rules

DO NOT modify during simulation runs.
These represent fixed protocol rules that cannot be changed without a system redesign.
"""

# ── Token Economics ───────────────────────────────────────────────────────────
TOKEN_FACE_VALUE = 2.00  # USD purchasing power of 1 token at vendors (fixed forever)
MINT_PRICE = 1.00  # USD cost for employee to mint 1 token
ESCROW_START_PER_TOKEN = 1.00  # USD deposited to escrow at mint time

# ── Fee Split ─────────────────────────────────────────────────────────────────
# Employee fees are split between escrow (backs tokens) and operator (platform revenue).
FEE_TO_ESCROW_PCT = 0.65  # 65% of monthly employee fee → escrow pool
FEE_TO_OPERATOR_PCT = 0.35  # 35% of monthly employee fee → operator (admin + revenue)

# ── Burn Mechanics ────────────────────────────────────────────────────────────
# Burns activate only when pool-average escrow per token reaches $2.00
# (equivalent to CRR >= 1.0)
BURN_ELIGIBLE_CRR = 1.00  # Burns activate at this CRR threshold (escrow = $2/token)
BURN_RATE_FLOOR = 0.02  # 2% minimum burn rate (traditional tokenomics floor)
BURN_RATE_CEILING = 0.15  # 15% maximum burn rate (traditional tokenomics ceiling)

# ── CRR Thresholds ────────────────────────────────────────────────────────────
# System starts at CRR ~0.50 (mint $1 per $2 obligation).
# Fees + interest push CRR toward 1.0. Burns activate at CRR >= 1.0.
CRR_OPERATIONAL_TARGET = 0.65  # Healthy operating CRR during growth phase
CRR_MINT_PAUSE = 0.40  # Halt minting — escrow dangerously thin
CRR_CRITICAL = 0.35  # Insolvent — emergency halt
CRR_OVERCAPITALIZED = 2.00  # Burns allowed at ceiling rate

# ── Supply Rules ──────────────────────────────────────────────────────────────
CAPACITY_RATIO = 0.50  # Circulating tokens must stay <= 50% of total vendor capacity
MONTHLY_MINT_CAP_PER_EMPLOYEE = 5_000  # Hard per-employee monthly mint ceiling
EXPECTED_MONTHLY_MINT_PER_EMPLOYEE = 2_000  # Expected actual monthly usage

# ── Interest ──────────────────────────────────────────────────────────────────
ANNUAL_INTEREST_RATE = 0.04  # 4% annual yield on escrow (T-bill/money market)
MONTHLY_INTEREST_RATE = ANNUAL_INTEREST_RATE / 12

# ── Growth Curve (cumulative employees by month) ──────────────────────────────
GROWTH_CURVE = [
    100,
    500,
    1_000,
    2_000,
    5_000,
    8_000,
    10_000,
    20_000,
    50_000,
    100_000,
    150_000,
    200_000,
    250_000,
]
GROWTH_TARGET_MONTH = 60  # Month at which 5M employees is reached
GROWTH_TARGET_EMPLOYEES = 5_000_000

# ── Verdict Thresholds ────────────────────────────────────────────────────────
FAILURE_THRESHOLD = CRR_CRITICAL  # CRR below this = FAILURE
WARNING_THRESHOLD = CRR_MINT_PAUSE  # CRR below this = WARNING
