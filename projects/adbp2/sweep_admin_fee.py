"""
sweep_admin_fee.py — Compare two admin fee funding models across cap amounts.

Option 1: Admin fees deducted from escrow every B2B cycle.
Option 2: Admin fees deducted from monthly employee fee income before it hits escrow.

Sweeps admin fee cap from $0.01 to $0.08.
"""

import sys
import simulate


class _Suppress:
    def write(self, *a):
        pass

    def flush(self):
        pass


_orig_stdout = sys.stdout

FEE_CAPS = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]


def verdict(records, failure_reason):
    if not records:
        return "NO_DATA", 0.0, 0.0
    last = records[-1]
    crr = last["crr"]
    escrow_net = last["escrow_net"]
    if failure_reason or crr < 0.35:
        return "INSOLVENT", crr, escrow_net
    elif crr < 0.40:
        return "MINT_PAUSED", crr, escrow_net
    elif crr < 0.65:
        return "STRAINED", crr, escrow_net
    elif crr > 2.0:
        return "OVERCAPITALIZED", crr, escrow_net
    return "HEALTHY ✓", crr, escrow_net


def failure_month(records, failure_reason):
    if failure_reason:
        return records[-1]["month"] if records else "—"
    return "—"


# ── Option 1: Admin fees from escrow ────────────────────────────────────────
print("=" * 76)
print("OPTION 1 — Admin fees deducted from ESCROW each B2B cycle")
print("=" * 76)
print(
    f"{'Cap':>7}  {'Final CRR':>10}  {'Escrow Net':>14}  {'Verdict':>14}  {'Fail Mo':>7}"
)
print("-" * 76)

sys.stdout = _Suppress()
opt1_results = []
for cap in FEE_CAPS:
    simulate.BURN_ADMIN_FEE_CAP = cap
    records, failure_reason = simulate.run_simulation()
    v, crr, enet = verdict(records, failure_reason)
    fm = failure_month(records, failure_reason)
    opt1_results.append((cap, crr, enet, v, fm))
sys.stdout = _orig_stdout

for cap, crr, enet, v, fm in opt1_results:
    marker = " ◄" if "HEALTHY" in v else ""
    sign = "+" if enet >= 0 else ""
    print(
        f"  ${cap:.2f}  {crr:>10.4f}  {sign}${enet:>12,.0f}  {v:>14}  {str(fm):>7}{marker}"
    )

# ── Option 2: Admin fees from fee income ────────────────────────────────────

# Patch simulate to use fee-income funded admin fees
_orig_run = simulate.run_simulation


def run_option2():
    import simulate as sim
    from constants import (
        BURN_ELIGIBLE_CRR,
        CAPACITY_RATIO,
        CRR_CRITICAL,
        CRR_MINT_PAUSE,
        CRR_OPERATIONAL_TARGET,
        CRR_OVERCAPITALIZED,
        EXPECTED_MONTHLY_MINT_PER_EMPLOYEE,
        MINT_PRICE,
        MONTHLY_INTEREST_RATE,
        MONTHLY_MINT_CAP_PER_EMPLOYEE,
        TOKEN_FACE_VALUE,
    )

    growth = sim.build_growth_curve(sim.SIMULATION_MONTHS)
    escrow_pool = 0.0
    circulating_tokens = 0.0
    failure_reason = None
    records = []

    for month_idx, employee_count in enumerate(growth):
        month = month_idx + 1

        if circulating_tokens > 0:
            pre_crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
            minting_paused = pre_crr < CRR_MINT_PAUSE
        else:
            pre_crr = 0.5
            minting_paused = False

        total_capacity = float(employee_count) * sim.VENDOR_CAPACITY_PER_EMPLOYEE
        capacity_headroom = max(
            0.0, total_capacity * CAPACITY_RATIO - circulating_tokens
        )

        if not minting_paused:
            desired_mint = float(employee_count) * EXPECTED_MONTHLY_MINT_PER_EMPLOYEE
            hard_cap = float(employee_count) * MONTHLY_MINT_CAP_PER_EMPLOYEE
            new_tokens = min(desired_mint, capacity_headroom, hard_cap)
        else:
            new_tokens = 0.0

        escrow_pool += new_tokens * MINT_PRICE
        circulating_tokens += new_tokens

        # Fee income — admin fees paid first, remainder to escrow
        fee_revenue = float(employee_count) * sim.EMPLOYEE_FEE_MONTHLY
        admin_fees_paid = min(circulating_tokens * sim.BURN_ADMIN_FEE_CAP, fee_revenue)
        escrow_pool += fee_revenue - admin_fees_paid

        # Interest on escrow
        interest_escrow = escrow_pool * MONTHLY_INTEREST_RATE
        escrow_pool += interest_escrow

        if circulating_tokens > 0:
            per_token_escrow = escrow_pool / circulating_tokens
            crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
        else:
            per_token_escrow = 0.0
            crr = 0.5

        # Burns (CRR >= 1.0 only)
        tokens_burned = 0.0
        reimbursements_paid = 0.0
        burn_rate = 0.0
        if crr >= BURN_ELIGIBLE_CRR and circulating_tokens > 0:
            annual_burn_rate = sim.dynamic_burn_rate(crr)
            burn_rate = 1.0 - (1.0 - annual_burn_rate) ** (1.0 / 12.0)
            tokens_burned = circulating_tokens * burn_rate
            reimbursements_paid = min(tokens_burned * TOKEN_FACE_VALUE, escrow_pool)
            escrow_pool -= reimbursements_paid
            circulating_tokens -= tokens_burned

        if circulating_tokens > 0:
            per_token_escrow = escrow_pool / circulating_tokens
            crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
        else:
            per_token_escrow = 0.0
            crr = 0.5

        escrow_net = escrow_pool - (circulating_tokens * TOKEN_FACE_VALUE)

        if crr < CRR_CRITICAL:
            monthly_verdict = "INSOLVENT"
        elif crr < CRR_MINT_PAUSE or minting_paused:
            monthly_verdict = "MINT_PAUSED"
        elif crr < CRR_OPERATIONAL_TARGET:
            monthly_verdict = "STRAINED"
        elif crr > CRR_OVERCAPITALIZED:
            monthly_verdict = "OVERCAPITALIZED"
        else:
            monthly_verdict = "HEALTHY"

        records.append(
            {
                "month": month,
                "employees": employee_count,
                "circulating_tokens": round(circulating_tokens),
                "escrow_pool": round(escrow_pool, 2),
                "escrow_net": round(escrow_net, 2),
                "per_token_escrow": round(per_token_escrow, 4),
                "crr": round(crr, 4),
                "burn_rate_pct": round(burn_rate * 100, 2),
                "tokens_burned": round(tokens_burned),
                "admin_fees_paid": round(admin_fees_paid, 2),
                "verdict": monthly_verdict,
            }
        )

        if crr < CRR_CRITICAL and circulating_tokens > 0:
            failure_reason = f"INSOLVENT at month {month} — CRR={crr:.3f}"
            break

    return records, failure_reason


print()
print("=" * 76)
print("OPTION 2 — Admin fees deducted from FEE INCOME (before escrow)")
print("=" * 76)
print(
    f"{'Cap':>7}  {'Final CRR':>10}  {'Escrow Net':>14}  {'Verdict':>14}  {'Fail Mo':>7}"
)
print("-" * 76)

sys.stdout = _Suppress()
opt2_results = []
for cap in FEE_CAPS:
    simulate.BURN_ADMIN_FEE_CAP = cap
    records, failure_reason = run_option2()
    v, crr, enet = verdict(records, failure_reason)
    fm = failure_month(records, failure_reason)
    opt2_results.append((cap, crr, enet, v, fm))
sys.stdout = _orig_stdout

for cap, crr, enet, v, fm in opt2_results:
    marker = " ◄" if "HEALTHY" in v else ""
    sign = "+" if enet >= 0 else ""
    print(
        f"  ${cap:.2f}  {crr:>10.4f}  {sign}${enet:>12,.0f}  {v:>14}  {str(fm):>7}{marker}"
    )

print()
print("Done.")
