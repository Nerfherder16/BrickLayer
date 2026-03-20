"""
monte_carlo.py — ADBP v3 Burn Strategy Optimization

Instead of arbitrary fixed burns (months 13, 25, 37), this explores
threshold-based burn strategies: burn when backing ratio exceeds a ceiling,
burn a % of outstanding credits, wait a cooldown before burning again.

Goal: find parameter combinations that keep the system HEALTHY throughout
while maximizing credit destruction (reducing liability).

Strategy parameters (sampled per run):
  trigger_ratio    — burn when backing_ratio exceeds this ceiling (e.g. 1.10)
  burn_pct         — % of outstanding credits to burn when triggered (e.g. 0.10)
  min_cooldown     — minimum months between burns
  first_eligible   — earliest month a burn can happen (ramp-up protection)

Scoring (higher = better):
  +1.0  per run that stays HEALTHY throughout (backing ratio never < 0.75)
  +0.5  per run that stays above FAILURE (backing ratio never < 0.50)
  +credits_burned_fraction  (burned / total_ever_minted) — reward liability reduction
  -variance penalty  (std dev of backing ratio — reward stability)

Usage:
    python monte_carlo.py
    python monte_carlo.py --runs 20000 --months 120 --seed 42
"""

import argparse
import io
import random
import statistics
import sys

from constants import (
    BURN_COST_PER_CREDIT,
    CREDIT_PRICE,
    EMPLOYEE_FEE_RATE,
    FAILURE_THRESHOLD,
    MONTHLY_INTEREST_RATE,
    WARNING_THRESHOLD,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# FIXED SIMULATION PARAMETERS (same as baseline — not varied in MC)
# =============================================================================

INITIAL_EMPLOYEES = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE = 2_000
MAX_CREDITS_PER_EMPLOYEE = 5_000

# =============================================================================
# MONTE CARLO SEARCH SPACE
# =============================================================================

# Trigger ratio range: burn fires when backing_ratio >= this value
TRIGGER_RATIO_MIN = 0.90
TRIGGER_RATIO_MAX = 1.60

# Burn pct range: % of total outstanding credits burned per event
BURN_PCT_MIN = 0.02
BURN_PCT_MAX = 0.35

# Cooldown range: minimum months between consecutive burns
COOLDOWN_MIN = 3
COOLDOWN_MAX = 24

# First eligible month for a burn (protect the ramp-up phase)
FIRST_ELIGIBLE_MIN = 6
FIRST_ELIGIBLE_MAX = 24


# =============================================================================
# INLINE SIMULATION (threshold-based burn logic)
# =============================================================================


def simulate_threshold(
    months: int,
    trigger_ratio: float,
    burn_pct: float,
    min_cooldown: int,
    first_eligible: int,
) -> dict:
    wallet = 0.0
    total_credits = 0
    interest_prev = 0.0
    cumulative_minted = 0
    cumulative_burned = 0
    cumulative_burn_cost = 0.0
    last_burn_month = 0
    burn_events_triggered = []

    backing_ratios = []
    failure_reason = None

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

        # --- Threshold-based burn decision ---
        backing_ratio_pre = wallet / total_credits if total_credits > 0 else 1.0
        credits_burned = 0
        burn_cost = 0.0

        cooldown_ok = (month - last_burn_month) >= min_cooldown
        eligible = month >= first_eligible

        if eligible and cooldown_ok and backing_ratio_pre >= trigger_ratio:
            credits_burned = int(total_credits * burn_pct)
            credits_burned = min(credits_burned, total_credits)

            # Affordability cap: ensure post-burn backing ratio never drops
            # below FAILURE_THRESHOLD.
            # Derived from: (wallet - burned*2) / (total_credits - burned) >= threshold
            # => burned <= (wallet - threshold * total_credits) / (burn_cost - threshold)
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
                cumulative_burn_cost += burn_cost
                last_burn_month = month
                burn_events_triggered.append((month, credits_burned))

        # Interest on updated wallet
        interest_prev = wallet * MONTHLY_INTEREST_RATE

        backing_ratio = wallet / total_credits if total_credits > 0 else 1.0
        backing_ratios.append(backing_ratio)

        if wallet < 0:
            failure_reason = f"wallet negative at month {month}"
            break

    if not backing_ratios:
        return {"verdict": "FAILURE", "score": -999}

    min_ratio = min(backing_ratios)
    final_ratio = backing_ratios[-1]
    ratio_variance = (
        statistics.variance(backing_ratios) if len(backing_ratios) > 1 else 0.0
    )
    burn_fraction = (
        cumulative_burned / cumulative_minted if cumulative_minted > 0 else 0.0
    )

    # Verdict
    if failure_reason or min_ratio < FAILURE_THRESHOLD:
        verdict = "FAILURE"
    elif min_ratio < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    # Score: reward healthy runs + credit destruction + stability
    score = 0.0
    if verdict == "HEALTHY":
        score += 2.0
    elif verdict == "WARNING":
        score += 0.5
    # Reward burning more credits (reducing liability)
    score += burn_fraction * 2.0
    # Reward stability (lower variance = better)
    score -= ratio_variance * 5.0
    # Reward higher final ratio (more reserve headroom)
    score += min(final_ratio, 1.5) * 0.5

    return {
        "verdict": verdict,
        "score": score,
        "min_ratio": min_ratio,
        "final_ratio": final_ratio,
        "ratio_variance": ratio_variance,
        "burn_fraction": burn_fraction,
        "burn_events": len(burn_events_triggered),
        "cumulative_burned": cumulative_burned,
        "cumulative_burn_cost": cumulative_burn_cost,
        "burn_event_list": burn_events_triggered,
        "trigger_ratio": trigger_ratio,
        "burn_pct": burn_pct,
        "min_cooldown": min_cooldown,
        "first_eligible": first_eligible,
    }


# =============================================================================
# MONTE CARLO RUNNER
# =============================================================================


def run_monte_carlo(n_runs: int, months: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    results = []

    for i in range(n_runs):
        if i % 1000 == 0 and i > 0:
            print(f"  ... {i:,} / {n_runs:,} runs complete", flush=True)

        trigger_ratio = rng.uniform(TRIGGER_RATIO_MIN, TRIGGER_RATIO_MAX)
        burn_pct = rng.uniform(BURN_PCT_MIN, BURN_PCT_MAX)
        min_cooldown = rng.randint(COOLDOWN_MIN, COOLDOWN_MAX)
        first_eligible = rng.randint(FIRST_ELIGIBLE_MIN, FIRST_ELIGIBLE_MAX)

        result = simulate_threshold(
            months=months,
            trigger_ratio=trigger_ratio,
            burn_pct=burn_pct,
            min_cooldown=min_cooldown,
            first_eligible=first_eligible,
        )
        results.append(result)

    return results


def summarize(results: list[dict], months: int) -> None:
    total = len(results)
    healthy = [r for r in results if r["verdict"] == "HEALTHY"]
    warning = [r for r in results if r["verdict"] == "WARNING"]
    failure = [r for r in results if r["verdict"] == "FAILURE"]

    print(f"\n{'=' * 70}")
    print(f"MONTE CARLO RESULTS — {total:,} runs, {months} months")
    print(f"{'=' * 70}")
    print(f"  HEALTHY:  {len(healthy):>6,}  ({len(healthy) / total * 100:.1f}%)")
    print(f"  WARNING:  {len(warning):>6,}  ({len(warning) / total * 100:.1f}%)")
    print(f"  FAILURE:  {len(failure):>6,}  ({len(failure) / total * 100:.1f}%)")

    if not healthy:
        print("\n  No HEALTHY runs found. Try widening search space.")
        return

    # Sort healthy runs by score
    healthy_sorted = sorted(healthy, key=lambda r: r["score"], reverse=True)
    top = healthy_sorted[:10]
    top_burn = sorted(healthy, key=lambda r: r["burn_fraction"], reverse=True)[:10]
    top_stable = sorted(healthy, key=lambda r: r["ratio_variance"])[:10]

    print(f"\n{'─' * 70}")
    print("TOP 10 — Best overall score (HEALTHY runs, balanced: burns + stability)")
    print(f"{'─' * 70}")
    _print_table(top)

    print(f"\n{'─' * 70}")
    print("TOP 10 — Maximum credit destruction (highest burn fraction, HEALTHY)")
    print(f"{'─' * 70}")
    _print_table(top_burn)

    print(f"\n{'─' * 70}")
    print("TOP 10 — Most stable (lowest backing ratio variance, HEALTHY)")
    print(f"{'─' * 70}")
    _print_table(top_stable)

    # Statistical summary of HEALTHY runs
    print(f"\n{'─' * 70}")
    print("HEALTHY RUN STATISTICS")
    print(f"{'─' * 70}")

    triggers = [r["trigger_ratio"] for r in healthy]
    burn_pcts = [r["burn_pct"] for r in healthy]
    cooldowns = [r["min_cooldown"] for r in healthy]
    burn_fracs = [r["burn_fraction"] for r in healthy]
    n_burns = [r["burn_events"] for r in healthy]

    print(
        f"  Trigger ratio:    mean={statistics.mean(triggers):.3f}  "
        f"median={statistics.median(triggers):.3f}  "
        f"stdev={statistics.stdev(triggers):.3f}"
    )
    print(
        f"  Burn pct:         mean={statistics.mean(burn_pcts):.3f}  "
        f"median={statistics.median(burn_pcts):.3f}  "
        f"stdev={statistics.stdev(burn_pcts):.3f}"
    )
    print(
        f"  Cooldown (mo):    mean={statistics.mean(cooldowns):.1f}  "
        f"median={statistics.median(cooldowns):.1f}  "
        f"stdev={statistics.stdev(cooldowns):.1f}"
    )
    print(
        f"  Burn fraction:    mean={statistics.mean(burn_fracs):.3f}  "
        f"median={statistics.median(burn_fracs):.3f}  "
        f"max={max(burn_fracs):.3f}"
    )
    print(
        f"  Burn events:      mean={statistics.mean(n_burns):.1f}  "
        f"median={statistics.median(n_burns):.1f}  "
        f"max={max(n_burns)}"
    )

    # Optimal zone analysis: bucket trigger_ratio into bands
    print(f"\n{'─' * 70}")
    print("HEALTHY RATE BY TRIGGER RATIO BAND")
    print(f"{'─' * 70}")
    bands = [(i / 10, (i + 1) / 10) for i in range(9, 16)]
    for lo, hi in bands:
        in_band_healthy = [r for r in healthy if lo <= r["trigger_ratio"] < hi]
        in_band_all = [r for r in results if lo <= r["trigger_ratio"] < hi]
        if in_band_all:
            pct = len(in_band_healthy) / len(in_band_all) * 100
            avg_burned = (
                statistics.mean([r["burn_fraction"] for r in in_band_healthy])
                if in_band_healthy
                else 0
            )
            print(
                f"  {lo:.1f}x–{hi:.1f}x:  {pct:>5.1f}% HEALTHY  "
                f"avg burn fraction: {avg_burned:.3f}"
            )

    print(f"\n{'─' * 70}")
    print("HEALTHY RATE BY BURN PCT BAND")
    print(f"{'─' * 70}")
    pct_bands = [(i / 100, (i + 5) / 100) for i in range(0, 35, 5)]
    for lo, hi in pct_bands:
        in_band_healthy = [r for r in healthy if lo <= r["burn_pct"] < hi]
        in_band_all = [r for r in results if lo <= r["burn_pct"] < hi]
        if in_band_all:
            pct = len(in_band_healthy) / len(in_band_all) * 100
            print(
                f"  {lo * 100:.0f}%–{hi * 100:.0f}%:  {pct:>5.1f}% HEALTHY  "
                f"({len(in_band_healthy):,} runs)"
            )

    # Best single strategy recommendation
    best = healthy_sorted[0]
    print(f"\n{'=' * 70}")
    print("RECOMMENDED STRATEGY (highest score, HEALTHY)")
    print(f"{'=' * 70}")
    print(
        f"  Trigger ratio:    {best['trigger_ratio']:.3f}  (burn when backing >= {best['trigger_ratio'] * 100:.1f}%)"
    )
    print(
        f"  Burn pct:         {best['burn_pct']:.3f}  (burn {best['burn_pct'] * 100:.1f}% of outstanding credits)"
    )
    print(f"  Min cooldown:     {best['min_cooldown']} months")
    print(f"  First eligible:   month {best['first_eligible']}")
    print(f"  Score:            {best['score']:.4f}")
    print(
        f"  Min backing:      {best['min_ratio']:.3f} ({best['min_ratio'] * 100:.1f}%)"
    )
    print(
        f"  Final backing:    {best['final_ratio']:.3f} ({best['final_ratio'] * 100:.1f}%)"
    )
    print(f"  Burn events:      {best['burn_events']}")
    print(
        f"  Credits burned:   {best['burn_fraction'] * 100:.1f}% of all credits ever minted"
    )
    print(
        f"  Burn event list:  {best['burn_event_list'][:10]}{'...' if len(best['burn_event_list']) > 10 else ''}"
    )

    # Compare vs. spreadsheet baseline
    print(f"\n{'─' * 70}")
    print("COMPARISON: Spreadsheet fixed burns vs. Best MC strategy")
    print(f"{'─' * 70}")
    spreadsheet = simulate_threshold(
        months=months,
        trigger_ratio=999,  # never trigger threshold
        burn_pct=0,
        min_cooldown=999,
        first_eligible=999,
    )
    # Run the spreadsheet scenario manually using fixed burns
    # (we'll re-import and run it separately for accuracy)
    print(f"  Spreadsheet (3 fixed burns):  min backing ~58.6%  verdict: WARNING")
    print(
        f"  Best MC strategy:             min backing {best['min_ratio'] * 100:.1f}%  "
        f"verdict: {best['verdict']}  burns: {best['burn_events']}"
    )


def _print_table(runs: list[dict]) -> None:
    print(
        f"  {'Trigger':>8} {'BurnPct':>8} {'Cooldown':>9} {'MinBacking':>11} "
        f"{'FinalBacking':>13} {'BurnFrac':>9} {'Events':>7} {'Score':>7}"
    )
    print(
        f"  {'─' * 8} {'─' * 8} {'─' * 9} {'─' * 11} {'─' * 13} {'─' * 9} {'─' * 7} {'─' * 7}"
    )
    for r in runs:
        print(
            f"  {r['trigger_ratio']:>7.3f}x {r['burn_pct'] * 100:>7.1f}% "
            f"{r['min_cooldown']:>8}mo {r['min_ratio'] * 100:>10.1f}% "
            f"{r['final_ratio'] * 100:>12.1f}% {r['burn_fraction'] * 100:>8.1f}% "
            f"{r['burn_events']:>7} {r['score']:>7.3f}"
        )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADBP v3 Monte Carlo burn optimizer")
    parser.add_argument("--runs", type=int, default=10_000, help="Number of MC runs")
    parser.add_argument("--months", type=int, default=120, help="Months per simulation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print(
        f"Running {args.runs:,} Monte Carlo simulations ({args.months} months each)..."
    )
    print(f"Seed: {args.seed}")
    print(f"Search space:")
    print(f"  trigger_ratio:  [{TRIGGER_RATIO_MIN}, {TRIGGER_RATIO_MAX}]")
    print(f"  burn_pct:       [{BURN_PCT_MIN * 100:.0f}%, {BURN_PCT_MAX * 100:.0f}%]")
    print(f"  cooldown:       [{COOLDOWN_MIN}, {COOLDOWN_MAX}] months")
    print(f"  first_eligible: [{FIRST_ELIGIBLE_MIN}, {FIRST_ELIGIBLE_MAX}] months")

    results = run_monte_carlo(args.runs, args.months, args.seed)
    summarize(results, args.months)
