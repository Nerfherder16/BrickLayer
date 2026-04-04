"""
monte_carlo.py — ADBP v3 Burn Strategy Optimization

Explores threshold-based burn strategies over a configurable time horizon with
optional stochastic employee growth. Each run samples a random strategy and a
random growth trajectory; the score rewards HEALTHY outcomes + credit destruction
while penalising backing-ratio variance.

Strategy parameters (sampled per run):
  trigger_ratio    — burn when backing_ratio exceeds this ceiling (e.g. 1.10)
  burn_pct         — % of outstanding credits to burn when triggered
  min_cooldown     — minimum months between burns
  first_eligible   — earliest month a burn can happen (ramp-up protection)

Stochastic growth:
  Each run independently draws its monthly employee-growth sequence from
  N(EMPLOYEE_GROWTH_PER_MONTH, growth_sigma).  Set --growth-sigma 0 for
  the original deterministic model.

Scoring (higher = better):
  +2.0  verdict == HEALTHY (backing ratio never < 0.75)
  +0.5  verdict == WARNING (solvent but under pressure)
  +burn_fraction × 2.0   reward liability reduction
  -ratio_variance × 5.0  reward stability
  +min(final_ratio, 1.5) × 0.5

Usage:
    python monte_carlo.py
    python monte_carlo.py --runs 100000 --months 240 --seeds 42 99 123 --growth-sigma 300
"""

import argparse
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

# =============================================================================
# FIXED SIMULATION PARAMETERS
# =============================================================================

INITIAL_EMPLOYEES = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE = 2_000
MAX_CREDITS_PER_EMPLOYEE = 5_000

# =============================================================================
# MONTE CARLO SEARCH SPACE
# =============================================================================

TRIGGER_RATIO_MIN = 0.90
TRIGGER_RATIO_MAX = 1.60

BURN_PCT_MIN = 0.02
BURN_PCT_MAX = 0.35

COOLDOWN_MIN = 3
COOLDOWN_MAX = 24

FIRST_ELIGIBLE_MIN = 6
FIRST_ELIGIBLE_MAX = 24


# =============================================================================
# INLINE SIMULATION
# =============================================================================


def simulate_threshold(
    months: int,
    trigger_ratio: float,
    burn_pct: float,
    min_cooldown: int,
    first_eligible: int,
    monthly_growth: list[int],
) -> dict:
    """
    monthly_growth: list of (months - 1) ints.
        Entry i is the new employees added when moving from month i+1 → month i+2.
        At month 1, employee count = INITIAL_EMPLOYEES.
        At month t > 1, employee count = INITIAL_EMPLOYEES + sum(monthly_growth[:t-1]).
    """
    # Pre-compute employee headcount per month
    employee_counts = [INITIAL_EMPLOYEES]
    for delta in monthly_growth:
        employee_counts.append(employee_counts[-1] + delta)

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
        employees = employee_counts[month - 1]
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

        cooldown_ok = (month - last_burn_month) >= min_cooldown
        eligible = month >= first_eligible

        if eligible and cooldown_ok and backing_ratio_pre >= trigger_ratio:
            credits_burned = int(total_credits * burn_pct)
            credits_burned = min(credits_burned, total_credits)

            # Affordability cap: post-burn backing never drops below FAILURE_THRESHOLD
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

    if failure_reason or min_ratio < FAILURE_THRESHOLD:
        verdict = "FAILURE"
    elif min_ratio < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    score = 0.0
    if verdict == "HEALTHY":
        score += 2.0
    elif verdict == "WARNING":
        score += 0.5
    score += burn_fraction * 2.0
    score -= ratio_variance * 5.0
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


def run_monte_carlo(
    n_runs: int, months: int, seed: int, growth_sigma: float
) -> list[dict]:
    rng = random.Random(seed)
    results = []

    for i in range(n_runs):
        if i % 5_000 == 0 and i > 0:
            print(f"  ... {i:,} / {n_runs:,} runs complete", flush=True)

        # Sample strategy parameters
        trigger_ratio = rng.uniform(TRIGGER_RATIO_MIN, TRIGGER_RATIO_MAX)
        burn_pct = rng.uniform(BURN_PCT_MIN, BURN_PCT_MAX)
        min_cooldown = rng.randint(COOLDOWN_MIN, COOLDOWN_MAX)
        first_eligible = rng.randint(FIRST_ELIGIBLE_MIN, FIRST_ELIGIBLE_MAX)

        # Generate stochastic growth trajectory (months - 1 increments)
        if growth_sigma > 0:
            monthly_growth = [
                max(0, round(rng.gauss(EMPLOYEE_GROWTH_PER_MONTH, growth_sigma)))
                for _ in range(months - 1)
            ]
        else:
            monthly_growth = [EMPLOYEE_GROWTH_PER_MONTH] * (months - 1)

        result = simulate_threshold(
            months=months,
            trigger_ratio=trigger_ratio,
            burn_pct=burn_pct,
            min_cooldown=min_cooldown,
            first_eligible=first_eligible,
            monthly_growth=monthly_growth,
        )
        results.append(result)

    return results


# =============================================================================
# REPORTING
# =============================================================================


def summarize(results: list[dict], months: int, label: str = "") -> None:
    total = len(results)
    healthy = [r for r in results if r["verdict"] == "HEALTHY"]
    warning = [r for r in results if r["verdict"] == "WARNING"]
    failure = [r for r in results if r["verdict"] == "FAILURE"]

    tag = f" [{label}]" if label else ""
    print(f"\n{'=' * 70}")
    print(f"MONTE CARLO RESULTS{tag} — {total:,} runs, {months} months")
    print(f"{'=' * 70}")
    print(f"  HEALTHY:  {len(healthy):>7,}  ({len(healthy) / total * 100:.2f}%)")
    print(f"  WARNING:  {len(warning):>7,}  ({len(warning) / total * 100:.2f}%)")
    print(f"  FAILURE:  {len(failure):>7,}  ({len(failure) / total * 100:.2f}%)")

    if not healthy:
        print("\n  No HEALTHY runs found. Try widening search space.")
        return

    healthy_sorted = sorted(healthy, key=lambda r: r["score"], reverse=True)
    top_score = healthy_sorted[:10]
    top_burn = sorted(healthy, key=lambda r: r["burn_fraction"], reverse=True)[:10]
    top_stable = sorted(healthy, key=lambda r: r["ratio_variance"])[:10]

    print(f"\n{'─' * 70}")
    print("TOP 10 — Best overall score (HEALTHY runs)")
    print(f"{'─' * 70}")
    _print_table(top_score)

    print(f"\n{'─' * 70}")
    print("TOP 10 — Maximum credit destruction (HEALTHY)")
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
        f"  Trigger ratio:  mean={statistics.mean(triggers):.3f}  "
        f"median={statistics.median(triggers):.3f}  "
        f"stdev={statistics.stdev(triggers):.3f}"
    )
    print(
        f"  Burn pct:       mean={statistics.mean(burn_pcts):.3f}  "
        f"median={statistics.median(burn_pcts):.3f}  "
        f"stdev={statistics.stdev(burn_pcts):.3f}"
    )
    print(
        f"  Cooldown (mo):  mean={statistics.mean(cooldowns):.1f}  "
        f"median={statistics.median(cooldowns):.1f}  "
        f"stdev={statistics.stdev(cooldowns):.1f}"
    )
    print(
        f"  Burn fraction:  mean={statistics.mean(burn_fracs):.3f}  "
        f"median={statistics.median(burn_fracs):.3f}  "
        f"max={max(burn_fracs):.3f}"
    )
    print(
        f"  Burn events:    mean={statistics.mean(n_burns):.1f}  "
        f"median={statistics.median(n_burns):.1f}  "
        f"max={max(n_burns)}"
    )

    # Trigger ratio bands
    print(f"\n{'─' * 70}")
    print("HEALTHY RATE BY TRIGGER RATIO BAND")
    print(f"{'─' * 70}")
    bands = [(i / 10, (i + 1) / 10) for i in range(9, 16)]
    for lo, hi in bands:
        band_h = [r for r in healthy if lo <= r["trigger_ratio"] < hi]
        band_all = [r for r in results if lo <= r["trigger_ratio"] < hi]
        if band_all:
            pct = len(band_h) / len(band_all) * 100
            avg_burned = (
                statistics.mean([r["burn_fraction"] for r in band_h]) if band_h else 0.0
            )
            print(
                f"  {lo:.1f}x–{hi:.1f}x:  {pct:>6.2f}% HEALTHY  "
                f"avg burn fraction: {avg_burned:.3f}"
            )

    # Burn pct bands
    print(f"\n{'─' * 70}")
    print("HEALTHY RATE BY BURN PCT BAND")
    print(f"{'─' * 70}")
    pct_bands = [(i / 100, (i + 5) / 100) for i in range(0, 35, 5)]
    for lo, hi in pct_bands:
        band_h = [r for r in healthy if lo <= r["burn_pct"] < hi]
        band_all = [r for r in results if lo <= r["burn_pct"] < hi]
        if band_all:
            pct = len(band_h) / len(band_all) * 100
            print(
                f"  {lo * 100:.0f}%–{hi * 100:.0f}%:  {pct:>6.2f}% HEALTHY  "
                f"({len(band_h):,} runs)"
            )

    # Best single strategy
    best = healthy_sorted[0]
    print(f"\n{'=' * 70}")
    print(f"RECOMMENDED STRATEGY{tag} (highest score, HEALTHY)")
    print(f"{'=' * 70}")
    print(
        f"  Trigger ratio:   {best['trigger_ratio']:.3f}  "
        f"(burn when backing >= {best['trigger_ratio'] * 100:.1f}%)"
    )
    print(
        f"  Burn pct:        {best['burn_pct']:.3f}  "
        f"(burn {best['burn_pct'] * 100:.1f}% of outstanding credits)"
    )
    print(f"  Min cooldown:    {best['min_cooldown']} months")
    print(f"  First eligible:  month {best['first_eligible']}")
    print(f"  Score:           {best['score']:.4f}")
    print(
        f"  Min backing:     {best['min_ratio']:.3f} ({best['min_ratio'] * 100:.1f}%)"
    )
    print(
        f"  Final backing:   {best['final_ratio']:.3f} ({best['final_ratio'] * 100:.1f}%)"
    )
    print(f"  Burn events:     {best['burn_events']}")
    print(
        f"  Credits burned:  {best['burn_fraction'] * 100:.1f}% of all credits ever minted"
    )
    print(
        f"  Burn event list: "
        f"{best['burn_event_list'][:10]}"
        f"{'...' if len(best['burn_event_list']) > 10 else ''}"
    )


def _print_table(runs: list[dict]) -> None:
    print(
        f"  {'Trigger':>8} {'BurnPct':>8} {'Cooldown':>9} {'MinBacking':>11} "
        f"{'FinalBacking':>13} {'BurnFrac':>9} {'Events':>7} {'Score':>7}"
    )
    print(
        f"  {'─' * 8} {'─' * 8} {'─' * 9} {'─' * 11} {'─' * 13} "
        f"{'─' * 9} {'─' * 7} {'─' * 7}"
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
    parser = argparse.ArgumentParser(
        description="ADBP v3 Monte Carlo — extended run with stochastic growth"
    )
    parser.add_argument(
        "--runs", type=int, default=10_000, help="Number of MC runs per seed"
    )
    parser.add_argument("--months", type=int, default=120, help="Months per simulation")
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42],
        help="Random seeds — one full run per seed (default: 42)",
    )
    parser.add_argument(
        "--growth-sigma",
        type=float,
        default=300.0,
        dest="growth_sigma",
        help=(
            "Std dev of monthly employee growth increments "
            "(0 = deterministic, default = 300 ≈ 30%% of mean)"
        ),
    )
    args = parser.parse_args()

    print("ADBP v3 Monte Carlo — Extended Run")
    print(f"  Runs per seed:    {args.runs:,}")
    print(f"  Months:           {args.months}")
    print(f"  Seeds:            {args.seeds}")
    print(
        f"  Growth model:     N(mean={EMPLOYEE_GROWTH_PER_MONTH}, "
        f"sigma={args.growth_sigma}) per month"
        + (" [DETERMINISTIC]" if args.growth_sigma == 0 else "")
    )
    print("  Search space:")
    print(f"    trigger_ratio:  [{TRIGGER_RATIO_MIN}, {TRIGGER_RATIO_MAX}]")
    print(f"    burn_pct:       [{BURN_PCT_MIN * 100:.0f}%, {BURN_PCT_MAX * 100:.0f}%]")
    print(f"    cooldown:       [{COOLDOWN_MIN}, {COOLDOWN_MAX}] months")
    print(f"    first_eligible: [{FIRST_ELIGIBLE_MIN}, {FIRST_ELIGIBLE_MAX}] months")
    print(
        f"\n  Total simulations: "
        f"{len(args.seeds) * args.runs:,} "
        f"({len(args.seeds)} seed(s) × {args.runs:,} runs × {args.months} months)"
    )

    all_results: list[dict] = []
    per_seed: dict[int, list[dict]] = {}

    for seed in args.seeds:
        print(f"\n── seed={seed} ──────────────────────────────────────────────────")
        seed_results = run_monte_carlo(args.runs, args.months, seed, args.growth_sigma)
        per_seed[seed] = seed_results
        all_results.extend(seed_results)

        if len(args.seeds) > 1:
            # Per-seed summary (condensed — no tables)
            total = len(seed_results)
            h = sum(1 for r in seed_results if r["verdict"] == "HEALTHY")
            w = sum(1 for r in seed_results if r["verdict"] == "WARNING")
            f = sum(1 for r in seed_results if r["verdict"] == "FAILURE")
            print(
                f"  seed={seed}: HEALTHY={h / total * 100:.2f}%  "
                f"WARNING={w / total * 100:.2f}%  "
                f"FAILURE={f / total * 100:.2f}%"
            )

    if len(args.seeds) > 1:
        # Stability table
        print(f"\n{'─' * 70}")
        print("SEED STABILITY CHECK")
        print(f"{'─' * 70}")
        for seed, results in per_seed.items():
            total = len(results)
            h = sum(1 for r in results if r["verdict"] == "HEALTHY")
            w = sum(1 for r in results if r["verdict"] == "WARNING")
            f = sum(1 for r in results if r["verdict"] == "FAILURE")
            print(
                f"  Seed {seed:>5}:  "
                f"HEALTHY={h / total * 100:>6.2f}%  "
                f"WARNING={w / total * 100:>6.2f}%  "
                f"FAILURE={f / total * 100:>6.2f}%"
            )
        # Full aggregate summary with tables
        print(f"\n\n{'#' * 70}")
        print(
            f"  AGGREGATE — {len(args.seeds)} seeds × {args.runs:,} runs = "
            f"{len(all_results):,} total"
        )
        print(f"{'#' * 70}")
        summarize(all_results, args.months, label="AGGREGATE")
    else:
        summarize(all_results, args.months)
