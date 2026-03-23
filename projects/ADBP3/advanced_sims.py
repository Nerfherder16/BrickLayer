"""
advanced_sims.py — ADBP v3 Extended Simulation Suite

Runs eight distinct simulation families to stress-test and validate the model:

  1. Velocity Sensitivity      — breakage rate at 1×/3×/6×/12×/24× annual velocity
  2. Regime-Switching Growth   — Markov chain BOOM/NORMAL/BUST employee growth
  3. Interest Rate Scenarios   — 0%, 1%, 2%, 4%, 6%, 8% APR
  4. Regulatory Shock          — floor raised to 75% or 100% backing requirement
  5. Burn Timing Alternatives  — threshold vs fixed-calendar vs quarterly-calendar
  6. Correlated Adversity      — growth bust + rate shock + vendor dropout combined
  7. Tornado Chart             — parameter sensitivity ranking
  8. Tail Risk Analysis        — left-tail distribution of minimum backing ratios

Usage:
    python advanced_sims.py
    python advanced_sims.py --months 120 --runs 5000
"""

import argparse
import io
import random
import statistics
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from constants import (
    BURN_COST_PER_CREDIT,
    CREDIT_PRICE,
    FAILURE_THRESHOLD,
    WARNING_THRESHOLD,
)

# ── Simulation parameters ─────────────────────────────────────────────────────
INITIAL_EMPLOYEES       = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE    = 2_000
BASE_MONTHLY_RATE       = 0.04 / 12   # 4% APR baseline
HEALTHY_THRESHOLD       = WARNING_THRESHOLD  # 0.75

# MC-optimal strategy (from 300k-run campaign)
OPT_TRIGGER   = 1.332
OPT_BURN_PCT  = 0.349
OPT_COOLDOWN  = 18
OPT_FIRST_EL  = 20

# ── Core simulation (mirrors monte_carlo.py logic) ────────────────────────────

def simulate(
    months: int,
    trigger_ratio: float,
    burn_pct: float,
    min_cooldown: int,
    first_eligible: int,
    monthly_growth: list,
    monthly_interest_rate: float = BASE_MONTHLY_RATE,
    floor_ratio: float = FAILURE_THRESHOLD,
    burn_timing: str = "threshold",          # "threshold" | "annual" | "quarterly"
    monthly_expiry: list = None,             # optional list[float] of credits to expire per month
) -> dict:
    employee_counts = [INITIAL_EMPLOYEES]
    for delta in monthly_growth:
        employee_counts.append(max(0, employee_counts[-1] + delta))

    wallet         = 0.0
    total_credits  = 0
    interest_prev  = 0.0
    cum_minted     = 0
    cum_burned     = 0
    cum_expired    = 0
    last_burn_mo   = 0
    burn_events    = []
    backing_ratios = []

    for month in range(1, months + 1):
        employees      = employee_counts[month - 1]
        credits_minted = employees * CREDITS_PER_EMPLOYEE
        inflow         = credits_minted * CREDIT_PRICE

        wallet         = (wallet + interest_prev + inflow) if month > 1 else inflow
        total_credits += credits_minted
        cum_minted    += credits_minted

        # Optional expiry (no treasury cost)
        if monthly_expiry:
            expired = min(int(monthly_expiry[month - 1]), total_credits)
            total_credits -= expired
            cum_expired   += expired

        # Burn decision
        fire_burn = False
        backing_pre = wallet / total_credits if total_credits > 0 else 1.0
        cooldown_ok = (month - last_burn_mo) >= min_cooldown
        eligible    = month >= first_eligible

        if burn_timing == "threshold":
            fire_burn = eligible and cooldown_ok and backing_pre >= trigger_ratio
        elif burn_timing == "annual":
            # Fire once per year if eligible, cooldown ok, and above floor
            fire_burn = eligible and cooldown_ok and (month % 12 == 0) and backing_pre >= trigger_ratio
        elif burn_timing == "quarterly":
            fire_burn = eligible and cooldown_ok and (month % 3 == 0) and backing_pre >= trigger_ratio

        if fire_burn and total_credits > 0:
            desired      = int(total_credits * burn_pct)
            max_afford   = int((wallet - floor_ratio * total_credits)
                               / (BURN_COST_PER_CREDIT - floor_ratio))
            to_burn      = min(desired, max(0, max_afford))
            if to_burn > 0:
                wallet        -= to_burn * BURN_COST_PER_CREDIT
                total_credits -= to_burn
                cum_burned    += to_burn
                last_burn_mo   = month
                burn_events.append((month, to_burn))

        interest_prev = wallet * monthly_interest_rate

        ratio = wallet / total_credits if total_credits > 0 else 1.0
        backing_ratios.append(ratio)

        if wallet < 0:
            break

    if not backing_ratios:
        return {"verdict": "FAILURE", "min_backing": 0.0, "final_backing": 0.0,
                "burn_events": 0, "burn_fraction": 0.0, "expired_fraction": 0.0}

    min_r  = min(backing_ratios)
    final_r = backing_ratios[-1]
    burn_frac = cum_burned / cum_minted if cum_minted > 0 else 0.0
    exp_frac  = cum_expired / cum_minted if cum_minted > 0 else 0.0

    if min_r < FAILURE_THRESHOLD:
        verdict = "FAILURE"
    elif min_r < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    return {
        "verdict":          verdict,
        "min_backing":      min_r,
        "final_backing":    final_r,
        "burn_events":      len(burn_events),
        "burn_event_list":  burn_events,
        "burn_fraction":    burn_frac,
        "expired_fraction": exp_frac,
        "backing_ratios":   backing_ratios,
    }


def flat_growth(months):
    return [EMPLOYEE_GROWTH_PER_MONTH] * (months - 1)

def stochastic_growth(months, seed=42, sigma=300):
    rng = random.Random(seed)
    return [max(0, round(rng.gauss(EMPLOYEE_GROWTH_PER_MONTH, sigma)))
            for _ in range(months - 1)]

def mc_runs(months, runs, seed, growth_sigma, trigger, burn_pct, cooldown, first_el,
            monthly_interest_rate=BASE_MONTHLY_RATE, floor_ratio=FAILURE_THRESHOLD,
            burn_timing="threshold"):
    rng = random.Random(seed)
    counts = {"HEALTHY": 0, "WARNING": 0, "FAILURE": 0}
    min_backings = []
    burn_fracs   = []
    for _ in range(runs):
        growth = [max(0, round(rng.gauss(EMPLOYEE_GROWTH_PER_MONTH, growth_sigma)))
                  for _ in range(months - 1)]
        r = simulate(months, trigger, burn_pct, cooldown, first_el, growth,
                     monthly_interest_rate=monthly_interest_rate,
                     floor_ratio=floor_ratio, burn_timing=burn_timing)
        counts[r["verdict"]] += 1
        min_backings.append(r["min_backing"])
        burn_fracs.append(r["burn_fraction"])
    return counts, min_backings, burn_fracs

def pct(n, total):
    return f"{100*n/total:.2f}%" if total else "n/a"

def bar(v, width=20):
    filled = round(v * width)
    return "█" * filled + "░" * (width - filled)

def sep(char="─", width=70):
    print(char * width)

def hdr(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Velocity Sensitivity
# ═════════════════════════════════════════════════════════════════════════════

def run_velocity_sensitivity(months, runs, seed):
    hdr("SECTION 1 — Velocity Sensitivity")
    print("  At lower velocity, credits sit longer → higher breakage rate.")
    print("  Breakage eliminates $2 obligations for $0 cost.")
    print()

    # velocity → annual breakage rate (from expiry_analysis research)
    VELOCITY_BREAKAGE = {24: 0.04, 12: 0.06, 6: 0.08, 3: 0.11, 1: 0.14}

    print(f"  {'Velocity':>10}  {'Ann.Breakage':>12}  {'HEALTHY':>8}  {'WARNING':>8}  "
          f"{'FAILURE':>8}  {'AvgBurnEvts':>11}  {'AvgBurnFrac':>11}")
    sep()

    # Baseline (no breakage)
    rng = random.Random(seed)
    counts, min_b, bf = mc_runs(months, runs, seed, 300,
                                OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL)
    total = sum(counts.values())
    print(f"  {'baseline':>10}  {'0%':>12}  {pct(counts['HEALTHY'],total):>8}  "
          f"{pct(counts['WARNING'],total):>8}  {pct(counts['FAILURE'],total):>8}  "
          f"{'n/a':>11}  {statistics.mean(bf)*100:>10.1f}%")

    for velocity, ann_breakage in sorted(VELOCITY_BREAKAGE.items(), reverse=True):
        monthly_breakage = ann_breakage / 12
        h = w = f = 0
        all_bf = []
        all_burn_evts = []
        rng2 = random.Random(seed)
        for _ in range(runs):
            growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                      for _ in range(months - 1)]
            # Build monthly expiry list from breakage rate applied to outstanding
            # We pre-compute a simplified expiry: each month, breakage_rate * outstanding
            # (proportional drain — simpler than cohort tracking for this sweep)
            # We'll inject expiry_override via a wrapper
            r = simulate_with_breakage(months, OPT_TRIGGER, OPT_BURN_PCT,
                                       OPT_COOLDOWN, OPT_FIRST_EL, growth,
                                       monthly_breakage=monthly_breakage)
            verdict = r["verdict"]
            if verdict == "HEALTHY": h += 1
            elif verdict == "WARNING": w += 1
            else: f += 1
            all_bf.append(r["burn_fraction"])
            all_burn_evts.append(r["burn_events"])
        tot = h + w + f
        print(f"  {velocity:>9}x  {ann_breakage*100:>11.0f}%  {pct(h,tot):>8}  "
              f"{pct(w,tot):>8}  {pct(f,tot):>8}  "
              f"{statistics.mean(all_burn_evts):>11.1f}  "
              f"{statistics.mean(all_bf)*100:>10.1f}%")


def simulate_with_breakage(months, trigger, burn_pct, cooldown, first_el,
                            monthly_growth, monthly_breakage):
    """Variant of simulate() with a proportional monthly breakage drain."""
    employee_counts = [INITIAL_EMPLOYEES]
    for delta in monthly_growth:
        employee_counts.append(max(0, employee_counts[-1] + delta))

    wallet         = 0.0
    total_credits  = 0
    interest_prev  = 0.0
    cum_minted     = 0
    cum_burned     = 0
    cum_expired    = 0
    last_burn_mo   = 0
    burn_events    = []
    backing_ratios = []

    for month in range(1, months + 1):
        employees      = employee_counts[month - 1]
        credits_minted = employees * CREDITS_PER_EMPLOYEE
        inflow         = credits_minted * CREDIT_PRICE

        wallet         = (wallet + interest_prev + inflow) if month > 1 else inflow
        total_credits += credits_minted
        cum_minted    += credits_minted

        # Breakage drain (no treasury cost)
        expired = int(total_credits * monthly_breakage)
        total_credits = max(0, total_credits - expired)
        cum_expired  += expired

        # Burn
        backing_pre = wallet / total_credits if total_credits > 0 else 1.0
        cooldown_ok = (month - last_burn_mo) >= cooldown
        eligible    = month >= first_el

        if eligible and cooldown_ok and backing_pre >= trigger and total_credits > 0:
            desired    = int(total_credits * burn_pct)
            max_afford = int((wallet - FAILURE_THRESHOLD * total_credits)
                             / (BURN_COST_PER_CREDIT - FAILURE_THRESHOLD))
            to_burn    = min(desired, max(0, max_afford))
            if to_burn > 0:
                wallet        -= to_burn * BURN_COST_PER_CREDIT
                total_credits -= to_burn
                cum_burned    += to_burn
                last_burn_mo   = month
                burn_events.append((month, to_burn))

        interest_prev = wallet * BASE_MONTHLY_RATE
        ratio = wallet / total_credits if total_credits > 0 else 1.0
        backing_ratios.append(ratio)
        if wallet < 0:
            break

    if not backing_ratios:
        return {"verdict": "FAILURE", "min_backing": 0.0, "final_backing": 0.0,
                "burn_events": 0, "burn_fraction": 0.0}

    min_r   = min(backing_ratios)
    burn_frac = cum_burned / cum_minted if cum_minted > 0 else 0.0

    if min_r < FAILURE_THRESHOLD:
        verdict = "FAILURE"
    elif min_r < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    return {"verdict": verdict, "min_backing": min_r,
            "final_backing": backing_ratios[-1],
            "burn_events": len(burn_events), "burn_fraction": burn_frac}


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Regime-Switching Growth
# ═════════════════════════════════════════════════════════════════════════════

def run_regime_switching(months, runs, seed):
    hdr("SECTION 2 — Regime-Switching Growth (Markov Chain)")
    print("  Growth follows BOOM/NORMAL/BUST states with probabilistic transitions.")
    print()

    # State definitions: (mean_growth, sigma)
    STATES = {
        "BOOM":   (2500, 400),
        "NORMAL": (1000, 300),
        "BUST":   (-300, 500),
    }
    # Transition matrix [from][to]
    TRANSITIONS = {
        "BOOM":   {"BOOM": 0.70, "NORMAL": 0.25, "BUST": 0.05},
        "NORMAL": {"BOOM": 0.15, "NORMAL": 0.70, "BUST": 0.15},
        "BUST":   {"BOOM": 0.05, "NORMAL": 0.45, "BUST": 0.50},
    }

    def markov_growth(n_months, rng, start_state="NORMAL"):
        state = start_state
        result = []
        for _ in range(n_months):
            mean, sigma = STATES[state]
            delta = max(-employee_count_floor(), round(rng.gauss(mean, sigma)))
            result.append(delta)
            # Transition
            r = rng.random()
            cumulative = 0.0
            for next_state, prob in TRANSITIONS[state].items():
                cumulative += prob
                if r <= cumulative:
                    state = next_state
                    break
        return result

    def employee_count_floor():
        return 0  # can go negative but capped at 0 in simulate()

    print(f"  {'Start State':>12}  {'HEALTHY':>8}  {'WARNING':>8}  {'FAILURE':>8}  "
          f"{'MinBack(avg)':>13}  {'MinBack(p5)':>11}")
    sep()

    # Also run baseline Gaussian for comparison
    rng_b = random.Random(seed)
    h = w = f = 0
    min_bs = []
    for _ in range(runs):
        growth = [max(0, round(rng_b.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                  for _ in range(months - 1)]
        r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL, growth)
        if r["verdict"] == "HEALTHY": h += 1
        elif r["verdict"] == "WARNING": w += 1
        else: f += 1
        min_bs.append(r["min_backing"])
    tot = h + w + f
    min_bs_sorted = sorted(min_bs)
    p5 = min_bs_sorted[int(0.05 * len(min_bs_sorted))]
    print(f"  {'Baseline(N)':>12}  {pct(h,tot):>8}  {pct(w,tot):>8}  {pct(f,tot):>8}  "
          f"{statistics.mean(min_bs)*100:>12.1f}%  {p5*100:>10.1f}%")

    for start_state in ["NORMAL", "BOOM", "BUST"]:
        rng2 = random.Random(seed + 1)
        h = w = f = 0
        min_bs = []
        for _ in range(runs):
            growth = markov_growth(months - 1, rng2, start_state)
            r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL, growth)
            if r["verdict"] == "HEALTHY": h += 1
            elif r["verdict"] == "WARNING": w += 1
            else: f += 1
            min_bs.append(r["min_backing"])
        tot = h + w + f
        min_bs_sorted = sorted(min_bs)
        p5 = min_bs_sorted[int(0.05 * len(min_bs_sorted))]
        print(f"  {start_state:>12}  {pct(h,tot):>8}  {pct(w,tot):>8}  {pct(f,tot):>8}  "
              f"{statistics.mean(min_bs)*100:>12.1f}%  {p5*100:>10.1f}%")

    print()
    print("  State definitions:")
    for state, (mean, sigma) in STATES.items():
        print(f"    {state:6}: growth ~ N({mean:+,}, {sigma})/month")
    print()
    print("  Transition probabilities (row=from, col=to):")
    print(f"  {'':10}  {'→BOOM':>8}  {'→NORMAL':>8}  {'→BUST':>8}")
    for from_state, trans in TRANSITIONS.items():
        print(f"  {from_state:10}  {trans['BOOM']*100:>7.0f}%  "
              f"{trans['NORMAL']*100:>7.0f}%  {trans['BUST']*100:>7.0f}%")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Interest Rate Scenarios
# ═════════════════════════════════════════════════════════════════════════════

def run_interest_rate_scenarios(months, runs, seed):
    hdr("SECTION 3 — Interest Rate Scenarios")
    print("  Treasury earns interest on wallet balance. Rate directly affects")
    print("  how fast backing ratio grows and how often burn triggers fire.")
    print()

    rates = [0.00, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08]

    print(f"  {'APR':>6}  {'HEALTHY':>8}  {'WARNING':>8}  {'FAILURE':>8}  "
          f"{'MinBack(avg)':>13}  {'AvgBurnEvts':>12}  {'AvgBurnFrac':>12}")
    sep()

    for apr in rates:
        monthly_rate = apr / 12
        counts, min_b, bf = mc_runs(months, runs, seed, 300,
                                    OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL,
                                    monthly_interest_rate=monthly_rate)
        total = sum(counts.values())
        rng2 = random.Random(seed)
        burn_evts = []
        for _ in range(runs):
            growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                      for _ in range(months - 1)]
            r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL,
                         growth, monthly_interest_rate=monthly_rate)
            burn_evts.append(r["burn_events"])
        print(f"  {apr*100:>5.0f}%  {pct(counts['HEALTHY'],total):>8}  "
              f"{pct(counts['WARNING'],total):>8}  {pct(counts['FAILURE'],total):>8}  "
              f"{statistics.mean(min_b)*100:>12.1f}%  "
              f"{statistics.mean(burn_evts):>12.1f}  "
              f"{statistics.mean(bf)*100:>11.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Regulatory Shock (Floor Change)
# ═════════════════════════════════════════════════════════════════════════════

def run_regulatory_shock(months, runs, seed):
    hdr("SECTION 4 — Regulatory Shock (Backing Floor Change)")
    print("  What if regulators require a higher minimum backing ratio?")
    print("  Floor affects: (a) burn affordability cap, (b) FAILURE threshold.")
    print()

    scenarios = [
        (0.50, "Current (50% floor)"),
        (0.75, "Raised to 75%"),
        (1.00, "Raised to 100% (full backing)"),
    ]

    print(f"  {'Floor':>8}  {'Scenario':28}  {'HEALTHY':>8}  {'WARNING':>8}  "
          f"{'FAILURE':>8}  {'AvgBurnFrac':>12}")
    sep()

    for floor, label in scenarios:
        h = w = f = 0
        bf_all = []
        rng2 = random.Random(seed)
        for _ in range(runs):
            growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                      for _ in range(months - 1)]
            # Redefine verdict thresholds with new floor
            r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL,
                         growth, floor_ratio=floor)
            # Re-evaluate verdict against new floor (floor = new FAILURE threshold)
            min_b = r["min_backing"]
            if min_b < floor:
                verdict = "FAILURE"
            elif min_b < WARNING_THRESHOLD:
                verdict = "WARNING"
            else:
                verdict = "HEALTHY"
            if verdict == "HEALTHY": h += 1
            elif verdict == "WARNING": w += 1
            else: f += 1
            bf_all.append(r["burn_fraction"])
        tot = h + w + f
        print(f"  {floor*100:>7.0f}%  {label:28}  {pct(h,tot):>8}  "
              f"{pct(w,tot):>8}  {pct(f,tot):>8}  "
              f"{statistics.mean(bf_all)*100:>11.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Burn Timing Alternatives
# ═════════════════════════════════════════════════════════════════════════════

def run_burn_timing(months, runs, seed):
    hdr("SECTION 5 — Burn Timing Alternatives")
    print("  Compares threshold-triggered vs fixed-calendar burn schedules.")
    print()

    timings = [
        ("threshold",  "Threshold-triggered (current)"),
        ("annual",     "Fixed-calendar: annual (month % 12 == 0)"),
        ("quarterly",  "Fixed-calendar: quarterly (month % 3 == 0)"),
    ]

    print(f"  {'Timing':12}  {'Description':35}  {'HEALTHY':>8}  {'WARNING':>8}  "
          f"{'AvgBurns':>9}  {'AvgBurnFrac':>12}")
    sep()

    for timing_key, label in timings:
        h = w = f = 0
        burns_all = []
        bf_all    = []
        rng2 = random.Random(seed)
        for _ in range(runs):
            growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                      for _ in range(months - 1)]
            r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL,
                         growth, burn_timing=timing_key)
            if r["verdict"] == "HEALTHY": h += 1
            elif r["verdict"] == "WARNING": w += 1
            else: f += 1
            burns_all.append(r["burn_events"])
            bf_all.append(r["burn_fraction"])
        tot = h + w + f
        print(f"  {timing_key:12}  {label:35}  {pct(h,tot):>8}  {pct(w,tot):>8}  "
              f"{statistics.mean(burns_all):>9.1f}  "
              f"{statistics.mean(bf_all)*100:>11.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Correlated Adversity
# ═════════════════════════════════════════════════════════════════════════════

def run_correlated_adversity(months, runs, seed):
    hdr("SECTION 6 — Correlated Adversity Scenarios")
    print("  Multiple bad conditions occurring simultaneously.")
    print()

    def bust_growth(months, rng, severity=0.5):
        """Growth collapses to negative after month 12."""
        growth = []
        for i in range(months - 1):
            if i < 12:
                growth.append(max(0, round(rng.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300))))
            else:
                growth.append(round(rng.gauss(-EMPLOYEE_GROWTH_PER_MONTH * severity, 400)))
        return growth

    scenarios = [
        # (label, apr, growth_fn, floor)
        ("Baseline",                         0.04, "normal",  0.50),
        ("Zero interest",                    0.00, "normal",  0.50),
        ("Growth bust (50% decline)",        0.04, "bust50",  0.50),
        ("Growth bust + zero interest",      0.00, "bust50",  0.50),
        ("Severe bust (90% decline)",        0.04, "bust90",  0.50),
        ("Severe bust + zero interest",      0.00, "bust90",  0.50),
        ("All adverse (bust+0%+75% floor)",  0.00, "bust50",  0.75),
    ]

    print(f"  {'Scenario':42}  {'HEALTHY':>8}  {'WARNING':>8}  {'FAILURE':>8}  "
          f"{'MinBack(p5)':>12}")
    sep()

    for label, apr, growth_type, floor in scenarios:
        h = w = f = 0
        min_bs = []
        rng2 = random.Random(seed)
        monthly_rate = apr / 12
        for _ in range(runs):
            if growth_type == "normal":
                growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                          for _ in range(months - 1)]
            elif growth_type == "bust50":
                growth = bust_growth(months, rng2, severity=0.50)
            elif growth_type == "bust90":
                growth = bust_growth(months, rng2, severity=0.90)

            r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL,
                         growth, monthly_interest_rate=monthly_rate, floor_ratio=floor)
            min_b = r["min_backing"]
            if min_b < floor: f += 1
            elif min_b < WARNING_THRESHOLD: w += 1
            else: h += 1
            min_bs.append(min_b)
        tot = h + w + f
        p5 = sorted(min_bs)[int(0.05 * len(min_bs))]
        print(f"  {label:42}  {pct(h,tot):>8}  {pct(w,tot):>8}  {pct(f,tot):>8}  "
              f"{p5*100:>11.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Tornado Chart (Parameter Sensitivity)
# ═════════════════════════════════════════════════════════════════════════════

def run_tornado(months, runs, seed):
    hdr("SECTION 7 — Tornado Chart (Parameter Sensitivity)")
    print("  Each parameter swept independently; others held at MC-optimal values.")
    print("  Ranks parameters by impact on HEALTHY rate.")
    print()

    def sweep_param(param_name, values, base_params, rng_seed):
        results = []
        for val in values:
            params = dict(base_params)
            params[param_name] = val
            h = 0
            rng2 = random.Random(rng_seed)
            for _ in range(runs):
                growth = [max(0, round(rng2.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                          for _ in range(months - 1)]
                r = simulate(months, params["trigger"], params["burn_pct"],
                             params["cooldown"], params["first_el"], growth)
                if r["verdict"] == "HEALTHY":
                    h += 1
            results.append((val, h / runs * 100))
        return results

    base = {"trigger": OPT_TRIGGER, "burn_pct": OPT_BURN_PCT,
            "cooldown": OPT_COOLDOWN, "first_el": OPT_FIRST_EL}

    sweeps = [
        ("trigger",   [0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60]),
        ("burn_pct",  [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]),
        ("cooldown",  [3, 6, 9, 12, 15, 18, 21, 24]),
        ("first_el",  [6, 9, 12, 15, 18, 21, 24]),
    ]

    param_ranges = {}
    for param_name, values in sweeps:
        results = sweep_param(param_name, values, base, seed)
        healthy_rates = [r for _, r in results]
        param_ranges[param_name] = (min(healthy_rates), max(healthy_rates), results)

    # Sort by range (max - min)
    sorted_params = sorted(param_ranges.items(), key=lambda x: x[1][1] - x[1][0], reverse=True)

    PARAM_LABELS = {
        "trigger":  "Trigger ratio",
        "burn_pct": "Burn size %",
        "cooldown": "Cooldown months",
        "first_el": "First eligible month",
    }

    print(f"  {'Parameter':22}  {'Min HEALTHY':>11}  {'Max HEALTHY':>11}  "
          f"{'Range':>8}  {'Impact':>8}")
    sep()
    for param_name, (lo, hi, _) in sorted_params:
        label = PARAM_LABELS.get(param_name, param_name)
        rng_val = hi - lo
        bar_str = bar(rng_val / 100)
        print(f"  {label:22}  {lo:>10.1f}%  {hi:>10.1f}%  {rng_val:>7.1f}%  {bar_str}")

    print()
    print("  Detail by parameter value:")
    for param_name, (lo, hi, results) in sorted_params:
        label = PARAM_LABELS.get(param_name, param_name)
        print(f"\n  {label}:")
        for val, healthy_pct in results:
            marker = " ◄ optimal" if abs(val - base.get(param_name, -1)) < 1e-6 else ""
            print(f"    {val:>8}  {healthy_pct:>6.1f}%  {bar(healthy_pct/100, 30)}{marker}")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Tail Risk Analysis
# ═════════════════════════════════════════════════════════════════════════════

def run_tail_risk(months, runs, seed):
    hdr("SECTION 8 — Tail Risk Analysis")
    print("  Distribution of minimum backing ratios across all runs.")
    print("  Focus: left tail (worst outcomes). Optimal strategy + stochastic growth.")
    print()

    rng = random.Random(seed)
    min_backings = []
    final_backings = []
    burn_months_first = []

    for _ in range(runs):
        growth = [max(0, round(rng.gauss(EMPLOYEE_GROWTH_PER_MONTH, 300)))
                  for _ in range(months - 1)]
        r = simulate(months, OPT_TRIGGER, OPT_BURN_PCT, OPT_COOLDOWN, OPT_FIRST_EL, growth)
        min_backings.append(r["min_backing"])
        final_backings.append(r["final_backing"])
        evts = r.get("burn_event_list", [])
        burn_months_first.append(evts[0][0] if evts else None)

    min_b_sorted = sorted(min_backings)
    n = len(min_b_sorted)

    percentiles = [0.1, 0.5, 1, 2, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"  {'Percentile':>12}  {'Min Backing':>12}  {'Status':>10}")
    sep()
    for pct_val in percentiles:
        idx = max(0, int(pct_val / 100 * n) - 1)
        mb  = min_b_sorted[idx]
        if mb < FAILURE_THRESHOLD:
            status = "FAILURE"
        elif mb < WARNING_THRESHOLD:
            status = "WARNING"
        else:
            status = "HEALTHY"
        print(f"  {pct_val:>11.1f}%  {mb*100:>11.1f}%  {status:>10}")

    print()
    print(f"  Mean min backing:   {statistics.mean(min_backings)*100:.1f}%")
    print(f"  Stdev min backing:  {statistics.stdev(min_backings)*100:.1f}%")
    print(f"  Mean final backing: {statistics.mean(final_backings)*100:.1f}%")

    # Histogram of min backing
    print()
    print("  Distribution of min backing ratios:")
    buckets = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.75), (0.75, 0.80),
               (0.80, 0.90), (0.90, 1.00), (1.00, 1.10), (1.10, float('inf'))]
    bucket_labels = ["50-60%", "60-70%", "70-75%", "75-80%",
                     "80-90%", "90-100%", "100-110%", ">110%"]
    for (lo, hi), lbl in zip(buckets, bucket_labels):
        count = sum(1 for x in min_backings if lo <= x < hi)
        pct_count = count / n
        status = "FAILURE" if hi <= FAILURE_THRESHOLD else \
                 "WARNING" if hi <= WARNING_THRESHOLD else "HEALTHY"
        print(f"  {lbl:>10}  {bar(pct_count, 30)}  {pct_count*100:>5.1f}%  {status}")

    # First burn month distribution
    fired = [m for m in burn_months_first if m is not None]
    no_burn = sum(1 for m in burn_months_first if m is None)
    print()
    print(f"  Runs with 0 burn events: {no_burn} ({no_burn/n*100:.1f}%)")
    if fired:
        print(f"  First burn month — mean: {statistics.mean(fired):.0f}, "
              f"median: {statistics.median(fired):.0f}, "
              f"min: {min(fired)}, max: {max(fired)}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="ADBP Advanced Simulation Suite")
    parser.add_argument("--months", type=int, default=120,
                        help="Simulation horizon in months (default: 120)")
    parser.add_argument("--runs",   type=int, default=5_000,
                        help="MC runs per scenario (default: 5,000)")
    parser.add_argument("--seed",   type=int, default=42,
                        help="RNG seed (default: 42)")
    args = parser.parse_args()

    print("=" * 70)
    print("  ADBP v3 Advanced Simulation Suite")
    print(f"  Months: {args.months}  |  Runs per scenario: {args.runs:,}  |  Seed: {args.seed}")
    print(f"  Optimal strategy: trigger={OPT_TRIGGER}x  burn={OPT_BURN_PCT*100:.1f}%  "
          f"cooldown={OPT_COOLDOWN}mo  first_eligible=mo{OPT_FIRST_EL}")
    print("=" * 70)

    run_velocity_sensitivity(args.months, args.runs, args.seed)
    run_regime_switching(args.months, args.runs, args.seed)
    run_interest_rate_scenarios(args.months, args.runs, args.seed)
    run_regulatory_shock(args.months, args.runs, args.seed)
    run_burn_timing(args.months, args.runs, args.seed)
    run_correlated_adversity(args.months, args.runs, args.seed)
    run_tornado(args.months, args.runs, args.seed)
    run_tail_risk(args.months, args.runs, args.seed)

    print()
    print("=" * 70)
    print("  Run complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
