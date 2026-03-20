"""
simulate.py — ADBP v2 Token Credit System Simulation

Models solvency across the full 5-year growth lifecycle.
Agent modifies SCENARIO PARAMETERS section only.

Usage:
    python simulate.py
    python simulate.py > run.log 2>&1
    grep "^verdict:" run.log

Output format (grep-friendly):
    primary_metric:    <float>   (final CRR)
    verdict:           <HEALTHY|WARNING|FAILURE>
    failure_reason:    <str or NONE>
"""

import csv
import io
import json
import os
import sys
from constants import (
    BURN_ELIGIBLE_CRR,
    BURN_RATE_CEILING,
    BURN_RATE_FLOOR,
    CAPACITY_RATIO,
    CRR_CRITICAL,
    CRR_MINT_PAUSE,
    CRR_OPERATIONAL_TARGET,
    CRR_OVERCAPITALIZED,
    EXPECTED_MONTHLY_MINT_PER_EMPLOYEE,
    FAILURE_THRESHOLD,
    FEE_TO_ESCROW_PCT,
    FEE_TO_OPERATOR_PCT,
    GROWTH_CURVE,
    GROWTH_TARGET_EMPLOYEES,
    MINT_PRICE,
    MONTHLY_INTEREST_RATE,
    MONTHLY_MINT_CAP_PER_EMPLOYEE,
    TOKEN_FACE_VALUE,
    WARNING_THRESHOLD,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — Agent modifies this section only.
# =============================================================================

SCENARIO_NAME = "Baseline — $45/mo fee, 65% to escrow / 35% operator, burns at CRR≥1.0"

# ── Employee monthly platform fee ─────────────────────────────────────────────
EMPLOYEE_FEE_MONTHLY = 45.00  # USD per employee per month — 65% to escrow, 35% operator

# ── Vendor capacity ───────────────────────────────────────────────────────────
# Total system capacity = employees × this multiplier (approximates vendor acceptance)
VENDOR_CAPACITY_PER_EMPLOYEE = 3_000  # tokens of vendor capacity per employee in system

# ── Simulation length ─────────────────────────────────────────────────────────
SIMULATION_MONTHS = 60

# =============================================================================
# SIMULATION ENGINE — Do not modify below this line.
# =============================================================================


def build_growth_curve(months: int) -> list[int]:
    """Extend the defined growth curve to target months via exponential interpolation."""
    base = list(GROWTH_CURVE)
    if len(base) >= months:
        return base[:months]

    last_count = base[-1]
    remaining = months - len(base)
    growth_factor = (GROWTH_TARGET_EMPLOYEES / last_count) ** (1.0 / remaining)

    for i in range(1, remaining + 1):
        val = int(last_count * (growth_factor**i))
        base.append(min(val, GROWTH_TARGET_EMPLOYEES))

    return base[:months]


def dynamic_burn_rate(crr: float) -> float:
    """
    Returns ANNUAL burn rate, scaled across the burn-active CRR range (1.0 → 2.0).
    High CRR → high burn (up to ceiling). Low CRR → low burn (floor).
    Caller converts to monthly rate: monthly = 1 - (1 - annual)^(1/12)
    """
    if crr >= CRR_OVERCAPITALIZED:
        return BURN_RATE_CEILING
    normalized = (crr - BURN_ELIGIBLE_CRR) / (CRR_OVERCAPITALIZED - BURN_ELIGIBLE_CRR)
    normalized = max(0.0, min(1.0, normalized))
    return BURN_RATE_FLOOR + (BURN_RATE_CEILING - BURN_RATE_FLOOR) * normalized


def verdict_for(crr: float, minting_paused: bool) -> str:
    if crr < CRR_CRITICAL:
        return "INSOLVENT"
    if crr < CRR_MINT_PAUSE or minting_paused:
        return "MINT_PAUSED"
    if crr < CRR_OPERATIONAL_TARGET:
        return "STRAINED"
    if crr > CRR_OVERCAPITALIZED:
        return "OVERCAPITALIZED"
    return "HEALTHY"  # Burns active when CRR >= BURN_ELIGIBLE_CRR (1.0)


def run_simulation() -> tuple[list[dict], str | None]:
    growth = build_growth_curve(SIMULATION_MONTHS)

    escrow_pool = 0.0
    circulating_tokens = 0.0

    failure_reason = None
    records = []

    for month_idx, employee_count in enumerate(growth):
        month = month_idx + 1

        # ── Pre-mint CRR check ────────────────────────────────────────────────
        if circulating_tokens > 0:
            pre_crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
            minting_paused = pre_crr < CRR_MINT_PAUSE
        else:
            pre_crr = 0.5  # System start — no tokens yet, default to design CRR
            minting_paused = False

        # ── Step 1: Minting ───────────────────────────────────────────────────
        total_capacity = float(employee_count) * VENDOR_CAPACITY_PER_EMPLOYEE
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

        # ── Step 2: Employee fee collection — 65% escrow / 35% operator ────
        fee_revenue = float(employee_count) * EMPLOYEE_FEE_MONTHLY
        operator_revenue = (
            fee_revenue * FEE_TO_OPERATOR_PCT
        )  # platform revenue, leaves system
        escrow_pool += fee_revenue * FEE_TO_ESCROW_PCT

        # ── Step 3: Interest accrual ──────────────────────────────────────────
        interest_escrow = escrow_pool * MONTHLY_INTEREST_RATE
        escrow_pool += interest_escrow

        # ── Step 4: CRR and per-token escrow ─────────────────────────────────
        if circulating_tokens > 0:
            per_token_escrow = escrow_pool / circulating_tokens
            crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
        else:
            per_token_escrow = 0.0
            crr = 0.5

        # ── Step 5b: Burn events (CRR ≥ 1.0 only) ────────────────────────────
        tokens_burned = 0.0
        reimbursements_paid = 0.0
        burn_rate = 0.0

        if crr >= BURN_ELIGIBLE_CRR and circulating_tokens > 0:
            annual_burn_rate = dynamic_burn_rate(crr)
            burn_rate = 1.0 - (1.0 - annual_burn_rate) ** (1.0 / 12.0)
            tokens_burned = circulating_tokens * burn_rate

            # Vendor always receives exactly $2.00 per burned token from escrow
            reimbursements_paid = min(tokens_burned * TOKEN_FACE_VALUE, escrow_pool)
            escrow_pool -= reimbursements_paid
            circulating_tokens -= tokens_burned

        # ── Step 6: Final state ───────────────────────────────────────────────
        if circulating_tokens > 0:
            per_token_escrow = escrow_pool / circulating_tokens
            crr = escrow_pool / (circulating_tokens * TOKEN_FACE_VALUE)
        else:
            per_token_escrow = 0.0
            crr = 0.5

        escrow_net = escrow_pool - (circulating_tokens * TOKEN_FACE_VALUE)

        capacity_utilization = (
            circulating_tokens / total_capacity if total_capacity > 0 else 0.0
        )
        monthly_verdict = verdict_for(crr, minting_paused)

        records.append(
            {
                "month": month,
                "employees": employee_count,
                "new_tokens_minted": round(new_tokens),
                "circulating_tokens": round(circulating_tokens),
                "escrow_pool": round(escrow_pool, 2),
                "escrow_net": round(escrow_net, 2),
                "per_token_escrow": round(per_token_escrow, 4),
                "crr": round(crr, 4),
                "burn_rate_pct": round(burn_rate * 100, 2),
                "tokens_burned": round(tokens_burned),
                "reimbursements_paid": round(reimbursements_paid, 2),
                "operator_revenue": round(operator_revenue, 2),
                "fee_revenue": round(fee_revenue, 2),
                "interest_escrow": round(interest_escrow, 2),
                "total_capacity": round(total_capacity),
                "capacity_utilization_pct": round(capacity_utilization * 100, 2),
                "minting_paused": minting_paused,
                "verdict": monthly_verdict,
            }
        )

        # Failure check
        if crr < CRR_CRITICAL and circulating_tokens > 0:
            failure_reason = f"INSOLVENT at month {month} — CRR={crr:.3f}"
            break

    return records, failure_reason


def evaluate(records: list[dict], failure_reason: str | None) -> dict:
    if not records:
        return {"verdict": "FAILURE", "failure_reason": "No records produced"}

    last = records[-1]
    crr = last["crr"]

    if failure_reason or crr < FAILURE_THRESHOLD:
        verdict = "FAILURE"
    elif crr < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = last["verdict"]

    first_burn_month = next(
        (r["month"] for r in records if r["tokens_burned"] > 0), None
    )
    peak_crr_record = max(records, key=lambda r: r["crr"])
    burn_months = sum(1 for r in records if r["tokens_burned"] > 0)

    return {
        "primary_metric": crr,
        "verdict": verdict,
        "failure_reason": failure_reason or "NONE",
        "final_crr": round(crr, 4),
        "final_escrow_net": round(last["escrow_net"], 2),
        "final_employees": last["employees"],
        "first_burn_month": first_burn_month or "never",
        "peak_crr": peak_crr_record["crr"],
        "peak_crr_month": peak_crr_record["month"],
        "burn_active_months": burn_months,
        "months_simulated": len(records),
    }


def write_results_tsv(records: list[dict]) -> None:
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open("results.tsv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(records)


def write_json(records: list[dict]) -> None:
    os.makedirs("reports", exist_ok=True)
    with open("reports/simulation_data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def print_table(records: list[dict]) -> None:
    hdr = (
        f"{'Mo':>3} {'Employees':>10} {'Tokens':>13} {'Escrow':>15} "
        f"{'$/Tok':>7} {'CRR':>6} {'Burn%':>6} {'EscrowNet':>15} {'Verdict'}"
    )
    print("\n" + "=" * 90)
    print("ADBP v2 — Monthly Simulation Results")
    print("=" * 90)
    print(hdr)
    print("-" * 90)
    for r in records:
        crr_s = f"{r['crr']:.3f}"
        print(
            f"{r['month']:>3} {r['employees']:>10,} {r['circulating_tokens']:>13,} "
            f"${r['escrow_pool']:>13,.0f} ${r['per_token_escrow']:>5.3f} "
            f"{crr_s:>6} {r['burn_rate_pct']:>5.1f}% "
            f"${r['escrow_net']:>13,.0f} {r['verdict']}"
        )
    print("=" * 90)


def plot_charts(records: list[dict]) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        print("matplotlib not installed — skipping charts (pip install matplotlib)")
        return

    months = [r["month"] for r in records]
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle(
        f"ADBP v2 — {SCENARIO_NAME.replace('$', r'\$')}",
        fontsize=13,
        fontweight="bold",
        y=0.99,
    )
    fig.patch.set_facecolor("#0f0d1a")
    for ax_row in axes:
        for ax in ax_row:
            ax.set_facecolor("#1e1b2e")
            ax.tick_params(colors="#9ca3af")
            ax.xaxis.label.set_color("#9ca3af")
            ax.yaxis.label.set_color("#9ca3af")
            ax.title.set_color("#e5e7eb")
            for spine in ax.spines.values():
                spine.set_edgecolor("#2d2a3e")

    def fmt_m(x, _):
        if x >= 1e9:
            return f"${x / 1e9:.1f}B"
        if x >= 1e6:
            return f"${x / 1e6:.1f}M"
        if x >= 1e3:
            return f"${x / 1e3:.0f}K"
        return f"${x:.0f}"

    def fmt_count(x, _):
        if x >= 1e6:
            return f"{x / 1e6:.1f}M"
        if x >= 1e3:
            return f"{x / 1e3:.0f}K"
        return f"{x:.0f}"

    # 1. Employee growth
    ax = axes[0, 0]
    ax.plot(months, [r["employees"] for r in records], color="#8b5cf6", lw=2)
    ax.fill_between(
        months, [r["employees"] for r in records], alpha=0.15, color="#8b5cf6"
    )
    ax.set_title("Employee Growth")
    ax.set_ylabel("Employees")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_count))
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    # 2. CRR trajectory
    ax = axes[0, 1]
    crr_vals = [min(r["crr"], 2.5) for r in records]
    ax.plot(months, crr_vals, color="#38bdf8", lw=2, label="CRR")
    ax.axhline(
        BURN_ELIGIBLE_CRR,
        color="#34d399",
        ls="--",
        alpha=0.8,
        lw=1.5,
        label=f"Burn gate ({BURN_ELIGIBLE_CRR:.2f})",
    )
    ax.axhline(
        CRR_OPERATIONAL_TARGET,
        color="#f59e0b",
        ls="--",
        alpha=0.7,
        lw=1,
        label=f"Op. target ({CRR_OPERATIONAL_TARGET})",
    )
    ax.axhline(
        CRR_MINT_PAUSE,
        color="#f472b6",
        ls="--",
        alpha=0.7,
        lw=1,
        label=f"Mint pause ({CRR_MINT_PAUSE})",
    )
    ax.axhline(
        CRR_CRITICAL,
        color="#ef4444",
        ls="--",
        alpha=0.7,
        lw=1,
        label=f"Critical ({CRR_CRITICAL})",
    )
    ax.set_title("Cash Reserve Ratio (CRR)")
    ax.set_ylabel("CRR")
    ax.legend(fontsize=7, facecolor="#1e1b2e", labelcolor="#e5e7eb")
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    # 3. Escrow pool vs treasury
    ax = axes[1, 0]
    ax.plot(
        months,
        [r["escrow_pool"] for r in records],
        color="#38bdf8",
        lw=2,
        label="Escrow",
    )
    ax.plot(
        months,
        [r["escrow_net"] for r in records],
        color="#34d399",
        lw=2,
        label="Escrow Net (buffer)",
    )
    ax.axhline(
        0, color="#f472b6", ls="--", alpha=0.6, lw=1, label="Zero (fully obligated)"
    )
    ax.set_title("Escrow Pool vs Net Buffer (USD)")
    ax.set_ylabel("USD")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_m))
    ax.legend(fontsize=8, facecolor="#1e1b2e", labelcolor="#e5e7eb")
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    # 4. Per-token escrow (burn eligibility line)
    ax = axes[1, 1]
    ax.plot(months, [r["per_token_escrow"] for r in records], color="#f59e0b", lw=2)
    ax.axhline(
        TOKEN_FACE_VALUE,
        color="#34d399",
        ls="--",
        alpha=0.9,
        lw=1.5,
        label=f"Burn eligible (${TOKEN_FACE_VALUE:.2f})",
    )
    ax.set_title("Per-Token Escrow Backing ($)")
    ax.set_ylabel("USD / Token")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.2f}"))
    ax.legend(fontsize=8, facecolor="#1e1b2e", labelcolor="#e5e7eb")
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    # 5. Dynamic burn rate
    ax = axes[2, 0]
    ax.plot(months, [r["burn_rate_pct"] for r in records], color="#f472b6", lw=2)
    ax.fill_between(
        months, [r["burn_rate_pct"] for r in records], alpha=0.15, color="#f472b6"
    )
    ax.axhline(
        BURN_RATE_FLOOR * 100,
        color="#9ca3af",
        ls="--",
        alpha=0.5,
        lw=1,
        label="Floor 2%",
    )
    ax.axhline(
        BURN_RATE_CEILING * 100,
        color="#9ca3af",
        ls=":",
        alpha=0.5,
        lw=1,
        label="Ceiling 15%",
    )
    ax.set_title("Dynamic Burn Rate (%)")
    ax.set_ylabel("Burn Rate (%)")
    ax.legend(fontsize=8, facecolor="#1e1b2e", labelcolor="#e5e7eb")
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    # 6. Monthly escrow inflow vs admin fees
    ax = axes[2, 1]
    ax.stackplot(
        months,
        [r["fee_revenue"] for r in records],
        [r["interest_escrow"] for r in records],
        labels=["Fee income", "Interest"],
        colors=["#8b5cf6", "#38bdf8"],
        alpha=0.8,
    )
    ax.plot(
        months,
        [r["admin_fees_paid"] for r in records],
        color="#f472b6",
        lw=2,
        label="Admin fees out",
    )
    ax.set_title("Monthly Escrow Inflow vs Admin Fees (USD)")
    ax.set_ylabel("USD")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_m))
    ax.legend(fontsize=7, facecolor="#1e1b2e", labelcolor="#e5e7eb")
    ax.grid(True, alpha=0.2, color="#2d2a3e")

    for ax_row in axes:
        for ax in ax_row:
            ax.set_xlabel("Month", color="#9ca3af")

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    os.makedirs("reports", exist_ok=True)
    out = "reports/simulation_charts.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0f0d1a")
    print(f"\n  Charts saved → {out}")
    plt.show()


if __name__ == "__main__":
    print("\nADBP v2 Simulation")
    print(f"Scenario: {SCENARIO_NAME}")
    print(
        f"  Fee: ${EMPLOYEE_FEE_MONTHLY}/mo → {FEE_TO_ESCROW_PCT * 100:.0f}% escrow / {FEE_TO_OPERATOR_PCT * 100:.0f}% operator"
    )
    print(f"  Burn: vendor=$2.00/token reimbursed from escrow at CRR≥1.0")
    print(f"  Months: {SIMULATION_MONTHS}")
    print("-" * 60)

    records, failure_reason = run_simulation()
    results = evaluate(records, failure_reason)

    print_table(records)

    print("\nKey Metrics:")
    for k, v in results.items():
        print(f"  {k}: {v}")

    write_results_tsv(records)
    write_json(records)

    print(f"\nverdict: {results['verdict']}")
    print(f"primary_metric: {results['primary_metric']}")
    print(f"failure_reason: {results['failure_reason']}")

    print("\nWriting output files...")
    print("  results.tsv")
    print("  reports/simulation_data.json")

    plot_charts(records)


# =============================================================================
# RUST ENGINE DELEGATION — Do not modify. Added by the MC build pipeline.
# =============================================================================
# When the adbp2_mc Rust extension is available, replace run_simulation() and
# evaluate() with thin wrappers that delegate to Rust. Falls back to the pure-
# Python implementations above if the extension is not built.
#
# This block runs at module-import time, so any caller of run_simulation() or
# evaluate() — including the __main__ block above — automatically uses Rust
# when it is available.
# =============================================================================


def _make_params_dict() -> dict:
    """Pack current module-level SCENARIO PARAMETERS + constants into a dict.

    Imports constants directly to be self-contained when called from any context
    (including exec'd namespaces in tests).
    """
    import constants as _c

    return {
        "employee_fee_monthly": EMPLOYEE_FEE_MONTHLY,
        "vendor_capacity_per_employee": VENDOR_CAPACITY_PER_EMPLOYEE,
        "simulation_months": SIMULATION_MONTHS,
        "token_face_value": _c.TOKEN_FACE_VALUE,
        "mint_price": _c.MINT_PRICE,
        "escrow_start_per_token": _c.ESCROW_START_PER_TOKEN,
        "burn_eligible_crr": _c.BURN_ELIGIBLE_CRR,
        "burn_rate_floor": _c.BURN_RATE_FLOOR,
        "burn_rate_ceiling": _c.BURN_RATE_CEILING,
        "fee_to_operator_pct": _c.FEE_TO_OPERATOR_PCT,
        "crr_operational_target": _c.CRR_OPERATIONAL_TARGET,
        "crr_mint_pause": _c.CRR_MINT_PAUSE,
        "crr_critical": _c.CRR_CRITICAL,
        "crr_overcapitalized": _c.CRR_OVERCAPITALIZED,
        "capacity_ratio": _c.CAPACITY_RATIO,
        "monthly_mint_cap_per_employee": float(_c.MONTHLY_MINT_CAP_PER_EMPLOYEE),
        "expected_monthly_mint_per_employee": float(
            _c.EXPECTED_MONTHLY_MINT_PER_EMPLOYEE
        ),
        "annual_interest_rate": _c.ANNUAL_INTEREST_RATE,
        "monthly_interest_rate": _c.ANNUAL_INTEREST_RATE / 12.0,
        "growth_curve": list(_c.GROWTH_CURVE),
        "growth_target_employees": _c.GROWTH_TARGET_EMPLOYEES,
        "failure_threshold": _c.FAILURE_THRESHOLD,
        "warning_threshold": _c.WARNING_THRESHOLD,
    }


try:
    import adbp2_mc as _adbp2_mc  # type: ignore[import]

    _rust_run_simulation = _adbp2_mc.run_simulation
    _rust_evaluate = _adbp2_mc.evaluate

    # Keep a reference to the original Python implementations
    _py_run_simulation = run_simulation
    _py_evaluate = evaluate

    def run_simulation():  # type: ignore[misc]  # noqa: F811
        """Rust-backed run_simulation(). Falls back to Python if Rust unavailable."""
        params = _make_params_dict()
        result = _rust_run_simulation(params)
        records = result["records"]
        failure_reason = result.get("failure_reason")
        return records, failure_reason

    def evaluate(records, failure_reason):  # type: ignore[misc]  # noqa: F811
        """Rust-backed evaluate(). Falls back to Python if Rust unavailable."""
        params = _make_params_dict()
        sim_result = {"records": records, "failure_reason": failure_reason}
        return _rust_evaluate(sim_result, params)

except ImportError:
    pass  # Pure-Python implementations above remain in effect
