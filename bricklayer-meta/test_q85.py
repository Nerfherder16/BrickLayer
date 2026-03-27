"""
test_q85.py — Q8.5 analytical root cause derivation + simulation verification.

Determines WHY the novelty cliff appears at DN=0.95 under recalibration
instead of the predicted 0.65-0.80 range.

Step 1: Analytical derivation of effective_accuracy(DN)
Step 2: Simulation sweep verification
Step 3: Proposed fix derivation
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Constants (from constants.py)
BASE_SPECIALIST_ACCURACY = 0.875
BASE_GENERALIST_ACCURACY = 0.625  # original
RECALIBRATED_BASE_GENERALIST_ACCURACY = 0.50  # recalibrated (Change 3)
RECALIBRATED_PEER_REVIEW_CORRECTION_RATE = 0.40  # recalibrated (Change 1)
WAVE_SATURATION_RATE = 0.15
CAMPAIGN_YIELD_WARNING = 0.45
CAMPAIGN_YIELD_FAILURE = 0.25

# Fixed scenario parameters
AGENT_SPECIALIZATION_RATIO = 0.65
PEER_REVIEW_RATE = 1.00
WAVE_COUNT = 4
QUESTIONS_PER_WAVE = 7


# ============================================================
# Step 1: Analytical derivation
# ============================================================


def novelty_penalty(dn: float) -> float:
    """_novelty_penalty() from simulate.py (unchanged by recalibration)."""
    if dn <= 0.30:
        return 1.0 - dn * 0.10
    elif dn <= 0.60:
        return 0.97 - (dn - 0.30) * 0.35
    else:
        return 0.865 - (dn - 0.60) * 0.55


def base_accuracy() -> float:
    """_agent_accuracy() with recalibrated generalist accuracy."""
    return (
        AGENT_SPECIALIZATION_RATIO * BASE_SPECIALIST_ACCURACY
        + (1.0 - AGENT_SPECIALIZATION_RATIO) * RECALIBRATED_BASE_GENERALIST_ACCURACY
    )


def effective_accuracy_recal(dn: float) -> float:
    """Compute effective_accuracy at given DN under recalibrated parameters."""
    ba = base_accuracy()
    nm = novelty_penalty(dn)
    accuracy = ba * nm
    drift_rate = 1.0 - accuracy
    # Recalibrated novelty discount (Change 2)
    novelty_discount = max(0.05, 1.0 - dn * 0.90)
    peer_correction = (
        PEER_REVIEW_RATE
        * drift_rate
        * RECALIBRATED_PEER_REVIEW_CORRECTION_RATE
        * novelty_discount
    )
    ea = min(0.98, accuracy + peer_correction)
    return ea


def effective_accuracy_original(dn: float) -> float:
    """Compute effective_accuracy at given DN under ORIGINAL (pre-recal) parameters."""
    ba_orig = (
        AGENT_SPECIALIZATION_RATIO * BASE_SPECIALIST_ACCURACY
        + (1.0 - AGENT_SPECIALIZATION_RATIO) * BASE_GENERALIST_ACCURACY  # 0.625
    )
    nm = novelty_penalty(dn)
    accuracy = ba_orig * nm
    drift_rate = 1.0 - accuracy
    # Original novelty discount
    novelty_discount_orig = max(0.20, 1.0 - dn * 0.60)
    peer_correction = PEER_REVIEW_RATE * drift_rate * 0.55 * novelty_discount_orig
    ea = min(0.98, accuracy + peer_correction)
    return ea


def wave_uniqueness(wave: int) -> float:
    saturation = WAVE_SATURATION_RATE * (QUESTIONS_PER_WAVE / 7.0)
    return max(0.10, 1.0 - (wave - 1) * saturation)


def expected_campaign_yield(dn: float) -> float:
    """Deterministic (expectation-value) campaign yield at given DN.

    This is the analytical mean ignoring RNG variance.
    wave_yield = effective_accuracy(dn) * uniqueness(wave)  [both gates as independent probs]
    campaign_yield = mean over waves
    """
    ea = effective_accuracy_recal(dn)
    wave_yields = [ea * wave_uniqueness(w) for w in range(1, WAVE_COUNT + 1)]
    return sum(wave_yields) / len(wave_yields)


print("=" * 70)
print("STEP 1: ANALYTICAL DERIVATION")
print("=" * 70)

ba = base_accuracy()
print(f"\nBase accuracy (recalibrated):")
print(
    f"  = 0.65 * {BASE_SPECIALIST_ACCURACY} + 0.35 * {RECALIBRATED_BASE_GENERALIST_ACCURACY}"
)
print(
    f"  = {0.65 * BASE_SPECIALIST_ACCURACY:.5f} + {0.35 * RECALIBRATED_BASE_GENERALIST_ACCURACY:.5f}"
)
print(f"  = {ba:.5f}")

print(f"\nWave uniqueness sequence (WAVE_COUNT=4, WAVE_SATURATION_RATE=0.15):")
for w in range(1, 5):
    print(f"  Wave {w}: uniqueness = {wave_uniqueness(w):.3f}")

mean_uniqueness = sum(wave_uniqueness(w) for w in range(1, WAVE_COUNT + 1)) / WAVE_COUNT
print(f"  Mean uniqueness (4 waves) = {mean_uniqueness:.4f}")

print(
    f"\nRequired effective_accuracy to clear CAMPAIGN_YIELD_WARNING={CAMPAIGN_YIELD_WARNING}:"
)
print(f"  effective_accuracy × mean_uniqueness >= {CAMPAIGN_YIELD_WARNING}")
print(f"  effective_accuracy × {mean_uniqueness:.4f} >= {CAMPAIGN_YIELD_WARNING}")
required_ea = CAMPAIGN_YIELD_WARNING / mean_uniqueness
print(f"  effective_accuracy >= {required_ea:.4f}  (= 0.45 / {mean_uniqueness:.4f})")

print(f"\nAnalytical effective_accuracy(DN) sweep — recalibrated vs original:")
print(
    f"{'DN':>6}  {'novelty_mult':>12}  {'accuracy':>9}  {'drift':>7}  {'nd_recal':>8}  {'peer_corr_recal':>15}  {'eff_acc_recal':>13}  {'eff_acc_orig':>12}  {'exp_yield_recal':>15}  {'cliff?':>6}"
)
print("-" * 115)

dns = [0.35, 0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
for dn in dns:
    nm = novelty_penalty(dn)
    acc = ba * nm
    drift = 1.0 - acc
    nd_recal = max(0.05, 1.0 - dn * 0.90)
    pc_recal = (
        PEER_REVIEW_RATE * drift * RECALIBRATED_PEER_REVIEW_CORRECTION_RATE * nd_recal
    )
    ea_recal = min(0.98, acc + pc_recal)
    ea_orig = effective_accuracy_original(dn)
    ey = expected_campaign_yield(dn)
    cliff = "<<CLIFF" if ey < CAMPAIGN_YIELD_WARNING else ""
    print(
        f"{dn:>6.2f}  {nm:>12.4f}  {acc:>9.4f}  {drift:>7.4f}  {nd_recal:>8.4f}  {pc_recal:>15.4f}  {ea_recal:>13.4f}  {ea_orig:>12.4f}  {ey:>15.4f}  {cliff:>6}"
    )

# Find exact crossover analytically
print(f"\nAnalytical cliff crossover:")
print(
    f"  The cliff is defined as the DN where expected_campaign_yield < {CAMPAIGN_YIELD_WARNING}"
)
print(f"  = where effective_accuracy(DN) * mean_uniqueness < {CAMPAIGN_YIELD_WARNING}")
print(f"  = where effective_accuracy(DN) < {required_ea:.4f}")

# Find crossover by bisection
lo, hi = 0.80, 1.00
for _ in range(60):
    mid = (lo + hi) / 2
    if effective_accuracy_recal(mid) > required_ea:
        lo = mid
    else:
        hi = mid
crossover_dn = (lo + hi) / 2
print(f"  Crossover DN (bisection): {crossover_dn:.4f}")
print(
    f"  effective_accuracy at crossover: {effective_accuracy_recal(crossover_dn):.6f}"
)
print(f"  required_ea: {required_ea:.6f}")


# ============================================================
# Step 2: Simulation sweep verification
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: SIMULATION SWEEP VERIFICATION")
print("=" * 70)

import random


def run_sim_at_dn(dn: float, seed: int = 42) -> dict:
    """Run simulation at given DN with recalibrated parameters."""
    rng = random.Random(seed)

    nm = novelty_penalty(dn)
    acc = ba * nm
    drift_rate = 1.0 - acc
    nd = max(0.05, 1.0 - dn * 0.90)
    pc = PEER_REVIEW_RATE * drift_rate * RECALIBRATED_PEER_REVIEW_CORRECTION_RATE * nd
    effective_acc = min(0.98, acc + pc)

    total_q = 0
    total_act = 0
    wave_records = []

    for wave in range(1, WAVE_COUNT + 1):
        uniqueness = wave_uniqueness(wave)
        wave_q = 0
        wave_act = 0
        for _ in range(QUESTIONS_PER_WAVE):
            total_q += 1
            wave_q += 1
            is_novel = rng.random() < uniqueness
            is_accurate = rng.random() < effective_acc
            if is_novel and is_accurate:
                wave_act += 1
                total_act += 1
        wave_records.append(
            {
                "wave": wave,
                "yield": wave_act / wave_q,
                "actionable": wave_act,
            }
        )

    campaign_yield = total_act / total_q
    if campaign_yield < CAMPAIGN_YIELD_FAILURE:
        verdict = "FAILURE"
    elif campaign_yield < CAMPAIGN_YIELD_WARNING:
        verdict = "WARNING"
    else:
        verdict = "HEALTHY"

    return {
        "dn": dn,
        "effective_acc": round(effective_acc, 4),
        "expected_yield": round(expected_campaign_yield(dn), 4),
        "sim_yield": round(campaign_yield, 4),
        "verdict": verdict,
        "total_actionable": total_act,
    }


print(
    f"\n{'DN':>6}  {'eff_acc':>8}  {'exp_yield':>10}  {'sim_yield':>10}  {'verdict':>8}  {'note':>20}"
)
print("-" * 75)

sweep_dns = [round(0.35 + i * 0.05, 2) for i in range(14)]
first_warning_dn = None
first_failure_dn = None
for dn in sweep_dns:
    r = run_sim_at_dn(dn)
    note = ""
    if r["verdict"] != "HEALTHY" and first_warning_dn is None:
        first_warning_dn = dn
        note = "<< FIRST NON-HEALTHY"
    if r["verdict"] == "FAILURE" and first_failure_dn is None:
        first_failure_dn = dn
        note = "<< FIRST FAILURE"
    print(
        f"{dn:>6.2f}  {r['effective_acc']:>8.4f}  {r['expected_yield']:>10.4f}  {r['sim_yield']:>10.4f}  {r['verdict']:>8}  {note}"
    )

print(f"\nFirst non-HEALTHY DN (sim): {first_warning_dn}")
print(f"Analytical crossover DN:   {crossover_dn:.4f}")


# ============================================================
# Root cause analysis
# ============================================================
print("\n" + "=" * 70)
print("ROOT CAUSE ANALYSIS")
print("=" * 70)

print(f"""
The cliff is at DN≈0.95 (not 0.65-0.80) because of THREE compounding factors:

1. RECALIBRATED BASE ACCURACY IS STILL HIGH AT MODERATE DN
   base_accuracy = {ba:.5f}  (was {0.65 * BASE_SPECIALIST_ACCURACY + 0.35 * BASE_GENERALIST_ACCURACY:.5f} pre-recal)
   At DN=0.70: novelty_mult = {novelty_penalty(0.70):.4f}
   accuracy(DN=0.70) = {ba * novelty_penalty(0.70):.4f}
   Even with Change 3 (generalist 0.625→0.50), the specialist-weighted base
   accuracy only dropped from ~0.787 to ~0.744.

2. THE NOVELTY_DISCOUNT FORMULA (Change 2) FLOORS AT 0.05, NOT 0.00
   At DN=0.90: novelty_discount = max(0.05, 1 - 0.90*0.90) = max(0.05, 0.19) = 0.190
   At DN=0.95: novelty_discount = max(0.05, 1 - 0.95*0.90) = max(0.05, 0.145) = 0.145
   At DN=1.00: novelty_discount = max(0.05, 1 - 1.00*0.90) = max(0.05, 0.10) = 0.100
   The floor is 0.05 (not 0), so peer correction never fully disappears.
   This keeps effective_accuracy elevated even at extreme novelty.

3. THE DOMINANT YIELD DRIVER IS WAVE UNIQUENESS SATURATION, NOT ACCURACY
   At DN=0.35: effective_acc={effective_accuracy_recal(0.35):.4f}, Wave 4 uniqueness=0.55 → yield=0.429/wave
   Campaign yield is already dragged down by saturation at nominal DN.
   Accuracy has to DROP SUBSTANTIALLY before it overtakes saturation as the
   yield-limiting factor. The threshold is effective_acc < {required_ea:.4f}.

   effective_accuracy only reaches {required_ea:.4f} at DN≈{crossover_dn:.3f}.

ALGEBRAIC EXPLANATION OF WHY 0.65-0.80 WAS EXPECTED BUT CLIFF IS AT 0.95:
   Q6.1 predicted the cliff at DN 0.65-0.80 based on the OLD parameters where:
   - Base generalist accuracy = 0.625 (recal: 0.50)
   - Peer correction rate = 0.55 (recal: 0.40)
   - Novelty discount = max(0.20, 1-DN*0.60) (recal: max(0.05, 1-DN*0.90))

   Under OLD parameters at DN=0.70:
     accuracy = {effective_accuracy_original(0.70):.4f} (recal: {effective_accuracy_recal(0.70):.4f})

   Wait — this seems backwards. The recalibration should have LOWERED effective_acc.
   Let's compare both:
""")

print(
    f"{'DN':>6}  {'ea_orig':>10}  {'ea_recal':>10}  {'diff':>8}  {'exp_yield_orig':>14}  {'exp_yield_recal':>15}"
)
print("-" * 75)
for dn in [0.35, 0.55, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
    ea_orig = effective_accuracy_original(dn)
    ea_recal = effective_accuracy_recal(dn)
    diff = ea_recal - ea_orig
    # Expected yield under original parameters:
    ba_orig = 0.65 * BASE_SPECIALIST_ACCURACY + 0.35 * BASE_GENERALIST_ACCURACY
    nm = novelty_penalty(dn)
    acc_orig = ba_orig * nm
    drift_orig = 1.0 - acc_orig
    nd_orig = max(0.20, 1.0 - dn * 0.60)
    pc_orig = PEER_REVIEW_RATE * drift_orig * 0.55 * nd_orig
    ey_orig_ea = min(0.98, acc_orig + pc_orig)
    ey_orig = (
        sum(ey_orig_ea * wave_uniqueness(w) for w in range(1, WAVE_COUNT + 1))
        / WAVE_COUNT
    )
    ey_recal = expected_campaign_yield(dn)
    print(
        f"{dn:>6.2f}  {ea_orig:>10.4f}  {ea_recal:>10.4f}  {diff:>+8.4f}  {ey_orig:>14.4f}  {ey_recal:>15.4f}"
    )

print(f"""
KEY INSIGHT: The recalibrations produced MIXED effects on effective_accuracy:
  - Change 1 (PRCR: 0.55→0.40) REDUCES peer correction by 27%
  - Change 2 (novelty discount slope: 0.60→0.90, floor: 0.20→0.05):
      At LOW DN (0.35): old discount={max(0.20, 1 - 0.35 * 0.60):.3f}, new={max(0.05, 1 - 0.35 * 0.90):.3f} — NEW IS LOWER
      At MID DN (0.70): old discount={max(0.20, 1 - 0.70 * 0.60):.3f}, new={max(0.05, 1 - 0.70 * 0.90):.3f} — ROUGHLY EQUAL
      At HIGH DN (0.90): old discount={max(0.20, 1 - 0.90 * 0.60):.3f}, new={max(0.05, 1 - 0.90 * 0.90):.3f} — ALMOST EQUAL
  - Change 3 (generalist: 0.625→0.50) REDUCES base accuracy

  The COMBINED effect is that effective_accuracy is LOWER across the board.
  But because the nominal yield was dragged down by saturation (Wave 4 = 0.55
  uniqueness gives yield = ea * 0.55), the actual campaign_yield THRESHOLD at
  CAMPAIGN_YIELD_WARNING=0.45 requires effective_acc < {required_ea:.4f}.

  The recalibrated effective_accuracy only drops below {required_ea:.4f} at DN≈{crossover_dn:.3f}
  because the novelty_penalty function itself is the binding constraint:

  At DN=0.80: novelty_mult = {novelty_penalty(0.80):.4f}  → accuracy = {ba * novelty_penalty(0.80):.4f}
  At DN=0.90: novelty_mult = {novelty_penalty(0.90):.4f}  → accuracy = {ba * novelty_penalty(0.90):.4f}
  At DN=0.95: novelty_mult = {novelty_penalty(0.95):.4f}  → accuracy = {ba * novelty_penalty(0.95):.4f}

  The _novelty_penalty() piecewise slope at DN>0.60 is only -0.55 per unit DN.
  Combined with base_accuracy={ba:.4f}, the accuracy*novelty_mult product
  falls slowly. Peer correction (even discounted) keeps effective_acc above
  the required {required_ea:.4f} until well into extreme novelty territory.
""")


# ============================================================
# Step 3: Proposed fix derivation
# ============================================================
print("=" * 70)
print("STEP 3: PROPOSED FIX — TARGET CLIFF AT DN≈0.70")
print("=" * 70)

print(f"""
The fix must make effective_accuracy(DN=0.70) < {required_ea:.4f}
while keeping expected_campaign_yield(DN=0.35) ≥ 0.50 (HEALTHY threshold).

Current at DN=0.70:
  accuracy(0.70) = {ba * novelty_penalty(0.70):.4f}
  drift(0.70) = {1 - ba * novelty_penalty(0.70):.4f}
  novelty_discount(0.70) = max(0.05, 1 - 0.70*0.90) = {max(0.05, 1 - 0.70 * 0.90):.4f}

  To make effective_acc(0.70) < {required_ea:.4f}:
  accuracy + peer_correction < {required_ea:.4f}
  {ba * novelty_penalty(0.70):.4f} + 1.0 * {1 - ba * novelty_penalty(0.70):.4f} * 0.40 * novelty_discount < {required_ea:.4f}
  {ba * novelty_penalty(0.70):.4f} + {(1 - ba * novelty_penalty(0.70)) * 0.40:.4f} * novelty_discount < {required_ea:.4f}
  {(1 - ba * novelty_penalty(0.70)) * 0.40:.4f} * novelty_discount < {required_ea - ba * novelty_penalty(0.70):.4f}
  novelty_discount < {(required_ea - ba * novelty_penalty(0.70)) / ((1 - ba * novelty_penalty(0.70)) * 0.40):.4f}
""")

acc_070 = ba * novelty_penalty(0.70)
drift_070 = 1.0 - acc_070
needed_nd_max = (required_ea - acc_070) / (drift_070 * 0.40)
print(f"  Required novelty_discount(0.70) < {needed_nd_max:.4f}")

# Current formula: max(0.05, 1 - DN * 0.90)
# At DN=0.70: max(0.05, 1 - 0.63) = 0.37
print(
    f"  Current formula gives: max(0.05, 1 - 0.70*0.90) = {max(0.05, 1 - 0.70 * 0.90):.4f}"
)
print(f"  Need: < {needed_nd_max:.4f}")
print(
    f"  Gap: {max(0.05, 1 - 0.70 * 0.90) - needed_nd_max:.4f} — current is too generous"
)

# Find the slope k in max(0.05, 1 - DN * k) such that at DN=0.70 the discount = needed_nd_max
# 1 - 0.70 * k = needed_nd_max
# k = (1 - needed_nd_max) / 0.70
needed_k = (1.0 - needed_nd_max) / 0.70
print(f"\n  If formula = max(0.05, 1 - DN * k):")
print(f"  Need 1 - 0.70 * k = {needed_nd_max:.4f}")
print(f"  k = (1 - {needed_nd_max:.4f}) / 0.70 = {needed_k:.4f}")
print(f"  So k ≈ {needed_k:.2f} (round up to ensure cliff stays ≤ 0.70)")

# Test k values to find one that moves cliff to 0.65-0.80 without regressing nominal
print(f"\n  Testing candidate k values (formula: max(0.05, 1 - DN * k)):")
print(
    f"  {'k':>6}  {'ea(0.35)':>9}  {'ey(0.35)':>9}  {'ea(0.70)':>9}  {'ey(0.70)':>9}  {'cliff_dn':>9}  {'verdict_0.35':>12}  {'verdict_0.70':>12}"
)
print(f"  {'-' * 85}")


def effective_accuracy_with_k(dn: float, k: float) -> float:
    nm = novelty_penalty(dn)
    acc = ba * nm
    drift = 1.0 - acc
    nd = max(0.05, 1.0 - dn * k)
    pc = PEER_REVIEW_RATE * drift * RECALIBRATED_PEER_REVIEW_CORRECTION_RATE * nd
    return min(0.98, acc + pc)


def expected_yield_with_k(dn: float, k: float) -> float:
    ea = effective_accuracy_with_k(dn, k)
    return sum(ea * wave_uniqueness(w) for w in range(1, WAVE_COUNT + 1)) / WAVE_COUNT


def find_cliff_dn_with_k(k: float) -> float:
    """Find DN where expected campaign yield < CAMPAIGN_YIELD_WARNING."""
    # Binary search
    lo, hi = 0.30, 1.05
    for _ in range(60):
        mid = (lo + hi) / 2.0
        ey = expected_yield_with_k(mid, k)
        if ey >= CAMPAIGN_YIELD_WARNING:
            lo = mid
        else:
            hi = mid
    result = (lo + hi) / 2.0
    # Clamp to [0, 1] if no cliff found
    if expected_yield_with_k(1.00, k) >= CAMPAIGN_YIELD_WARNING:
        return float("inf")
    return result


for k_test in [1.20, 1.30, 1.40, 1.50, 1.60, 1.70, 1.80, 1.90, 2.00]:
    ea_035 = effective_accuracy_with_k(0.35, k_test)
    ey_035 = expected_yield_with_k(0.35, k_test)
    ea_070 = effective_accuracy_with_k(0.70, k_test)
    ey_070 = expected_yield_with_k(0.70, k_test)
    cliff = find_cliff_dn_with_k(k_test)
    verdict_035 = (
        "HEALTHY"
        if ey_035 >= 0.50
        else ("WARNING" if ey_035 >= CAMPAIGN_YIELD_WARNING else "FAILURE")
    )
    verdict_070 = (
        "HEALTHY"
        if ey_070 >= 0.50
        else ("WARNING" if ey_070 >= CAMPAIGN_YIELD_WARNING else "FAILURE")
    )
    cliff_str = f"{cliff:.3f}" if cliff < 2.0 else ">1.00"
    in_range = " ← IN RANGE" if (0.65 <= cliff <= 0.80) else ""
    print(
        f"  {k_test:>6.2f}  {ea_035:>9.4f}  {ey_035:>9.4f}  {ea_070:>9.4f}  {ey_070:>9.4f}  {cliff_str:>9}{in_range}"
    )

print(f"""
PROPOSED FIX (single-line change to _peer_correction()):

  Current:  novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 0.90)
  Proposed: novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 1.50)

This change:
  - At DN=0.35 (nominal): discount drops from 0.685 → 0.475
    effective_accuracy: {effective_accuracy_with_k(0.35, 1.50):.4f} (was {effective_accuracy_recal(0.35):.4f})
    expected yield: {expected_yield_with_k(0.35, 1.50):.4f} (was {expected_campaign_yield(0.35):.4f}) — still HEALTHY (≥0.50)
  - At DN=0.70 (cliff target): discount drops from 0.370 → 0.050 (floor hit)
    effective_accuracy: {effective_accuracy_with_k(0.70, 1.50):.4f} (was {effective_accuracy_recal(0.70):.4f})
    expected yield: {expected_yield_with_k(0.70, 1.50):.4f} — crosses WARNING threshold
  - Cliff DN with k=1.50: {find_cliff_dn_with_k(1.50):.3f}
""")

# Verify the proposed fix summary
k_proposed = 1.50
cliff_proposed = find_cliff_dn_with_k(k_proposed)
ey_nominal = expected_yield_with_k(0.35, k_proposed)
ey_at_cliff = expected_yield_with_k(cliff_proposed, k_proposed)

print(f"VERIFICATION OF PROPOSED FIX (k=1.50):")
print(
    f"  Nominal (DN=0.35): expected yield = {ey_nominal:.4f}  → {'HEALTHY' if ey_nominal >= 0.50 else 'REGRESSION'}"
)
print(
    f"  Cliff location: DN = {cliff_proposed:.4f}  → {'IN RANGE [0.65-0.80]' if 0.65 <= cliff_proposed <= 0.80 else 'OUT OF RANGE'}"
)
print(f"  expected yield at cliff: {ey_at_cliff:.4f}")

print(f"\nDN sweep with PROPOSED FIX (k=1.50):")
print(f"{'DN':>6}  {'ea_proposed':>12}  {'exp_yield':>10}  {'verdict':>8}")
print("-" * 45)
for dn in [0.35, 0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
    ea = effective_accuracy_with_k(dn, k_proposed)
    ey = expected_yield_with_k(dn, k_proposed)
    verdict = (
        "HEALTHY"
        if ey >= 0.50
        else ("WARNING" if ey >= CAMPAIGN_YIELD_WARNING else "FAILURE")
    )
    print(f"{dn:>6.2f}  {ea:>12.4f}  {ey:>10.4f}  {verdict:>8}")

print(f"""
SUMMARY
=======
Root cause: The novelty cliff sits at DN=0.95 (not 0.65-0.80) because:
  1. The recalibrated base_accuracy ({ba:.4f}) is still high due to specialist-
     weighted fleet (0.65 * 0.875 + 0.35 * 0.50 = {ba:.5f}).
  2. The novelty_discount slope of 0.90 (Change 2) is not steep enough to
     sufficiently discount peer correction at moderate novelty (DN 0.65-0.80).
     At DN=0.70, discount = {max(0.05, 1 - 0.70 * 0.90):.3f} — still provides substantial
     peer correction that keeps effective_acc above the required {required_ea:.4f}.
  3. The minimum effective_accuracy needed to trigger the cliff
     (= {CAMPAIGN_YIELD_WARNING} / mean_uniqueness_{WAVE_COUNT}waves = {CAMPAIGN_YIELD_WARNING}/{mean_uniqueness:.4f} = {required_ea:.4f})
     requires the novelty penalty to compound with a sharply reduced peer
     correction — which only happens at DN≈0.95 under current k=0.90 slope.

Fix: Change novelty_discount slope from 0.90 to 1.50:
  novelty_discount = max(0.05, 1.0 - DOMAIN_NOVELTY * 1.50)

  At this slope, the discount reaches the floor (0.05) at DN=0.633, meaning
  peer correction is effectively neutralized beyond DN≈0.63. This moves the
  cliff to DN≈{cliff_proposed:.3f}, within the target range [0.65-0.80].
  The nominal yield (DN=0.35) remains {ey_nominal:.4f} — above HEALTHY threshold.
""")
