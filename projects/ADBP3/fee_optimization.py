"""
fee_optimization.py — ADBP v3 Admin Fee Optimization

Sweeps the admin fee from $0.01 to $0.10 to find the optimal fee level that:
  - Maximizes vendor incentive (admin income meaningfulness, recirculation gradient)
  - Keeps employee premium low (effective cost per $2 purchasing power)
  - Maintains zero treasury risk (treasury always gets $1.00/credit regardless of fee)

KEY ASSUMPTION (consistent with structural solvency proof and 300K MC runs):
  The admin fee is ADDITIONAL to the $1.00 treasury inflow. Employee pays $1.00 to
  treasury + admin fee to admin pool. This is why the structural guarantee holds:
  treasury always receives exactly $1.00/credit regardless of admin fee level.
  Treasury risk = 0 at every fee level in this sweep.

Metrics per fee level:
  1. Employee effective cost and net discount rate
  2. Admin pool size at key checkpoints
  3. Per-vendor income at standard recirculation shares (1%, 5%, 10%, 20%)
  4. Recirculation incentive gradient ($/month per 1% share)
  5. Vendor discount cost coverage ratio (admin income / discount cost)
  6. Composite incentive score

Usage:
    python fee_optimization.py
    python fee_optimization.py --months 120
"""

import argparse
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── Growth constants (same as all other sims) ─────────────────────────────────
INITIAL_EMPLOYEES = 1_000
EMPLOYEE_GROWTH_PER_MONTH = 1_000
CREDITS_PER_EMPLOYEE = 2_000
CREDIT_PRICE = 1.00  # treasury inflow per credit (fixed, guaranteed)
PURCHASING_POWER = 2.00  # vendor provides $2 of goods per credit accepted
VENDOR_DISCOUNT_COST = (
    PURCHASING_POWER - CREDIT_PRICE
)  # $1.00 cost to vendor per credit accepted

# Fee sweep range
FEE_RANGE = [round(0.01 * i, 2) for i in range(1, 11)]  # $0.01 → $0.10

# Recirculation shares to model
SHARES = [0.01, 0.05, 0.10, 0.20]

# Minimum vendor income threshold for "meaningful" monthly incentive at month 12
# Based on: any income stream that exceeds $10K/month is worth participating for
MINIMUM_MEANINGFUL_MONTHLY = 10_000

# Checkpoints for reporting
CHECKPOINTS = [12, 24, 36, 60, 120, 240]


def build_growth_profile(months: int):
    """Return list of (month, employees, credits_minted) for each month."""
    profile = []
    for t in range(1, months + 1):
        employees = INITIAL_EMPLOYEES + EMPLOYEE_GROWTH_PER_MONTH * t
        credits = employees * CREDITS_PER_EMPLOYEE
        profile.append((t, employees, credits))
    return profile


def compute_fee_metrics(fee: float, profile: list) -> dict:
    """Compute all metrics for a given fee level over the growth profile."""
    cumul_admin = 0.0
    cumul_treasury = 0.0
    results_by_month = {}

    for t, employees, monthly_credits in profile:
        monthly_admin = monthly_credits * fee
        monthly_treasury = monthly_credits * CREDIT_PRICE
        cumul_admin += monthly_admin
        cumul_treasury += monthly_treasury

        # Per-vendor income by recirculation share
        vendor_income = {s: monthly_admin * s for s in SHARES}
        cumul_vendor_income = {s: cumul_admin * s for s in SHARES}

        # Recirculation incentive gradient: extra $/month per 1% share increase
        recirc_gradient = monthly_admin * 0.01

        # Employee metrics
        effective_cost_per_credit = CREDIT_PRICE + fee
        net_purchasing_gain = PURCHASING_POWER - effective_cost_per_credit  # $
        effective_discount_rate = net_purchasing_gain / effective_cost_per_credit  # %

        results_by_month[t] = {
            "employees": employees,
            "monthly_credits": monthly_credits,
            "monthly_admin": monthly_admin,
            "cumul_admin": cumul_admin,
            "cumul_treasury": cumul_treasury,
            "vendor_income": vendor_income,
            "cumul_vendor_income": cumul_vendor_income,
            "recirc_gradient": recirc_gradient,
            "effective_cost": effective_cost_per_credit,
            "net_gain": net_purchasing_gain,
            "effective_discount_rate": effective_discount_rate,
        }

    # Vendor discount cost coverage at month 60 (5% share): how much of the discount
    # cost does admin income cover? (meaningful for vendors who can't fully recirculate)
    m60 = results_by_month.get(60, results_by_month[max(results_by_month)])
    monthly_credits_m60 = m60["monthly_credits"]
    admin_income_5pct_m60 = m60["vendor_income"][0.05]
    discount_cost_5pct_m60 = monthly_credits_m60 * 0.05 * VENDOR_DISCOUNT_COST
    coverage_ratio = (
        admin_income_5pct_m60 / discount_cost_5pct_m60
    )  # always < 1 unless fee > discount cost

    # Check minimum threshold: which month does a 5% share vendor first exceed MINIMUM_MEANINGFUL_MONTHLY?
    threshold_month = None
    for t, data in results_by_month.items():
        if data["vendor_income"][0.05] >= MINIMUM_MEANINGFUL_MONTHLY:
            threshold_month = t
            break

    return {
        "by_month": results_by_month,
        "coverage_ratio_m60": coverage_ratio,
        "threshold_month": threshold_month,
    }


def fmt_dollar(v: float) -> str:
    if abs(v) >= 1e9:
        return f"${v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.1f}K"
    return f"${v:.2f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=240)
    args = parser.parse_args()

    profile = build_growth_profile(args.months)
    all_metrics = {fee: compute_fee_metrics(fee, profile) for fee in FEE_RANGE}

    print("=" * 72)
    print("  ADBP v3 — Admin Fee Optimization Sweep")
    print(f"  Fee range: $0.01 – $0.10  |  Months: {args.months}")
    print("  Assumption: Admin fee is ADDITIONAL to $1.00 treasury inflow.")
    print("  Treasury risk = 0.00% at every fee level (structural guarantee holds).")
    print("=" * 72)

    # ── Section 1: Employee Impact ─────────────────────────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 1 — Employee Effective Cost and Net Benefit")
    print("=" * 72)
    print()
    print("  Employee pays $1.00 (treasury) + admin fee (admin pool) per credit.")
    print("  They receive $2.00 of purchasing power at vendors.")
    print("  Net benefit = $2.00 value − effective cost = purchasing gain.")
    print()
    print(
        f"  {'Fee':>6}  {'Effective Cost':>14}  {'Net Gain':>10}  {'Effective Discount':>18}  {'Employee Premium':>16}"
    )
    print("  " + "-" * 70)
    for fee in FEE_RANGE:
        effective_cost = CREDIT_PRICE + fee
        net_gain = PURCHASING_POWER - effective_cost
        discount_rate = net_gain / effective_cost * 100
        premium_over_base = fee / CREDIT_PRICE * 100
        print(
            f"  ${fee:.2f}  {fmt_dollar(effective_cost):>14}  {fmt_dollar(net_gain):>10}  {discount_rate:>17.1f}%  {premium_over_base:>15.0f}%"
        )

    print()
    print("  NOTE: Even at $0.10 (max fee), employees gain $0.90 for every $1.10 spent")
    print("  (81.8% effective discount). The fee range is imperceptible to employees")
    print("  relative to the $2.00/$1.00 amplification they're already receiving.")

    # ── Section 2: Admin Pool Size by Fee ─────────────────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 2 — Admin Pool Size at Key Checkpoints by Fee Level")
    print("=" * 72)
    print()
    print("  Cumulative admin pool at months 12, 60, 120, 240:")
    print()

    cps = [12, 60, 120, 240]
    header = f"  {'Fee':>6}  " + "  ".join(f"{'Mo.' + str(m):>14}" for m in cps)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        row = f"  ${fee:.2f}  "
        for m in cps:
            v = bm[min(m, args.months)]["cumul_admin"]
            row += f"  {fmt_dollar(v):>14}"
        print(row)

    # ── Section 3: Per-Vendor Income at 5% and 10% Share ──────────────────────
    print()
    print("=" * 72)
    print("  SECTION 3 — Monthly Admin Income for Vendor with 5% or 10% Share")
    print("=" * 72)
    print()
    print("  Monthly income by fee level at key months (5% recirculation share):")
    print()
    print(
        f"  {'Fee':>6}  "
        + "  ".join(
            f"{'Mo.' + str(m):>12}" for m in [12, 36, 60, 120, 240] if m <= args.months
        )
    )
    print("  " + "-" * 70)
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        row = f"  ${fee:.2f}  "
        for m in [12, 36, 60, 120, 240]:
            if m > args.months:
                continue
            v = bm[m]["vendor_income"][0.05]
            row += f"  {fmt_dollar(v):>12}"
        print(row)

    print()
    print("  Monthly income by fee level at key months (10% recirculation share):")
    print()
    print(
        f"  {'Fee':>6}  "
        + "  ".join(
            f"{'Mo.' + str(m):>12}" for m in [12, 36, 60, 120, 240] if m <= args.months
        )
    )
    print("  " + "-" * 70)
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        row = f"  ${fee:.2f}  "
        for m in [12, 36, 60, 120, 240]:
            if m > args.months:
                continue
            v = bm[m]["vendor_income"][0.10]
            row += f"  {fmt_dollar(v):>12}"
        print(row)

    # ── Section 4: Recirculation Incentive Gradient ────────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 4 — Recirculation Incentive Gradient")
    print("=" * 72)
    print()
    print(
        "  Gradient = extra monthly admin income per 1% increase in recirculation share."
    )
    print("  This is the behavioral incentive for vendors to grow their share.")
    print("  Higher gradient → vendors compete harder to recirculate more credits.")
    print()
    print(
        f"  {'Fee':>6}  {'Mo.12 Gradient':>16}  {'Mo.60 Gradient':>16}  {'Mo.120 Gradient':>17}  {'Mo.240 Gradient':>17}"
    )
    print("  " + "-" * 75)
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        months_to_show = [12, 60, 120, 240]
        row = f"  ${fee:.2f}  "
        for m in months_to_show:
            if m > args.months:
                row += f"  {'N/A':>16}"
                continue
            v = bm[m]["recirc_gradient"]
            row += f"  {fmt_dollar(v):>16}"
        print(row)

    # ── Section 5: Discount Cost Coverage at Month 60 ─────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 5 — Admin Fee Coverage of Vendor Discount Cost (Mo.60, 5% share)")
    print("=" * 72)
    print()
    print("  When a vendor accepts credits, their discount cost = $1.00/credit.")
    print("  Admin fee income partially offsets this for vendors who can't fully")
    print(
        "  recirculate. Coverage ratio = monthly admin income / monthly discount cost."
    )
    print(
        "  (Note: 100% recirculation eliminates discount cost — admin is pure upside.)"
    )
    print()
    print(
        f"  {'Fee':>6}  {'Admin/Mo (5% share)':>20}  {'Discount Cost/Mo':>18}  {'Coverage Ratio':>16}"
    )
    print("  " + "-" * 65)
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        m = min(60, args.months)
        admin_income = bm[m]["vendor_income"][0.05]
        monthly_credits = bm[m]["monthly_credits"]
        discount_cost = monthly_credits * 0.05 * VENDOR_DISCOUNT_COST
        coverage = admin_income / discount_cost * 100
        print(
            f"  ${fee:.2f}  {fmt_dollar(admin_income):>20}  {fmt_dollar(discount_cost):>18}  {coverage:>15.1f}%"
        )

    print()
    print(
        "  KEY: Admin fee alone cannot fully cover vendor discount cost at any fee level."
    )
    print("  Recirculation remains the primary cost recovery mechanism for vendors.")
    print("  Admin fee is a supplemental incentive — not a cost subsidy.")

    # ── Section 6: Minimum Meaningful Threshold ───────────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 6 — When Does Admin Income Become Meaningful?")
    print("=" * 72)
    print()
    print(
        f"  Threshold: ${MINIMUM_MEANINGFUL_MONTHLY:,.0f}/month for a vendor with 5% recirculation share."
    )
    print(f"  This represents minimum income that motivates vendor participation.")
    print()
    print(
        f"  {'Fee':>6}  {'Threshold Month':>15}  {'Mo.12 Income (5%)':>20}  {'Mo.12 Income (10%)':>20}"
    )
    print("  " + "-" * 65)
    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        t_month = all_metrics[fee]["threshold_month"]
        m12 = min(12, args.months)
        inc_5 = bm[m12]["vendor_income"][0.05]
        inc_10 = bm[m12]["vendor_income"][0.10]
        t_str = f"Month {t_month}" if t_month else "Never"
        print(
            f"  ${fee:.2f}  {t_str:>15}  {fmt_dollar(inc_5):>20}  {fmt_dollar(inc_10):>20}"
        )

    # ── Section 7: Composite Score and Recommendation ─────────────────────────
    print()
    print("=" * 72)
    print("  SECTION 7 — Composite Scoring and Optimal Fee Recommendation")
    print("=" * 72)
    print()
    print("  Scoring dimensions (0-100 each):")
    print(
        "    A) Vendor income adequacy  — admin income at 10% share, month 60 (normalized)"
    )
    print("    B) Recirculation incentive — gradient at month 60 (normalized)")
    print(
        "    C) Coverage ratio          — admin income vs. discount cost for partial recirculators"
    )
    print(
        "    D) Employee cost           — lower premium is better (inverted: max - fee)"
    )
    print()
    print(
        "  Weights: vendor income 35% | recirculation gradient 35% | coverage 15% | employee cost 15%"
    )
    print("  (Treasury score omitted — it is always 100% at every fee level.)")
    print()

    # Gather scores
    scores = {}
    max_vendor_income = max(
        all_metrics[fee]["by_month"][min(60, args.months)]["vendor_income"][0.10]
        for fee in FEE_RANGE
    )
    max_gradient = max(
        all_metrics[fee]["by_month"][min(60, args.months)]["recirc_gradient"]
        for fee in FEE_RANGE
    )
    max_coverage = max(all_metrics[fee]["coverage_ratio_m60"] for fee in FEE_RANGE)

    for fee in FEE_RANGE:
        bm = all_metrics[fee]["by_month"]
        m60 = min(60, args.months)

        vendor_income = bm[m60]["vendor_income"][0.10] / max_vendor_income * 100
        recirc_grad = bm[m60]["recirc_gradient"] / max_gradient * 100
        coverage = all_metrics[fee]["coverage_ratio_m60"] / max_coverage * 100
        emp_cost = (0.10 - fee) / 0.09 * 100  # higher fee = worse score for employee

        composite = (
            0.35 * vendor_income
            + 0.35 * recirc_grad
            + 0.15 * coverage
            + 0.15 * emp_cost
        )
        scores[fee] = {
            "vendor_income": vendor_income,
            "recirc_grad": recirc_grad,
            "coverage": coverage,
            "emp_cost": emp_cost,
            "composite": composite,
        }

    print(
        f"  {'Fee':>6}  {'Vendor Inc.':>12}  {'Recirc Grad.':>13}  {'Coverage':>10}  {'Emp. Cost':>10}  {'COMPOSITE':>10}"
    )
    print("  " + "-" * 68)
    best_fee = max(scores, key=lambda f: scores[f]["composite"])
    for fee in FEE_RANGE:
        s = scores[fee]
        marker = " <-- OPTIMAL" if fee == best_fee else ""
        print(
            f"  ${fee:.2f}  {s['vendor_income']:>11.1f}%  {s['recirc_grad']:>12.1f}%  "
            f"{s['coverage']:>9.1f}%  {s['emp_cost']:>9.1f}%  {s['composite']:>9.1f}%{marker}"
        )

    # ── Final Recommendation ───────────────────────────────────────────────────
    print()
    print("=" * 72)
    print("  FINAL RECOMMENDATION")
    print("=" * 72)
    print()

    # Determine category-based thresholds
    # "Adequate" vendor incentive = composite score ≥ 80
    # "Strong" = composite ≥ 90
    adequate_fees = [f for f in FEE_RANGE if scores[f]["composite"] >= 80]
    strong_fees = [f for f in FEE_RANGE if scores[f]["composite"] >= 90]
    min_adequate = min(adequate_fees) if adequate_fees else None
    min_strong = min(strong_fees) if strong_fees else None

    print(f"  Optimal fee (composite score):   ${best_fee:.2f}")
    print(
        f"  Minimum for adequate incentive:  ${min_adequate:.2f}"
        if min_adequate
        else "  Minimum for adequate: None found"
    )
    print(
        f"  Minimum for strong incentive:    ${min_strong:.2f}"
        if min_strong
        else "  Minimum for strong:   None found"
    )
    print()
    print("  Rationale:")
    print(
        f"   - Treasury risk at $0.01: 0.00% | at ${best_fee:.2f}: 0.00% | at $0.10: 0.00%"
    )
    print("     Treasury is completely decoupled from admin fee level.")
    print()
    print(f"   - Employee impact of ${best_fee:.2f} fee:")
    eff_cost = CREDIT_PRICE + best_fee
    eff_disc = (PURCHASING_POWER - eff_cost) / eff_cost * 100
    print(f"     Effective cost per $2.00 purchasing power = ${eff_cost:.2f}")
    print(
        f"     Employee effective discount = {eff_disc:.1f}% (vs. 0% with no program)"
    )
    print()
    bm = all_metrics[best_fee]["by_month"]
    m12 = min(12, args.months)
    m60 = min(60, args.months)
    m120 = min(120, args.months)
    print(f"   - Vendor income at ${best_fee:.2f} (10% recirculation share):")
    print(f"     Month  12: {fmt_dollar(bm[m12]['vendor_income'][0.10])}/month")
    print(f"     Month  60: {fmt_dollar(bm[m60]['vendor_income'][0.10])}/month")
    print(f"     Month 120: {fmt_dollar(bm[m120]['vendor_income'][0.10])}/month")
    print()
    print(
        f"   - Recirculation gradient at ${best_fee:.2f} (month 60): {fmt_dollar(bm[m60]['recirc_gradient'])}/month per 1% share"
    )
    print(
        "     Vendors have a meaningful financial incentive to maximize recirculation."
    )
    print()
    print(
        f"   - Composite score at ${best_fee:.2f}: {scores[best_fee]['composite']:.1f}/100"
    )
    print()

    # Print comparison: best_fee vs $0.10 (current) vs one below best
    compare_fees = sorted(set([best_fee, 0.10, round(max(0.01, best_fee - 0.01), 2)]))
    print("  Fee comparison — impact summary:")
    print()
    print(
        f"  {'Fee':>6}  {'Employee Disc.':>14}  {'Mo.60 Inc. 10%':>16}  {'Mo.60 Gradient':>16}  {'Composite':>10}"
    )
    print("  " + "-" * 68)
    for f in compare_fees:
        bm2 = all_metrics[f]["by_month"]
        m60v = min(60, args.months)
        eff = (PURCHASING_POWER - (CREDIT_PRICE + f)) / (CREDIT_PRICE + f) * 100
        inc = bm2[m60v]["vendor_income"][0.10]
        grad = bm2[m60v]["recirc_gradient"]
        comp = scores[f]["composite"]
        marker = " *OPTIMAL*" if f == best_fee else (" current" if f == 0.10 else "")
        print(
            f"  ${f:.2f}  {eff:>13.1f}%  {fmt_dollar(inc):>16}  {fmt_dollar(grad):>16}  {comp:>9.1f}%{marker}"
        )

    print()
    print("=" * 72)
    print("  SYSTEM RULE IMPLICATION")
    print("=" * 72)
    print()
    print(
        "  The admin fee does NOT affect treasury solvency at any level in [0.01, 0.10]."
    )
    print("  It is a pure vendor/employer incentive lever. The only tradeoffs are:")
    print("   1. Vendor income adequacy (higher = better for vendors)")
    print(
        "   2. Employee effective cost (higher = slightly more expensive for employees)"
    )
    print(
        "   3. Recirculation behavioral incentive (higher = stronger competition for share)"
    )
    print()
    print(
        "  Since the employee discount remains above 80% even at the maximum $0.10 fee,"
    )
    print(
        "  and since vendor income and recirculation incentive scale linearly with fee,"
    )
    print(
        "  the recommendation prioritizes vendor network formation over minimal employee savings."
    )
    print(
        "  A well-incentivized vendor network is the critical path to program launch."
    )


if __name__ == "__main__":
    main()
