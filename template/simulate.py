"""
simulate.py — System stress-test simulation.

This is the file the agent modifies. Analogous to train.py in karpathy/autoresearch.
The agent changes SCENARIO PARAMETERS, reruns, reads output, and decides whether
to keep or discard the change.

DO NOT modify constants.py — those are immutable system rules.

Usage:
    python simulate.py > run.log 2>&1
    grep "^verdict:" run.log
    grep "^primary_metric:" run.log

Output format (grep-friendly, one metric per line):
    primary_metric:    <float>
    secondary_metric:  <float>
    verdict:           <HEALTHY|WARNING|FAILURE>
    failure_reason:    <str or NONE>
"""

import io
import sys

from constants import (
    FAILURE_THRESHOLD,
    SEED_CAPITAL,
    WARNING_THRESHOLD,
    # Add additional constants as needed
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# SCENARIO PARAMETERS — The agent modifies this section.
# Each run tests one hypothesis about system behavior under stress.
# Change one or more parameters, run, observe the verdict.
# =============================================================================

SCENARIO_NAME = "Baseline — verify system runs healthy under nominal conditions"

# --- Core adoption parameters ---
INITIAL_UNITS = 500  # Starting number of users / employees / nodes / etc.
MONTHLY_GROWTH_RATE = 0.08  # Month-over-month growth rate (8% = strong growth)
SIMULATION_MONTHS = 36  # How long to simulate (36 = 3 years)

# --- Behavior parameters ---
AVG_MONTHLY_VOLUME = 350  # Average monthly volume per unit (credits, requests, etc.)
ENGAGEMENT_MULTIPLIER = 1.0  # Scale engagement up/down from baseline (1.0 = baseline)

# --- Network / supply parameters ---
NETWORK_CHURN_RATE = 0.005  # Monthly churn rate for network participants
CHURN_ACCELERATOR = 1.0  # Multiplier on churn (1.0 = baseline, 10.0 = stress test)
COMPLIANCE_RATE = 1.0  # Fraction of committed capacity actually delivered

# --- Operating costs ---
MONTHLY_OPS_COST_PHASE1 = 30_000
PHASE2_THRESHOLD = 5_000
MONTHLY_OPS_COST_PHASE2 = 200_000
PHASE3_THRESHOLD = 50_000
MONTHLY_OPS_COST_PHASE3 = 5_416_667

# =============================================================================
# SIMULATION ENGINE — Do not modify below this line.
# =============================================================================


def get_monthly_ops_cost(unit_count: float) -> float:
    if unit_count >= PHASE3_THRESHOLD:
        return MONTHLY_OPS_COST_PHASE3
    elif unit_count >= PHASE2_THRESHOLD:
        return MONTHLY_OPS_COST_PHASE2
    return MONTHLY_OPS_COST_PHASE1


def run_simulation() -> tuple[list[dict], str | None]:
    treasury = SEED_CAPITAL
    units = float(INITIAL_UNITS)
    network_capacity = 1.0 * (1.0 - NETWORK_CHURN_RATE)
    failure_reason = None
    records = []

    for month in range(1, SIMULATION_MONTHS + 1):
        # Network decay
        network_capacity *= 1.0 - (NETWORK_CHURN_RATE * CHURN_ACCELERATOR)
        network_capacity = max(network_capacity, 0.01)

        # Volume this month
        monthly_volume = (
            units * AVG_MONTHLY_VOLUME * ENGAGEMENT_MULTIPLIER * COMPLIANCE_RATE
        )

        # Revenue and costs (replace with project-specific revenue formula)
        ops_cost = get_monthly_ops_cost(units)
        revenue = ops_cost * 1.5  # TODO: replace with project-specific revenue model
        # This default ensures the baseline is HEALTHY before customization
        treasury += revenue - ops_cost

        # Unit growth
        units *= 1.0 + MONTHLY_GROWTH_RATE

        # Primary metric (replace with project-specific metric)
        primary = treasury / ops_cost if ops_cost > 0 else 999.0

        records.append(
            {
                "month": month,
                "units": int(units),
                "volume": monthly_volume,
                "treasury": treasury,
                "ops_cost": ops_cost,
                "primary": primary,
            }
        )

        if treasury < 0:
            failure_reason = f"Treasury went negative at month {month}"
            break

    return records, failure_reason


def evaluate(records: list[dict], failure_reason: str | None) -> dict:
    if not records:
        return {"verdict": "FAILURE", "failure_reason": "No records produced"}

    last = records[-1]
    primary = last["primary"]

    verdict = "HEALTHY"
    reasons = []

    if failure_reason:
        reasons.append(failure_reason)
        verdict = "FAILURE"
    if primary < FAILURE_THRESHOLD:
        reasons.append(
            f"Primary metric {primary:.2f} < {FAILURE_THRESHOLD} failure threshold"
        )
        verdict = "FAILURE"
    elif primary < WARNING_THRESHOLD and verdict != "FAILURE":
        reasons.append(
            f"Primary metric {primary:.2f} < {WARNING_THRESHOLD} warning threshold"
        )
        verdict = "WARNING"

    return {
        "primary_metric": round(primary, 2),
        "treasury_final": round(last["treasury"], 2),
        "months_simulated": len(records),
        "verdict": verdict,
        "failure_reason": "; ".join(reasons) if reasons else "NONE",
    }


if __name__ == "__main__":
    print(f"Simulation -- {SCENARIO_NAME}")
    print(
        f"Parameters: {INITIAL_UNITS} initial units, {MONTHLY_GROWTH_RATE * 100:.1f}%/mo growth"
    )
    print(f"  Avg monthly volume: {AVG_MONTHLY_VOLUME}")
    print(f"  Network churn: {NETWORK_CHURN_RATE * 100:.1f}%/mo x{CHURN_ACCELERATOR}")
    print(f"  Compliance: {COMPLIANCE_RATE * 100:.0f}%")
    print("---")

    records, failure_reason = run_simulation()
    results = evaluate(records, failure_reason)

    for key, val in results.items():
        print(f"{key}: {val}")

    print("---")
    print(f"Months simulated: {len(records)} / {SIMULATION_MONTHS}")
    if records:
        last = records[-1]
        print(
            f"Final state: {last['units']:,} units | ${last['treasury']:,.0f} treasury"
        )
