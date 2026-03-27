"""
test_q83.py — Q8.3: Temperature diversity at WAVE_COUNT=6, QPW=9 (54 questions)

Tests whether the integer floor (1/54 ≈ 0.019) allows DIVERSITY_BONUS to produce
measurable yield improvements at larger campaign scale vs Q7.8 (1/28 ≈ 0.036).
"""

import sys

sys.path.insert(0, ".")

import simulate


def run_config(wave_count, qpw, diversity_bonus, hypothesis_temp, label):
    """Override module-level vars, run simulation, return results."""
    simulate.WAVE_COUNT = wave_count
    simulate.QUESTIONS_PER_WAVE = qpw
    simulate.DIVERSITY_BONUS = diversity_bonus
    simulate.HYPOTHESIS_TEMPERATURE = hypothesis_temp

    records, totals = simulate.run_simulation()
    results = simulate.evaluate(records, totals)
    return results


def main():
    # Baseline: T=0.30, no diversity bonus, 54 questions
    r_baseline = run_config(
        wave_count=6,
        qpw=9,
        diversity_bonus=0.0,
        hypothesis_temp=0.30,
        label="T=0.30 (baseline)",
    )

    # T=0.50: DIVERSITY_BONUS=0.10, validity=1.0
    r_t50 = run_config(
        wave_count=6, qpw=9, diversity_bonus=0.10, hypothesis_temp=0.50, label="T=0.50"
    )

    # T=0.70: DIVERSITY_BONUS=0.20, HYPOTHESIS_TEMPERATURE=0.70 (validity penalty applies)
    r_t70 = run_config(
        wave_count=6, qpw=9, diversity_bonus=0.20, hypothesis_temp=0.70, label="T=0.70"
    )

    baseline_yield = r_baseline["primary_metric"]
    t50_yield = r_t50["primary_metric"]
    t70_yield = r_t70["primary_metric"]

    delta_t50 = round(t50_yield - baseline_yield, 4)
    delta_t70 = round(t70_yield - baseline_yield, 4)

    print("=" * 60)
    print("Q8.3: Temperature diversity at 54-question scale")
    print(f"Resolution floor: 1/54 ≈ {1 / 54:.4f}")
    print("=" * 60)
    print()
    print(f"{'Config':<20} {'yield':<10} {'delta':<10} {'actionable':<12} {'verdict'}")
    print("-" * 60)
    print(
        f"{'T=0.30 (baseline)':<20} {baseline_yield:<10.4f} {'—':<10} {r_baseline['total_actionable']:<12} {r_baseline['verdict']}"
    )
    print(
        f"{'T=0.50':<20} {t50_yield:<10.4f} {delta_t50:+.4f}    {r_t50['total_actionable']:<12} {r_t50['verdict']}"
    )
    print(
        f"{'T=0.70':<20} {t70_yield:<10.4f} {delta_t70:+.4f}    {r_t70['total_actionable']:<12} {r_t70['verdict']}"
    )
    print()

    # Verdict determination
    max_delta = max(delta_t50, delta_t70)
    if max_delta >= 0.03:
        verdict = "HEALTHY"
        reason = (
            f"Temperature produces yield delta >= 0.03 — integer floor was the issue"
        )
    elif max_delta >= 0.01:
        verdict = "WARNING"
        reason = f"Effect detectable (delta 0.01–0.03) but marginal"
    else:
        verdict = "FAILURE"
        reason = f"No temperature produces yield delta >= 0.01 at 54-question scale — diversity bonus fundamentally too small"

    print(f"Q8.3 Verdict: {verdict}")
    print(f"Reason: {reason}")
    print()
    print(f"T=0.50 delta: {delta_t50:+.4f}")
    print(f"T=0.70 delta: {delta_t70:+.4f}")
    print(f"Max delta: {max_delta:+.4f}")
    print()

    # Supplemental: resolution floor check
    floor = 1 / 54
    print(f"Resolution floor at 54q: {floor:.4f}")
    print(
        f"T=0.50 delta vs floor: {'ABOVE' if delta_t50 > floor else 'AT/BELOW'} ({delta_t50:.4f} vs {floor:.4f})"
    )
    print(
        f"T=0.70 delta vs floor: {'ABOVE' if delta_t70 > floor else 'AT/BELOW'} ({delta_t70:.4f} vs {floor:.4f})"
    )

    return {
        "verdict": verdict,
        "baseline_yield": baseline_yield,
        "t50_yield": t50_yield,
        "t70_yield": t70_yield,
        "delta_t50": delta_t50,
        "delta_t70": delta_t70,
        "t50_actionable": r_t50["total_actionable"],
        "t70_actionable": r_t70["total_actionable"],
        "baseline_actionable": r_baseline["total_actionable"],
        "reason": reason,
    }


if __name__ == "__main__":
    results = main()
