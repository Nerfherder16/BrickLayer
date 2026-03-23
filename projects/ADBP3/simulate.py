"""
simulate.py — ADBP v3 Reserve-Backed Credit System Simulation
Final model incorporating Monte Carlo findings.

Treasury mechanics (confirmed):
  Inflow:   $1.00 per credit minted (employee purchase price → treasury)
  Growth:   4% APR interest on wallet balance (monthly, prior-period interest added)
  Outflow:  $2.00 per credit burned (discretionary, threshold-triggered)

Admin revenue (tracked separately — does NOT flow to treasury):
  Pool:     credits_minted × 10% employee fee per period
  Dist:     pro-rata by vendor/employer recirculation share

Burn strategy (MC-optimized, replacing arbitrary fixed-date burns):
  Trigger:  burn fires when backing_ratio >= BURN_TRIGGER_RATIO
  Size:     burn BURN_PCT of outstanding credits, subject to affordability cap
  Cap:      post-burn backing ratio never drops below BURN_FLOOR_RATIO
            max_burnable = (wallet - floor × total) / (burn_cost_per_credit - floor)
  Cooldown: BURN_MIN_COOLDOWN months between consecutive burns
  Eligible: burns cannot fire before BURN_FIRST_ELIGIBLE month

MC findings summary (20,000 runs, 120 months):
  - Trigger >= 1.20x → 100% HEALTHY, zero burns fire in 10yr window
  - Trigger 1.10–1.20x → 93.5% HEALTHY, occasional large burns
  - Trigger ~1.15x + burn 30% → best score (max destruction + HEALTHY)
  - Trigger ~0.95x + burn 2–3% → most stable (ratio pinned near 100%)
  - Affordability cap → FAILURE rate drops from 2.3% to 0.0%

Primary metric:   backing_ratio = wallet / total_credits (face-value backing)
  HEALTHY:  >= 0.75
  WARNING:  0.50 – 0.74
  FAILURE:  < 0.50

Secondary metric: burn_coverage = wallet / (total_credits × $2)
  Represents fraction of full burn-out obligation the treasury can cover.

Usage:
    python simulate.py
    python simulate.py > run.log 2>&1
    grep "^verdict:" run.log
    grep "^primary_metric:" run.log
"""

import io
import sys

from constants import (
    BURN_COST_PER_CREDIT,
    CREDIT_PRICE,
    EMPLOYEE_FEE_RATE,
    FAILURE_THRESHOLD,
    MAX_CREDITS_PER_EMPLOYEE,
    MONTHLY_INTEREST_RATE,
    WARNING_THRESHOLD,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — Agent modifies ONLY this section.
# Each run tests one hypothesis. Change parameters, run, read verdict.
# =============================================================================

SCENARIO_NAME = (
    "Optimal — threshold burn at 114.6%, 30.2% size, 8mo cooldown (MC best score)"
)

# --- Employee growth (linear) ---
INITIAL_EMPLOYEES = 1_000  # Employees at month 1
EMPLOYEE_GROWTH_PER_MONTH = 1_000  # Additive growth per month

# --- Credit purchase behavior ---
CREDITS_PER_EMPLOYEE = 2_000  # Monthly credits purchased per employee
# Hard-capped at MAX_CREDITS_PER_EMPLOYEE (5,000)

# --- Simulation duration ---
SIMULATION_MONTHS = 120  # Months to simulate (120 = 10 years)

# --- Threshold-based burn strategy (MC-optimized) ---
# Burn fires automatically when backing_ratio >= BURN_TRIGGER_RATIO.
# Size is BURN_PCT of outstanding credits, capped by affordability.
#
# Preset options (from MC results):
#   Aggressive / max liability reduction:
#     BURN_TRIGGER_RATIO = 1.146, BURN_PCT = 0.302, BURN_MIN_COOLDOWN = 8
#     → 1 large burn, 30% of credits destroyed, min backing 77.6%
#
#   Conservative / maximum stability:
#     BURN_TRIGGER_RATIO = 0.966, BURN_PCT = 0.021, BURN_MIN_COOLDOWN = 6
#     → 18 small burns, ratio pinned near 97–100%, 12% of credits destroyed
#
#   No burns (observe natural growth only):
#     BURN_TRIGGER_RATIO = 9.999  (trigger never fires in 10yr window)

BURN_TRIGGER_RATIO = 1.146  # Burn fires when backing_ratio >= this
BURN_PCT = 0.302  # Fraction of total_credits to burn per event
BURN_MIN_COOLDOWN = 8  # Minimum months between consecutive burns
BURN_FIRST_ELIGIBLE = 13  # Earliest month a burn can fire (ramp-up protection)
BURN_FLOOR_RATIO = FAILURE_THRESHOLD  # Affordability cap floor (never breach this)

# =============================================================================
# SIMULATION ENGINE — Do not modify below this line.
# =============================================================================


def get_employees(month: int) -> int:
    return INITIAL_EMPLOYEES + (month - 1) * EMPLOYEE_GROWTH_PER_MONTH


def get_credits_per_employee() -> int:
    return min(CREDITS_PER_EMPLOYEE, MAX_CREDITS_PER_EMPLOYEE)


def run_simulation() -> tuple[list[dict], str | None]:
    wallet = 0.0
    total_credits = 0
    interest_prev = 0.0
    last_burn_month = 0

    cumulative_admin_revenue = 0.0
    cumulative_credits_minted = 0
    cumulative_credits_burned = 0
    cumulative_burn_cost = 0.0

    failure_reason = None
    records = []
    credits_per_emp = get_credits_per_employee()

    for month in range(1, SIMULATION_MONTHS + 1):
        employees = get_employees(month)
        credits_minted = employees * credits_per_emp

        # --- Treasury inflow: $1.00 per credit minted ---
        treasury_inflow = credits_minted * CREDIT_PRICE

        # --- Admin revenue pool: 10% employee fee (tracked, not in treasury) ---
        admin_fee_period = credits_minted * EMPLOYEE_FEE_RATE

        # --- Wallet update ---
        # Prior-period interest flows in first, then new inflow.
        # Matches spreadsheet: H[t] = H[t-1] + I[t-1] + D[t]
        if month == 1:
            wallet = treasury_inflow  # seed: no prior state
        else:
            wallet = wallet + interest_prev + treasury_inflow

        total_credits += credits_minted

        # --- Threshold-based burn decision ---
        credits_burned = 0
        burn_cost = 0.0
        burn_capped = False
        backing_pre = wallet / total_credits if total_credits > 0 else 1.0

        cooldown_ok = (month - last_burn_month) >= BURN_MIN_COOLDOWN
        eligible = month >= BURN_FIRST_ELIGIBLE

        if eligible and cooldown_ok and backing_pre >= BURN_TRIGGER_RATIO:
            requested = int(total_credits * BURN_PCT)
            requested = min(requested, total_credits)

            # Affordability cap: post-burn backing must stay >= BURN_FLOOR_RATIO.
            # Derivation:
            #   (wallet - burned × burn_cost) / (total - burned) >= floor
            #   => burned <= (wallet - floor × total) / (burn_cost_per_credit - floor)
            max_affordable = int(
                (wallet - BURN_FLOOR_RATIO * total_credits)
                / (BURN_COST_PER_CREDIT - BURN_FLOOR_RATIO)
            )
            credits_burned = min(requested, max(0, max_affordable))
            burn_capped = credits_burned < requested

            if credits_burned > 0:
                burn_cost = credits_burned * BURN_COST_PER_CREDIT
                wallet -= burn_cost
                total_credits -= credits_burned
                last_burn_month = month

        # --- Interest on updated wallet (carries to next period) ---
        interest_prev = wallet * MONTHLY_INTEREST_RATE

        # --- Accumulate totals ---
        cumulative_admin_revenue += admin_fee_period
        cumulative_credits_minted += credits_minted
        cumulative_credits_burned += credits_burned
        cumulative_burn_cost += burn_cost

        # --- Primary metric: face-value backing ratio ---
        backing_ratio = wallet / total_credits if total_credits > 0 else 1.0

        # --- Secondary: full burn-out coverage ---
        burn_coverage = (
            wallet / (total_credits * BURN_COST_PER_CREDIT)
            if total_credits > 0
            else 1.0
        )

        # --- Admin revenue vs. outstanding credit face value ---
        admin_vs_credits_ratio = (
            cumulative_admin_revenue / (total_credits * CREDIT_PRICE)
            if total_credits > 0
            else 0.0
        )

        records.append(
            {
                "month": month,
                "employees": employees,
                "credits_minted": credits_minted,
                "credits_burned": credits_burned,
                "burn_capped": burn_capped,
                "burn_cost": burn_cost,
                "backing_pre_burn": backing_pre,
                "total_credits": total_credits,
                "treasury_inflow": treasury_inflow,
                "wallet": wallet,
                "interest_earned": interest_prev,
                "backing_ratio": backing_ratio,
                "burn_coverage": burn_coverage,
                "admin_fee_period": admin_fee_period,
                "cumulative_admin_revenue": cumulative_admin_revenue,
                "cumulative_credits_minted": cumulative_credits_minted,
                "cumulative_credits_burned": cumulative_credits_burned,
                "cumulative_burn_cost": cumulative_burn_cost,
                "admin_vs_credits_ratio": admin_vs_credits_ratio,
            }
        )

        if wallet < 0:
            failure_reason = (
                f"Treasury went negative at month {month} "
                f"(wallet: ${wallet:,.0f}, burn_cost: ${burn_cost:,.0f})"
            )
            break

    return records, failure_reason


def evaluate(records: list[dict], failure_reason: str | None) -> dict:
    if not records:
        return {"verdict": "FAILURE", "failure_reason": "No records produced"}

    last = records[-1]
    primary = last["backing_ratio"]
    min_backing = min(r["backing_ratio"] for r in records)
    min_backing_month = next(
        r["month"] for r in records if r["backing_ratio"] == min_backing
    )
    burn_records = [r for r in records if r["credits_burned"] > 0]

    verdict = "HEALTHY"
    reasons = []

    if failure_reason:
        reasons.append(failure_reason)
        verdict = "FAILURE"

    if min_backing < FAILURE_THRESHOLD:
        reasons.append(
            f"Min backing ratio {min_backing:.3f} at month {min_backing_month} "
            f"< {FAILURE_THRESHOLD} failure threshold"
        )
        verdict = "FAILURE"
    elif min_backing < WARNING_THRESHOLD and verdict != "FAILURE":
        reasons.append(
            f"Min backing ratio {min_backing:.3f} at month {min_backing_month} "
            f"< {WARNING_THRESHOLD} warning threshold"
        )
        verdict = "WARNING"

    return {
        "primary_metric": round(primary, 4),
        "backing_ratio_final": round(last["backing_ratio"], 4),
        "backing_ratio_min": round(min_backing, 4),
        "backing_ratio_min_month": min_backing_month,
        "burn_coverage_final": round(last["burn_coverage"], 4),
        "wallet_final": round(last["wallet"], 2),
        "total_credits_final": last["total_credits"],
        "cumulative_admin_revenue": round(last["cumulative_admin_revenue"], 2),
        "cumulative_burn_cost": round(last["cumulative_burn_cost"], 2),
        "burn_events_fired": len(burn_records),
        "credits_burned_pct": round(
            last["cumulative_credits_burned"] / last["cumulative_credits_minted"] * 100,
            2,
        )
        if last["cumulative_credits_minted"] > 0
        else 0,
        "months_simulated": len(records),
        "verdict": verdict,
        "failure_reason": "; ".join(reasons) if reasons else "NONE",
    }


if __name__ == "__main__":
    print(f"Simulation — {SCENARIO_NAME}")
    print(
        f"  Employees:         {INITIAL_EMPLOYEES:,} start, +{EMPLOYEE_GROWTH_PER_MONTH:,}/month"
    )
    print(
        f"  Credits/employee:  {CREDITS_PER_EMPLOYEE:,}/month (cap: {MAX_CREDITS_PER_EMPLOYEE:,})"
    )
    print(f"  Duration:          {SIMULATION_MONTHS} months")
    print(
        f"  Burn trigger:      backing >= {BURN_TRIGGER_RATIO:.3f} ({BURN_TRIGGER_RATIO * 100:.1f}%)"
    )
    print(f"  Burn size:         {BURN_PCT * 100:.1f}% of outstanding credits")
    print(f"  Burn floor:        {BURN_FLOOR_RATIO:.0%} (affordability cap)")
    print(
        f"  Burn cooldown:     {BURN_MIN_COOLDOWN} months  |  first eligible: month {BURN_FIRST_ELIGIBLE}"
    )
    print("---")

    records, failure_reason = run_simulation()
    results = evaluate(records, failure_reason)

    for key, val in results.items():
        if isinstance(val, float):
            print(f"{key}: {val:.4f}")
        else:
            print(f"{key}: {val}")

    print("---")
    last = records[-1]
    print(f"\nFinal state (month {last['month']}):")
    print(f"  Employees:              {last['employees']:>16,}")
    print(f"  Total credits out:      {last['total_credits']:>16,}")
    print(f"  Treasury wallet:       ${last['wallet']:>16,.2f}")
    print(f"  Backing ratio:          {last['backing_ratio']:>15.2%}")
    print(f"  Burn coverage:          {last['burn_coverage']:>15.2%}")
    print(f"  Cumul. admin revenue:  ${last['cumulative_admin_revenue']:>16,.2f}")
    print(f"  Cumul. burn cost:      ${last['cumulative_burn_cost']:>16,.2f}")
    print(
        f"  Credits burned:         {last['cumulative_credits_burned']:>16,}  "
        f"({results['credits_burned_pct']:.1f}% of all minted)"
    )
    print(f"  Burn events fired:      {results['burn_events_fired']:>16}")
    print(f"  Interest this month:   ${last['interest_earned']:>16,.2f}")

    # Burn event log
    burn_records = [r for r in records if r["credits_burned"] > 0]
    if burn_records:
        print(f"\nBurn event log:")
        print(
            f"  {'Month':>6} {'Backing Pre':>12} {'Credits Burned':>16} "
            f"{'Burn Cost':>14} {'Backing Post':>13} {'Capped?':>8}"
        )
        print(f"  {'─' * 6} {'─' * 12} {'─' * 16} {'─' * 14} {'─' * 13} {'─' * 8}")
        for r in burn_records:
            print(
                f"  {r['month']:>6} {r['backing_pre_burn']:>11.1%} "
                f"{r['credits_burned']:>16,} ${r['burn_cost']:>13,.0f} "
                f"{r['backing_ratio']:>12.1%} {'YES' if r['burn_capped'] else 'no':>8}"
            )
    else:
        print(
            "\n  No burns fired. Trigger threshold not reached within simulation window."
        )

    # Month-by-month sample: first 3, burn months, last 3
    burn_months = {r["month"] for r in burn_records}
    highlight = (
        {r["month"] for r in records[:3]}
        | burn_months
        | {r["month"] for r in records[-3:]}
    )
    sample = [r for r in records if r["month"] in highlight]

    print(
        f"\n{'Mo':>4} {'Employees':>10} {'Minted':>12} {'Burned':>12} "
        f"{'Total Cred':>14} {'Wallet':>16} {'Backing':>8} {'Admin Rev':>12}"
    )
    print("-" * 96)
    prev = 0
    for r in sample:
        if r["month"] > prev + 1 and prev != 0:
            print("  ...")
        print(
            f"{r['month']:>4} {r['employees']:>10,} {r['credits_minted']:>12,} "
            f"{r['credits_burned']:>12,} {r['total_credits']:>14,} "
            f"${r['wallet']:>15,.0f} {r['backing_ratio']:>7.1%} "
            f"${r['admin_fee_period']:>11,.0f}"
        )
        prev = r["month"]
