"""
sweep_split.py — Sweep escrow/treasury fee split to find HEALTHY threshold.

Tests FEE_TO_ESCROW_PCT from 50% to 95% in 5% steps.
Also sweeps employee fee ($35–$65) at the optimal split for context.
"""

import sys

import simulate


# Suppress simulate.py stdout during sweep
class _Suppress:
    def write(self, *a):
        pass

    def flush(self):
        pass


CRR_OPERATIONAL_TARGET = 0.65  # HEALTHY threshold

# ── Sweep 1: escrow split at fixed $45/mo fee ────────────────────────────────

print("=" * 72)
print("SWEEP 1 — Escrow Split  |  Fee fixed at $45/mo")
print("=" * 72)
print(
    f"{'Escrow%':>8}  {'Treasury%':>10}  {'Final CRR':>10}  {'Peak CRR':>9}  {'Verdict':>14}  {'Treasury $B':>12}"
)
print("-" * 72)

_orig_stdout = sys.stdout
sys.stdout = _Suppress()

split_results = []
for escrow_pct_int in range(50, 96, 5):
    escrow_pct = escrow_pct_int / 100.0
    treasury_pct = round(1.0 - escrow_pct, 10)

    simulate.FEE_TO_ESCROW_PCT = escrow_pct
    simulate.FEE_TO_TREASURY_PCT = treasury_pct
    simulate.EMPLOYEE_FEE_MONTHLY = 45.0

    records, failure_reason = simulate.run_simulation()
    last = records[-1]
    crr = last["crr"]
    peak_crr = max(r["crr"] for r in records)
    treasury = last["treasury_balance"]

    if failure_reason or crr < 0.35:
        verdict = "INSOLVENT"
    elif crr < 0.40:
        verdict = "MINT_PAUSED"
    elif crr < 0.65:
        verdict = "STRAINED"
    elif crr > 2.0:
        verdict = "OVERCAPITALIZED"
    else:
        verdict = "HEALTHY ✓"

    split_results.append(
        (escrow_pct_int, treasury_pct * 100, crr, peak_crr, verdict, treasury)
    )

sys.stdout = _orig_stdout

for escrow_pct_int, treasury_pct, crr, peak_crr, verdict, treasury in split_results:
    marker = " ◄" if "HEALTHY" in verdict else ""
    print(
        f"{escrow_pct_int:>7}%  {treasury_pct:>9.0f}%  {crr:>10.4f}  {peak_crr:>9.4f}  {verdict:>14}  ${treasury / 1e9:>10.2f}B{marker}"
    )

# Find crossover
healthy = [r for r in split_results if "HEALTHY" in r[4]]
strained = [r for r in split_results if "STRAINED" in r[4]]

print()
if healthy:
    first_healthy = healthy[0]
    print(
        f"→ HEALTHY threshold: {first_healthy[0]}% escrow / {first_healthy[1]:.0f}% treasury"
    )
    print(
        f"  Final CRR: {first_healthy[2]:.4f}  |  Treasury at month 60: ${first_healthy[5] / 1e9:.2f}B"
    )
else:
    closest = max(split_results, key=lambda r: r[2])
    print(
        f"→ HEALTHY not reached. Closest: {closest[0]}% escrow → CRR {closest[2]:.4f} (need 0.65)"
    )
    print(f"  Gap to HEALTHY: {0.65 - closest[2]:.4f}")

# ── Sweep 2: fee amount at best split found ───────────────────────────────────

best_escrow = healthy[0][0] if healthy else max(split_results, key=lambda r: r[2])[0]
best_treasury = 100 - best_escrow

print()
print("=" * 72)
print(f"SWEEP 2 — Monthly Fee  |  Split fixed at {best_escrow}/{best_treasury}")
print("=" * 72)
print(
    f"{'Fee/mo':>8}  {'Final CRR':>10}  {'Peak CRR':>9}  {'Verdict':>14}  {'Treasury $B':>12}"
)
print("-" * 72)

simulate.FEE_TO_ESCROW_PCT = best_escrow / 100.0
simulate.FEE_TO_TREASURY_PCT = best_treasury / 100.0

sys.stdout = _Suppress()

fee_results = []
for fee in range(35, 71, 5):
    simulate.EMPLOYEE_FEE_MONTHLY = float(fee)
    records, failure_reason = simulate.run_simulation()
    last = records[-1]
    crr = last["crr"]
    peak_crr = max(r["crr"] for r in records)
    treasury = last["treasury_balance"]

    if failure_reason or crr < 0.35:
        verdict = "INSOLVENT"
    elif crr < 0.40:
        verdict = "MINT_PAUSED"
    elif crr < 0.65:
        verdict = "STRAINED"
    elif crr > 2.0:
        verdict = "OVERCAPITALIZED"
    else:
        verdict = "HEALTHY ✓"

    fee_results.append((fee, crr, peak_crr, verdict, treasury))

sys.stdout = _orig_stdout

for fee, crr, peak_crr, verdict, treasury in fee_results:
    marker = " ◄" if "HEALTHY" in verdict else ""
    print(
        f"  ${fee:>5}/mo  {crr:>10.4f}  {peak_crr:>9.4f}  {verdict:>14}  ${treasury / 1e9:>10.2f}B{marker}"
    )

print()
print("Done.")
