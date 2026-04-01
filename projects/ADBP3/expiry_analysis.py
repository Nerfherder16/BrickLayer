"""
expiry_analysis.py — ADBP v3 Credit Expiry & Velocity Analysis

Three ways credits leave the system:
  1. Burns       — discretionary, costs $2.00/credit (existing mechanism)
  2. Expiry      — cohort-based, $0 cost (CARD Act / loyalty program precedent)
  3. Breakage    — inactivity drain, $0 cost (~5-7% annual at 12× velocity)

Research baselines:
  - Gift cards (CARD Act): 5-yr minimum, 2-15% annual breakage
  - Closed-loop corporate:  24-36 month window, 5-12% breakage
  - Loyalty programs:       12-24 month inactivity trigger
  - Commuter FSA:           monthly rolling, <1% breakage (12× velocity)
  - ADBP (12× velocity):    recommended 5-7% annual breakage

At 12× annual velocity (1× per month), each credit changes hands monthly.
Active credits reset their inactivity clock; dormant credits accumulate toward expiry.
Higher velocity → lower breakage (fewer dormant credits).

Usage:
    python expiry_analysis.py
    python expiry_analysis.py --months 240 --expiry 24 36 60 --breakage 0.03 0.05 0.07
"""

import argparse
import io
import sys

from constants import (
    BURN_COST_PER_CREDIT,
    CREDIT_PRICE,
    FAILURE_THRESHOLD,
    MONTHLY_INTEREST_RATE,
    WARNING_THRESHOLD,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# FIXED SIMULATION PARAMETERS
# =============================================================================

INITIAL_EMPLOYEES = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE = 2_000
MAX_CREDITS_PER_EMPLOYEE = 5_000

# MC-optimal burn strategy (confirmed, 120-month horizon)
BURN_TRIGGER_RATIO = 1.146
BURN_PCT = 0.302
BURN_MIN_COOLDOWN = 8
BURN_FIRST_ELIGIBLE = 13

# Velocity research baseline
ANNUAL_VELOCITY = 12  # credits recirculate 12x per year (once per month avg)

# Breakage: % of outstanding credits that go permanently unused each year
# Research-derived for 12x velocity programs:
#   Low:    3% (high-engagement, commuter-FSA-like)
#   Medium: 6% (closed-loop corporate, recommended ADBP estimate)
#   High:   10% (single-merchant, lower engagement)
BREAKAGE_ANNUAL_VELOCITY_ADJUSTED = {
    12: 0.06,   # 12x velocity -> ~6% (ADBP baseline)
    6:  0.08,   # 6x velocity  -> ~8% (network contraction)
    3:  0.11,   # 3x velocity  -> ~11% (low engagement)
    1:  0.14,   # 1x velocity  -> ~14% (single-merchant range)
}


# =============================================================================
# SIMULATION WITH EXPIRY AND BREAKAGE
# =============================================================================


def simulate_with_expiry(
    months: int,
    expiry_window: int | None,    # None = no expiry; otherwise months before cohort expires
    annual_breakage_rate: float,  # fraction of outstanding credits that expire per year
    burn_enabled: bool = True,
    burn_trigger: float = BURN_TRIGGER_RATIO,
    burn_pct: float = BURN_PCT,
    burn_cooldown: int = BURN_MIN_COOLDOWN,
    burn_first_eligible: int = BURN_FIRST_ELIGIBLE,
) -> dict:
    """
    Cohort-based simulation tracking credit issuance by month.

    Expiry model:
        Credits issued at month T expire at month T + expiry_window.
        Expiry removes credits from outstanding supply at $0 cost to treasury.

    Breakage model:
        Each month, monthly_breakage_rate * total_credits expire from inactivity.
        Applied after new minting, before burn check.
        Represents credits held dormant (never used) by inactive participants.

    Velocity adjustment:
        At 12x/year velocity, active credits reset their inactivity clock monthly.
        Dormant credits (held without use) accumulate toward expiry.
        High velocity -> lower effective breakage.
    """
    monthly_breakage_rate = annual_breakage_rate / 12

    # Cohort tracking: list of [credits_remaining] indexed by issuance month (1-based)
    # cohorts[t-1] = credits still outstanding from month t's issuance
    cohorts = [0] * (months + 1)

    wallet = 0.0
    total_credits = 0
    interest_prev = 0.0
    last_burn_month = 0

    cumulative_minted = 0
    cumulative_burned = 0
    cumulative_expired_cohort = 0
    cumulative_expired_breakage = 0
    burn_events = []

    records = []

    for month in range(1, months + 1):
        employees = INITIAL_EMPLOYEES + (month - 1) * EMPLOYEE_GROWTH_PER_MONTH
        credits_minted = employees * min(CREDITS_PER_EMPLOYEE, MAX_CREDITS_PER_EMPLOYEE)
        treasury_inflow = credits_minted * CREDIT_PRICE

        # --- Treasury: add prior interest + new inflow ---
        if month == 1:
            wallet = treasury_inflow
        else:
            wallet = wallet + interest_prev + treasury_inflow

        # --- Mint new credits ---
        total_credits += credits_minted
        cohorts[month - 1] = credits_minted  # 0-indexed cohort
        cumulative_minted += credits_minted

        # --- Cohort expiry (CARD Act / closed-loop window) ---
        expired_cohort = 0
        if expiry_window is not None:
            expiring_cohort_month = month - expiry_window
            if 1 <= expiring_cohort_month <= months:
                idx = expiring_cohort_month - 1
                expired_cohort = cohorts[idx]
                cohorts[idx] = 0
                total_credits -= expired_cohort
                cumulative_expired_cohort += expired_cohort

        # --- Breakage (inactivity drain — % of outstanding) ---
        expired_breakage = 0
        if monthly_breakage_rate > 0 and total_credits > 0:
            expired_breakage = int(total_credits * monthly_breakage_rate)
            # Distribute breakage proportionally across all cohorts
            if total_credits > 0:
                ratio = expired_breakage / total_credits
                for i in range(len(cohorts)):
                    reduction = int(cohorts[i] * ratio)
                    cohorts[i] = max(0, cohorts[i] - reduction)
            total_credits -= expired_breakage
            cumulative_expired_breakage += expired_breakage

        # --- Interest on updated wallet ---
        interest_prev = wallet * MONTHLY_INTEREST_RATE

        # --- Burn decision (threshold-triggered, affordability-capped) ---
        credits_burned = 0
        burn_cost = 0.0
        if burn_enabled and total_credits > 0:
            backing_pre = wallet / total_credits
            cooldown_ok = (month - last_burn_month) >= burn_cooldown
            eligible = month >= burn_first_eligible

            if eligible and cooldown_ok and backing_pre >= burn_trigger:
                credits_burned = int(total_credits * burn_pct)
                credits_burned = min(credits_burned, total_credits)

                max_affordable = int(
                    (wallet - FAILURE_THRESHOLD * total_credits)
                    / (BURN_COST_PER_CREDIT - FAILURE_THRESHOLD)
                )
                credits_burned = min(credits_burned, max(0, max_affordable))
                burn_cost = credits_burned * BURN_COST_PER_CREDIT

                if credits_burned > 0:
                    wallet -= burn_cost
                    total_credits -= credits_burned
                    cumulative_burned += credits_burned
                    last_burn_month = month
                    burn_events.append(month)
                    # Distribute burn proportionally across cohorts
                    if total_credits + credits_burned > 0:
                        ratio = credits_burned / (total_credits + credits_burned)
                        for i in range(len(cohorts)):
                            reduction = int(cohorts[i] * ratio)
                            cohorts[i] = max(0, cohorts[i] - reduction)

        backing = wallet / total_credits if total_credits > 0 else 1.0

        records.append({
            "month": month,
            "employees": employees,
            "credits_minted": credits_minted,
            "expired_cohort": expired_cohort,
            "expired_breakage": expired_breakage,
            "credits_burned": credits_burned,
            "total_credits": total_credits,
            "wallet": wallet,
            "backing": backing,
        })

    if not records:
        return {"verdict": "FAILURE"}

    backings = [r["backing"] for r in records]
    min_backing = min(backings)
    final_backing = backings[-1]

    verdict = (
        "FAILURE" if min_backing < FAILURE_THRESHOLD
        else "WARNING" if min_backing < WARNING_THRESHOLD
        else "HEALTHY"
    )

    total_ever_minted = cumulative_minted
    total_liability_eliminated = cumulative_burned + cumulative_expired_cohort + cumulative_expired_breakage

    return {
        "verdict": verdict,
        "min_backing": min_backing,
        "final_backing": final_backing,
        "wallet": records[-1]["wallet"],
        "total_credits": records[-1]["total_credits"],
        "cumulative_minted": total_ever_minted,
        "cumulative_burned": cumulative_burned,
        "cumulative_expired_cohort": cumulative_expired_cohort,
        "cumulative_expired_breakage": cumulative_expired_breakage,
        "total_eliminated": total_liability_eliminated,
        "pct_eliminated": total_liability_eliminated / total_ever_minted if total_ever_minted > 0 else 0,
        "burn_events": len(burn_events),
        "burn_months": burn_events,
        "records": records,
    }


# =============================================================================
# SCENARIO RUNNER
# =============================================================================


def run_scenario_table(months: int, expiry_windows: list, breakage_rates: list) -> None:
    print(f"\n{'=' * 100}")
    print(f"EXPIRY & BREAKAGE SCENARIO MATRIX — {months} months")
    print(f"{'=' * 100}")
    print(
        f"  {'Expiry Window':>15} {'Annual Breakage':>16} "
        f"{'Min Backing':>12} {'Final Backing':>14} "
        f"{'Burns':>6} {'%Burned':>8} "
        f"{'%Cohort Exp':>12} {'%Breakage':>10} "
        f"{'%Total Elim':>12} {'Verdict':>10}"
    )
    print(f"  {'-' * 15} {'-' * 16} {'-' * 12} {'-' * 14} {'-' * 6} {'-' * 8} {'-' * 12} {'-' * 10} {'-' * 12} {'-' * 10}")

    # Reference: no expiry, no breakage, burns only
    ref = simulate_with_expiry(months, None, 0.0)
    print(
        f"  {'[REFERENCE]':>15} {'none':>16} "
        f"{ref['min_backing']:>11.1%} {ref['final_backing']:>13.1%} "
        f"{ref['burn_events']:>6} "
        f"{ref['cumulative_burned'] / ref['cumulative_minted']:>7.1%} "
        f"{'n/a':>12} {'n/a':>10} "
        f"{ref['pct_eliminated']:>11.1%} {ref['verdict']:>10}"
    )

    # Reference: no expiry, no breakage, NO burns either
    ref_noburn = simulate_with_expiry(months, None, 0.0, burn_enabled=False)
    print(
        f"  {'[NO BURNS]':>15} {'none':>16} "
        f"{ref_noburn['min_backing']:>11.1%} {ref_noburn['final_backing']:>13.1%} "
        f"{'0':>6} {'0.0%':>8} {'n/a':>12} {'n/a':>10} "
        f"{'0.0%':>12} {ref_noburn['verdict']:>10}"
    )

    print()
    for expiry in expiry_windows:
        for breakage in breakage_rates:
            r = simulate_with_expiry(months, expiry, breakage)
            pct_burned = r["cumulative_burned"] / r["cumulative_minted"]
            pct_cohort = r["cumulative_expired_cohort"] / r["cumulative_minted"]
            pct_break = r["cumulative_expired_breakage"] / r["cumulative_minted"]
            label = f"{expiry}mo window"
            print(
                f"  {label:>15} {breakage:>15.0%} "
                f"{r['min_backing']:>11.1%} {r['final_backing']:>13.1%} "
                f"{r['burn_events']:>6} {pct_burned:>7.1%} "
                f"{pct_cohort:>11.1%} {pct_break:>9.1%} "
                f"{r['pct_eliminated']:>11.1%} {r['verdict']:>10}"
            )
        print()

    # No-burn scenarios: expiry + breakage alone, no active burns
    print(f"\n{'─' * 100}")
    print("NO-BURN SCENARIOS: expiry + breakage only (burns disabled)")
    print(f"{'─' * 100}")
    print(
        f"  {'Expiry Window':>15} {'Annual Breakage':>16} "
        f"{'Min Backing':>12} {'Final Backing':>14} "
        f"{'%Cohort Exp':>12} {'%Breakage':>10} "
        f"{'%Total Elim':>12} {'Verdict':>10}"
    )
    print(f"  {'-' * 15} {'-' * 16} {'-' * 12} {'-' * 14} {'-' * 12} {'-' * 10} {'-' * 12} {'-' * 10}")
    for expiry in expiry_windows:
        for breakage in breakage_rates:
            r = simulate_with_expiry(months, expiry, breakage, burn_enabled=False)
            pct_cohort = r["cumulative_expired_cohort"] / r["cumulative_minted"]
            pct_break = r["cumulative_expired_breakage"] / r["cumulative_minted"]
            label = f"{expiry}mo window"
            print(
                f"  {label:>15} {breakage:>15.0%} "
                f"{r['min_backing']:>11.1%} {r['final_backing']:>13.1%} "
                f"{pct_cohort:>11.1%} {pct_break:>9.1%} "
                f"{r['pct_eliminated']:>11.1%} {r['verdict']:>10}"
            )
        print()


def print_monthly_trace(result: dict, label: str, show_months: list | None = None) -> None:
    """Print month-by-month detail for key months."""
    print(f"\n{'─' * 90}")
    print(f"MONTHLY TRACE: {label}")
    print(f"{'─' * 90}")
    print(
        f"  {'Mo':>4} {'Employees':>10} {'Minted':>12} {'Cohort Exp':>11} "
        f"{'Breakage':>9} {'Burned':>9} {'Total Credits':>14} {'Wallet':>14} "
        f"{'Backing':>9}"
    )
    print(f"  {'-' * 4} {'-' * 10} {'-' * 12} {'-' * 11} {'-' * 9} {'-' * 9} {'-' * 14} {'-' * 14} {'-' * 9}")

    milestones = show_months or list(range(1, 25)) + list(range(24, result["records"][-1]["month"] + 1, 12))
    shown = set()
    for r in result["records"]:
        m = r["month"]
        if m in milestones and m not in shown:
            shown.add(m)
            flag = " <BURN" if r["credits_burned"] > 0 else ""
            exp_flag = " <EXPIRE" if r["expired_cohort"] > 0 else ""
            print(
                f"  {m:>4} {r['employees']:>10,} {r['credits_minted']:>12,} "
                f"{r['expired_cohort']:>11,} {r['expired_breakage']:>9,} "
                f"{r['credits_burned']:>9,} {r['total_credits']:>14,} "
                f"${r['wallet']:>13,.0f} {r['backing']:>8.1%}"
                f"{flag}{exp_flag}"
            )


def run_velocity_breakage_analysis(months: int) -> None:
    """Show how velocity affects breakage and treasury outcomes."""
    print(f"\n{'=' * 80}")
    print(f"VELOCITY vs BREAKAGE IMPACT — {months} months, 36mo expiry window")
    print(f"{'=' * 80}")
    print(
        f"  {'Velocity':>10} {'Annual Breakage':>16} {'Min Backing':>12} "
        f"{'Final Backing':>14} {'Burns':>6} {'%Elim':>8} {'Verdict':>10}"
    )
    print(f"  {'-' * 10} {'-' * 16} {'-' * 12} {'-' * 14} {'-' * 6} {'-' * 8} {'-' * 10}")
    for velocity, breakage in sorted(BREAKAGE_ANNUAL_VELOCITY_ADJUSTED.items(), reverse=True):
        r = simulate_with_expiry(months, 36, breakage)
        print(
            f"  {velocity:>9}x {breakage:>15.0%} "
            f"{r['min_backing']:>11.1%} {r['final_backing']:>13.1%} "
            f"{r['burn_events']:>6} {r['pct_eliminated']:>7.1%} {r['verdict']:>10}"
        )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ADBP v3 Expiry & Breakage Analysis"
    )
    parser.add_argument("--months", type=int, default=120)
    parser.add_argument(
        "--expiry",
        type=int,
        nargs="+",
        default=[12, 24, 36, 60],
        help="Expiry window(s) in months to test",
    )
    parser.add_argument(
        "--breakage",
        type=float,
        nargs="+",
        default=[0.03, 0.06, 0.10],
        help="Annual breakage rates to test (e.g. 0.06 = 6%%)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print month-by-month traces for key scenarios",
    )
    args = parser.parse_args()

    print("ADBP v3 — Expiry & Velocity Analysis")
    print(f"  Months:          {args.months}")
    print(f"  Expiry windows:  {args.expiry} months")
    print(f"  Breakage rates:  {[f'{r:.0%}' for r in args.breakage]}")
    print(f"  Burn strategy:   trigger={BURN_TRIGGER_RATIO:.1%}  burn={BURN_PCT:.1%}  "
          f"cooldown={BURN_MIN_COOLDOWN}mo  first={BURN_FIRST_ELIGIBLE}")
    print("  Velocity note:   12x/yr -> ~6% breakage (research baseline)")

    run_scenario_table(args.months, args.expiry, args.breakage)
    run_velocity_breakage_analysis(args.months)

    if args.trace:
        # Detailed traces for representative scenarios
        baseline = simulate_with_expiry(args.months, None, 0.0)
        print_monthly_trace(baseline, "Baseline (burns only, no expiry)")

        recommended = simulate_with_expiry(args.months, 36, 0.06)
        print_monthly_trace(recommended, "Recommended (36mo expiry + 6% breakage + burns)")

        noburn_rec = simulate_with_expiry(args.months, 24, 0.10, burn_enabled=False)
        print_monthly_trace(noburn_rec, "No burns — 24mo expiry + 10% breakage only")

    print(f"\n{'─' * 80}")
    print("KEY INSIGHT: credits eliminated via expiry/breakage cost $0 vs $2.00/credit via burns.")
    print("Expiry is pure breakage revenue (treasury keeps $1, $2 obligation extinguished).")
    print(f"{'─' * 80}")
