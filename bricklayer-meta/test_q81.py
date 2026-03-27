"""
test_q81.py — Q8.1: J-curve Model B Phase 2 recalibration

Tests three J-curve variants to find one that produces Phase 2 mean >= 0.50
at WAVE_COUNT=20, QPW=7, DN=0.35, ASR=0.65.

Delete after running.
"""

import importlib
import sys
import os

# Ensure we import from bricklayer-meta directory
sys.path.insert(0, os.path.dirname(__file__))

import simulate

EMPIRICAL_TARGETS = {
    "phase1": 0.150,  # waves 1-7
    "phase2": 0.642,  # waves 8-15
    "phase3": 0.665,  # waves 16-20
}

TOLERANCE = 0.20


def wave_uniqueness_original(wave):
    """Original Model B (Q7.2 baseline): Phase 1=0.20, linear 8-15, plateau 0.75"""
    if wave <= 7:
        return 0.20
    elif wave <= 15:
        return 0.20 + (wave - 8) / 7.0 * (0.75 - 0.20)
    else:
        return 0.75


def wave_uniqueness_A(wave):
    """Variant A — Raised Phase 1 floor (0.35 instead of 0.20)"""
    if wave <= 7:
        return 0.35
    elif wave <= 15:
        return 0.35 + (wave - 8) / 7.0 * (0.75 - 0.35)
    else:
        return 0.75


def wave_uniqueness_B(wave):
    """Variant B — Compressed rise window (waves 8-12 instead of 8-15)"""
    if wave <= 7:
        return 0.20
    elif wave <= 12:
        return 0.20 + (wave - 8) / 4.0 * (0.75 - 0.20)
    else:
        return 0.75


def wave_uniqueness_C(wave):
    """Variant C — Convex (quadratic) rise"""
    if wave <= 7:
        return 0.20
    elif wave <= 15:
        t = (wave - 8) / 7.0  # 0->1 over waves 8-15
        return 0.20 + (0.75 - 0.20) * t**2  # convex: slow start, fast finish
    else:
        return 0.75


def compute_phase_means(records):
    """Compute per-phase mean wave yields."""
    phase1 = [r["wave_yield"] for r in records if 1 <= r["wave"] <= 7]
    phase2 = [r["wave_yield"] for r in records if 8 <= r["wave"] <= 15]
    phase3 = [r["wave_yield"] for r in records if 16 <= r["wave"] <= 20]

    p1_mean = sum(phase1) / len(phase1) if phase1 else 0.0
    p2_mean = sum(phase2) / len(phase2) if phase2 else 0.0
    p3_mean = sum(phase3) / len(phase3) if phase3 else 0.0

    return round(p1_mean, 3), round(p2_mean, 3), round(p3_mean, 3)


def run_variant(name, uniqueness_fn):
    """Run a simulation with a monkeypatched _wave_uniqueness function."""
    # Patch module-level parameters
    simulate.WAVE_COUNT = 20
    simulate.QUESTIONS_PER_WAVE = 7
    simulate.DOMAIN_NOVELTY = 0.35
    simulate.AGENT_SPECIALIZATION_RATIO = 0.65
    simulate.SIMULATION_SEED = 42

    # Monkeypatch the uniqueness function
    original_fn = simulate._wave_uniqueness
    simulate._wave_uniqueness = uniqueness_fn

    try:
        records, totals = simulate.run_simulation()
        results = simulate.evaluate(records, totals)
    finally:
        simulate._wave_uniqueness = original_fn

    p1, p2, p3 = compute_phase_means(records)

    return {
        "name": name,
        "verdict": results["verdict"],
        "campaign_yield": results["primary_metric"],
        "synthesis_coherence": results["synthesis_coherence"],
        "wave_novelty_floor": results["wave_novelty_floor"],
        "failure_reason": results["failure_reason"],
        "phase1_mean": p1,
        "phase2_mean": p2,
        "phase3_mean": p3,
        "records": records,
    }


def check_phase_targets(result):
    """Check each phase against empirical targets within ±0.20 tolerance."""
    checks = {}
    for phase_key, actual_val, target_val in [
        ("phase1", result["phase1_mean"], EMPIRICAL_TARGETS["phase1"]),
        ("phase2", result["phase2_mean"], EMPIRICAL_TARGETS["phase2"]),
        ("phase3", result["phase3_mean"], EMPIRICAL_TARGETS["phase3"]),
    ]:
        delta = actual_val - target_val
        passed = abs(delta) <= TOLERANCE
        checks[phase_key] = {
            "actual": actual_val,
            "target": target_val,
            "delta": round(delta, 3),
            "pass": passed,
        }
    return checks


def print_result(result):
    checks = check_phase_targets(result)
    print(f"\n{'=' * 60}")
    print(f"Variant: {result['name']}")
    print(f"  Verdict:          {result['verdict']}")
    print(f"  Campaign yield:   {result['campaign_yield']}")
    print(f"  Synthesis coh.:   {result['synthesis_coherence']}")
    print(f"  Wave novelty flr: {result['wave_novelty_floor']}")
    if result["failure_reason"] != "NONE":
        print(f"  Failure reason:   {result['failure_reason']}")
    print(f"  Phase means vs. empirical targets (±{TOLERANCE} tol):")
    for ph, c in checks.items():
        status = "PASS" if c["pass"] else "FAIL"
        print(
            f"    {ph}: actual={c['actual']:.3f}  target={c['target']:.3f}  delta={c['delta']:+.3f}  [{status}]"
        )
    print(
        f"  Phase 2 meets >=0.50 gate: {'YES' if result['phase2_mean'] >= 0.50 else 'NO'}"
    )


def main():
    print("Q8.1 — J-curve Model B Phase 2 recalibration")
    print("Testing three variants at WAVE_COUNT=20, QPW=7, DN=0.35, ASR=0.65")
    print("Target: at least one variant with HEALTHY verdict AND Phase 2 mean >= 0.50")

    variants = [
        ("Original Model B (Q7.2 baseline)", wave_uniqueness_original),
        ("Variant A — Raised Phase 1 floor (0.35)", wave_uniqueness_A),
        ("Variant B — Compressed rise window (8-12)", wave_uniqueness_B),
        ("Variant C — Convex (quadratic) rise", wave_uniqueness_C),
    ]

    results = []
    for name, fn in variants:
        r = run_variant(name, fn)
        results.append(r)
        print_result(r)

    # Determine best variant (highest Phase 2 mean among HEALTHY; fallback to highest overall)
    healthy_results = [r for r in results[1:] if r["verdict"] == "HEALTHY"]
    warning_results = [r for r in results[1:] if r["verdict"] == "WARNING"]
    best = None
    q81_verdict = "FAILURE"

    if healthy_results:
        # Sort by Phase 2 mean descending
        healthy_results.sort(key=lambda x: x["phase2_mean"], reverse=True)
        best = healthy_results[0]
        if best["phase2_mean"] >= 0.50:
            q81_verdict = "HEALTHY"
        else:
            q81_verdict = "WARNING"
    elif warning_results:
        warning_results.sort(key=lambda x: x["phase2_mean"], reverse=True)
        best = warning_results[0]
        if best["phase2_mean"] >= 0.50:
            q81_verdict = "WARNING"
        else:
            q81_verdict = "FAILURE"
    else:
        # All failure — pick highest phase2
        non_baseline = results[1:]
        non_baseline.sort(key=lambda x: x["phase2_mean"], reverse=True)
        best = non_baseline[0]
        q81_verdict = "FAILURE"

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Q8.1 Verdict:    {q81_verdict}")
    if best:
        print(f"Best variant:    {best['name']}")
        print(f"  Simulation verdict: {best['verdict']}")
        print(f"  Campaign yield:     {best['campaign_yield']}")
        print(
            f"  Phase 2 mean:       {best['phase2_mean']:.3f} (target 0.642, gate >= 0.50)"
        )
    print(f"Baseline (Q7.2): verdict=WARNING, phase2_mean=0.339")

    # Print per-wave for best variant
    if best:
        print(f"\nPer-wave breakdown for {best['name']}:")
        print(f"{'Wave':>5} {'Yield':>7} {'Uniq':>6} {'Phase':>7}")
        for r in best["records"]:
            wave = r["wave"]
            phase = "P1" if wave <= 7 else ("P2" if wave <= 15 else "P3")
            print(
                f"{wave:>5} {r['wave_yield']:>7.3f} {r['uniqueness']:>6.3f} {phase:>7}"
            )

    return q81_verdict, best


if __name__ == "__main__":
    q81_verdict, best = main()
    print(f"\nFinal Q8.1 verdict: {q81_verdict}")
    if best:
        print(f"Best variant Phase 2 mean: {best['phase2_mean']:.3f}")
