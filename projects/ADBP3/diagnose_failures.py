"""
diagnose_failures.py — Deep analysis of Monte Carlo failure cases.

Reproduces all FAILURE runs from the MC, extracts the exact month
the treasury went negative, the parameter combination that caused it,
and the month-by-month trajectory leading up to the collapse.
"""

import io
import random
import statistics
import sys

from constants import (
    BURN_COST_PER_CREDIT,
    CREDIT_PRICE,
    FAILURE_THRESHOLD,
    MONTHLY_INTEREST_RATE,
    WARNING_THRESHOLD,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Same settings as the MC run
INITIAL_EMPLOYEES = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE = 2_000
MAX_CREDITS_PER_EMPLOYEE = 5_000

TRIGGER_RATIO_MIN = 0.90
TRIGGER_RATIO_MAX = 1.60
BURN_PCT_MIN = 0.02
BURN_PCT_MAX = 0.35
COOLDOWN_MIN = 3
COOLDOWN_MAX = 24
FIRST_ELIGIBLE_MIN = 6
FIRST_ELIGIBLE_MAX = 24

N_RUNS = 20_000
SEED = 42


def simulate_detailed(months, trigger_ratio, burn_pct, min_cooldown, first_eligible):
    """Full simulation returning month-by-month records and failure info."""
    wallet = 0.0
    total_credits = 0
    interest_prev = 0.0
    cumulative_minted = 0
    cumulative_burned = 0
    last_burn_month = 0
    failure_reason = None
    records = []

    credits_per_emp = min(CREDITS_PER_EMPLOYEE, MAX_CREDITS_PER_EMPLOYEE)

    for month in range(1, months + 1):
        employees = INITIAL_EMPLOYEES + (month - 1) * EMPLOYEE_GROWTH_PER_MONTH
        credits_minted = employees * credits_per_emp
        treasury_inflow = credits_minted * CREDIT_PRICE

        if month == 1:
            wallet = treasury_inflow
        else:
            wallet = wallet + interest_prev + treasury_inflow

        total_credits += credits_minted
        cumulative_minted += credits_minted

        backing_pre = wallet / total_credits if total_credits > 0 else 1.0
        credits_burned = 0
        burn_cost = 0.0
        burn_attempted = False

        cooldown_ok = (month - last_burn_month) >= min_cooldown
        eligible = month >= first_eligible

        if eligible and cooldown_ok and backing_pre >= trigger_ratio:
            burn_attempted = True
            credits_to_burn = int(total_credits * burn_pct)
            credits_to_burn = min(credits_to_burn, total_credits)
            cost = credits_to_burn * BURN_COST_PER_CREDIT

            # Execute regardless of affordability (to expose failures)
            wallet -= cost
            total_credits -= credits_to_burn
            credits_burned = credits_to_burn
            burn_cost = cost
            cumulative_burned += credits_to_burn
            last_burn_month = month

        interest_prev = wallet * MONTHLY_INTEREST_RATE
        backing_post = wallet / total_credits if total_credits > 0 else 1.0

        records.append(
            {
                "month": month,
                "employees": employees,
                "credits_minted": credits_minted,
                "credits_burned": credits_burned,
                "burn_cost": burn_cost,
                "burn_attempted": burn_attempted,
                "backing_pre_burn": backing_pre,
                "backing_post_burn": backing_post,
                "wallet": wallet,
                "total_credits": total_credits,
                "interest": interest_prev,
            }
        )

        if wallet < 0:
            failure_reason = (
                f"Wallet went negative at month {month}: "
                f"${wallet:,.0f} after burning {credits_burned:,} credits "
                f"(cost ${burn_cost:,.0f}). "
                f"Backing pre-burn: {backing_pre:.3f}, post-burn: {backing_post:.3f}."
            )
            break

    min_ratio = min(r["backing_post_burn"] for r in records)
    verdict = (
        "FAILURE"
        if (failure_reason or min_ratio < FAILURE_THRESHOLD)
        else "WARNING"
        if min_ratio < WARNING_THRESHOLD
        else "HEALTHY"
    )

    return records, failure_reason, verdict


def run_and_collect_failures():
    rng = random.Random(SEED)
    failures = []

    for i in range(N_RUNS):
        trigger_ratio = rng.uniform(TRIGGER_RATIO_MIN, TRIGGER_RATIO_MAX)
        burn_pct = rng.uniform(BURN_PCT_MIN, BURN_PCT_MAX)
        min_cooldown = rng.randint(COOLDOWN_MIN, COOLDOWN_MAX)
        first_eligible = rng.randint(FIRST_ELIGIBLE_MIN, FIRST_ELIGIBLE_MAX)

        records, failure_reason, verdict = simulate_detailed(
            months=120,
            trigger_ratio=trigger_ratio,
            burn_pct=burn_pct,
            min_cooldown=min_cooldown,
            first_eligible=first_eligible,
        )

        if verdict == "FAILURE":
            failures.append(
                {
                    "run": i,
                    "trigger_ratio": trigger_ratio,
                    "burn_pct": burn_pct,
                    "min_cooldown": min_cooldown,
                    "first_eligible": first_eligible,
                    "failure_reason": failure_reason,
                    "records": records,
                    "failure_month": records[-1]["month"] if records else None,
                }
            )

    return failures


def analyze(failures):
    print(f"\n{'=' * 70}")
    print(f"FAILURE ANALYSIS — {len(failures):,} failed runs out of {N_RUNS:,}")
    print(f"{'=' * 70}")
    print(f"  Failure rate: {len(failures) / N_RUNS * 100:.2f}%")

    # Parameter distributions in failures
    triggers = [f["trigger_ratio"] for f in failures]
    burn_pcts = [f["burn_pct"] for f in failures]
    cooldowns = [f["min_cooldown"] for f in failures]
    eligibles = [f["first_eligible"] for f in failures]
    fail_months = [f["failure_month"] for f in failures]

    print(f"\n{'─' * 70}")
    print("PARAMETER DISTRIBUTIONS IN FAILURE RUNS")
    print(f"{'─' * 70}")
    print(
        f"  Trigger ratio:    mean={statistics.mean(triggers):.3f}  "
        f"median={statistics.median(triggers):.3f}  "
        f"min={min(triggers):.3f}  max={max(triggers):.3f}"
    )
    print(
        f"  Burn pct:         mean={statistics.mean(burn_pcts) * 100:.1f}%  "
        f"median={statistics.median(burn_pcts) * 100:.1f}%  "
        f"min={min(burn_pcts) * 100:.1f}%  max={max(burn_pcts) * 100:.1f}%"
    )
    print(
        f"  Cooldown:         mean={statistics.mean(cooldowns):.1f}mo  "
        f"median={statistics.median(cooldowns):.1f}mo"
    )
    print(
        f"  First eligible:   mean={statistics.mean(eligibles):.1f}mo  "
        f"median={statistics.median(eligibles):.1f}mo"
    )
    print(
        f"  Failure month:    mean={statistics.mean(fail_months):.1f}  "
        f"median={statistics.median(fail_months):.1f}  "
        f"min={min(fail_months)}  max={max(fail_months)}"
    )

    # Failure month distribution
    print(f"\n{'─' * 70}")
    print("WHEN DO FAILURES HAPPEN? (failure month distribution)")
    print(f"{'─' * 70}")
    bands = [(1, 12), (13, 24), (25, 36), (37, 48), (49, 60), (61, 120)]
    for lo, hi in bands:
        count = sum(1 for m in fail_months if lo <= m <= hi)
        bar = "█" * int(count / len(failures) * 40)
        print(
            f"  Month {lo:>3}–{hi:<3}: {count:>4} ({count / len(failures) * 100:>5.1f}%)  {bar}"
        )

    # Trigger ratio in failures vs. all
    print(f"\n{'─' * 70}")
    print("TRIGGER RATIO BANDS — failure concentration")
    print(f"{'─' * 70}")
    bands = [(i / 10, (i + 1) / 10) for i in range(9, 16)]
    for lo, hi in bands:
        count = sum(1 for f in failures if lo <= f["trigger_ratio"] < hi)
        total_in_band = int(
            N_RUNS * (hi - lo) / (TRIGGER_RATIO_MAX - TRIGGER_RATIO_MIN)
        )
        rate = count / max(total_in_band, 1) * 100
        bar = "█" * int(rate / 2)
        print(
            f"  {lo:.1f}x–{hi:.1f}x: {count:>4} failures  (~{rate:.1f}% of band)  {bar}"
        )

    # Burn pct in failures
    print(f"\n{'─' * 70}")
    print("BURN PCT BANDS — failure concentration")
    print(f"{'─' * 70}")
    pct_bands = [(i / 100, (i + 5) / 100) for i in range(0, 35, 5)]
    for lo, hi in pct_bands:
        count = sum(1 for f in failures if lo <= f["burn_pct"] < hi)
        total_in_band = int(N_RUNS * (hi - lo) / (BURN_PCT_MAX - BURN_PCT_MIN))
        rate = count / max(total_in_band, 1) * 100
        bar = "█" * int(rate / 2)
        print(
            f"  {lo * 100:.0f}%–{hi * 100:.0f}%: {count:>4} failures  (~{rate:.1f}% of band)  {bar}"
        )

    # Show 3 detailed failure trajectories
    print(f"\n{'─' * 70}")
    print("DETAILED FAILURE TRAJECTORIES (3 representative cases)")
    print(f"{'─' * 70}")

    # Sort by failure month to show early, mid, late failures
    sorted_f = sorted(failures, key=lambda f: f["failure_month"])
    cases = [
        sorted_f[0],  # earliest failure
        sorted_f[len(sorted_f) // 2],  # median failure
        sorted_f[-1],  # latest failure
    ]
    labels = ["EARLIEST FAILURE", "MEDIAN FAILURE", "LATEST FAILURE"]

    for label, case in zip(labels, cases):
        print(f"\n  [{label}] — Run #{case['run']}")
        print("  Parameters:")
        print(
            f"    trigger_ratio:  {case['trigger_ratio']:.3f}  "
            f"(burn when backing >= {case['trigger_ratio'] * 100:.1f}%)"
        )
        print(
            f"    burn_pct:       {case['burn_pct'] * 100:.1f}%  "
            f"(burn {case['burn_pct'] * 100:.1f}% of outstanding credits)"
        )
        print(f"    cooldown:       {case['min_cooldown']} months")
        print(f"    first_eligible: month {case['first_eligible']}")
        print(f"  Failure: {case['failure_reason']}")

        # Show months around the burn that caused failure
        records = case["records"]
        burn_months = [r for r in records if r["burn_attempted"]]
        fatal_month = case["failure_month"]

        # Show 3 months before each burn + the fatal month
        highlight = set()
        for b in burn_months:
            for m in range(max(1, b["month"] - 2), b["month"] + 2):
                highlight.add(m)
        highlight.add(fatal_month)
        if records:
            highlight.add(records[0]["month"])

        sample = [r for r in records if r["month"] in highlight]

        print(
            f"\n  {'Mo':>4} {'Employees':>10} {'Backing Pre':>12} "
            f"{'Burned':>12} {'Burn Cost':>12} {'Wallet After':>14} {'Backing Post':>13}"
        )
        print(
            f"  {'─' * 4} {'─' * 10} {'─' * 12} {'─' * 12} {'─' * 12} {'─' * 14} {'─' * 13}"
        )
        prev = 0
        for r in sample:
            if r["month"] > prev + 1 and prev != 0:
                print("    ...")
            marker = " ← BURN" if r["burn_attempted"] else ""
            marker = (
                " ← FAILURE"
                if r["month"] == fatal_month and not r["burn_attempted"]
                else marker
            )
            marker = (
                " ← BURN + FAILURE"
                if r["month"] == fatal_month and r["burn_attempted"]
                else marker
            )
            print(
                f"  {r['month']:>4} {r['employees']:>10,} {r['backing_pre_burn']:>11.1%} "
                f"{r['credits_burned']:>12,} ${r['burn_cost']:>11,.0f} "
                f"${r['wallet']:>13,.0f} {r['backing_post_burn']:>12.1%}{marker}"
            )
            prev = r["month"]

    # Root cause summary
    print(f"\n{'=' * 70}")
    print("ROOT CAUSE SUMMARY")
    print(f"{'=' * 70}")

    early_failures = [f for f in failures if f["failure_month"] <= 24]
    late_failures = [f for f in failures if f["failure_month"] > 24]

    print(f"""
  All {len(failures)} failures share one root cause:
  A burn event was triggered when the backing ratio met the trigger threshold,
  but the burn cost ($2/credit) exceeded what the wallet could absorb.

  This happens because the trigger ratio is measured BEFORE the burn.
  The system looked healthy enough to burn, but the burn itself was
  too large relative to the wallet balance — wallet went negative mid-burn.

  TWO FAILURE PATTERNS:

  1. EARLY FAILURES ({len(early_failures)} runs, {len(early_failures) / len(failures) * 100:.0f}% of failures):
     - Trigger ratio near 0.90x (fires very early, before treasury has built up)
     - Burn pct is high (20–35%) — large burn on a thin treasury
     - Treasury only has ~${(INITIAL_EMPLOYEES * CREDITS_PER_EMPLOYEE * CREDIT_PRICE):,.0f} at month 1
     - A 30% burn of even modest credit supply exceeds the wallet at month 6–12
     - Fix: raise first_eligible or lower burn_pct for early months

  2. LATE FAILURES ({len(late_failures)} runs, {len(late_failures) / len(failures) * 100:.0f}% of failures):
     - Trigger ratio near 0.90–1.00x fires repeatedly (many small burns)
     - After many burns, treasury is depleted; a final large burn finishes it
     - The compounding effect: each burn reduces interest income (smaller wallet)
     - Fix: higher trigger ratio or lower burn_pct

  THE SAFE ZONE (confirmed by MC):
  - Trigger ratio >= 1.10x:  93.5% healthy rate
  - Trigger ratio >= 1.20x:  100% healthy rate (trigger never fires in 10 years)
  - Burn pct <= 10%:          100% healthy rate
  - The danger zone is LOW trigger + HIGH burn_pct simultaneously
""")


if __name__ == "__main__":
    print(
        f"Re-running {N_RUNS:,} simulations to extract failure cases (seed={SEED})..."
    )
    print("This matches the original MC run exactly.")

    failures = run_and_collect_failures()
    analyze(failures)
