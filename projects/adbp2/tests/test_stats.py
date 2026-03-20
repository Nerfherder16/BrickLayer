"""
test_stats.py — Tests for the Rust stats module (Task 5).
Tests percentile() and summarize_mc() via Python-accessible helpers.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Task 5: percentile() ───────────────────────────────────────────────────────


def test_percentile_p0_is_min():
    """P0 must equal the minimum value."""
    import adbp2_mc

    data = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]
    assert abs(adbp2_mc.percentile_test(data, 0.0) - 1.0) < 1e-9


def test_percentile_p100_is_max():
    """P100 must equal the maximum value."""
    import adbp2_mc

    data = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]
    assert abs(adbp2_mc.percentile_test(data, 100.0) - 9.0) < 1e-9


def test_percentile_p50_of_1_to_5():
    """P50 of [1,2,3,4,5] must be 3.0."""
    import adbp2_mc

    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(adbp2_mc.percentile_test(data, 50.0) - 3.0) < 1e-9


def test_percentile_p25_interpolation():
    """P25 of [1,2,3,4] must use linear interpolation."""
    import adbp2_mc
    import numpy as np  # Use numpy as reference if available

    data = [1.0, 2.0, 3.0, 4.0]
    result = adbp2_mc.percentile_test(data, 25.0)
    try:
        expected = float(np.percentile(data, 25.0))
        assert abs(result - expected) < 1e-6, f"Got {result}, expected {expected}"
    except ImportError:
        # Without numpy, just verify it's in range [1, 2]
        assert 1.0 <= result <= 2.0


def test_percentile_single_element():
    """P50 of a single-element list must return that element."""
    import adbp2_mc

    assert abs(adbp2_mc.percentile_test([42.0], 50.0) - 42.0) < 1e-9


def test_percentile_uniform_values():
    """Percentile of all-equal values must return that value."""
    import adbp2_mc

    data = [5.0] * 10
    for p in [0.0, 25.0, 50.0, 75.0, 100.0]:
        assert abs(adbp2_mc.percentile_test(data, p) - 5.0) < 1e-9


# ── Task 5: run_monte_carlo output shape ──────────────────────────────────────


def _make_baseline_params():
    """Build params dict from constants.py."""
    import constants as c

    return {
        "employee_fee_monthly": 45.0,
        "vendor_capacity_per_employee": 3000.0,
        "simulation_months": 60,
        "token_face_value": c.TOKEN_FACE_VALUE,
        "mint_price": c.MINT_PRICE,
        "escrow_start_per_token": c.ESCROW_START_PER_TOKEN,
        "burn_eligible_crr": c.BURN_ELIGIBLE_CRR,
        "burn_rate_floor": c.BURN_RATE_FLOOR,
        "burn_rate_ceiling": c.BURN_RATE_CEILING,
        "fee_to_operator_pct": c.FEE_TO_OPERATOR_PCT,
        "crr_operational_target": c.CRR_OPERATIONAL_TARGET,
        "crr_mint_pause": c.CRR_MINT_PAUSE,
        "crr_critical": c.CRR_CRITICAL,
        "crr_overcapitalized": c.CRR_OVERCAPITALIZED,
        "capacity_ratio": c.CAPACITY_RATIO,
        "monthly_mint_cap_per_employee": float(c.MONTHLY_MINT_CAP_PER_EMPLOYEE),
        "expected_monthly_mint_per_employee": float(
            c.EXPECTED_MONTHLY_MINT_PER_EMPLOYEE
        ),
        "annual_interest_rate": c.ANNUAL_INTEREST_RATE,
        "growth_curve": list(c.GROWTH_CURVE),
        "growth_target_employees": c.GROWTH_TARGET_EMPLOYEES,
        "failure_threshold": c.FAILURE_THRESHOLD,
        "warning_threshold": c.WARNING_THRESHOLD,
    }


def _default_mc_config():
    return {
        "mint_per_employee_mean": 2000.0,
        "mint_per_employee_std": 200.0,
        "growth_multiplier_std": 0.1,
        "interest_rate_mean": 0.04,
        "interest_rate_std": 0.005,
        "fee_compliance_alpha": 20.0,
        "fee_compliance_beta": 2.0,
        "vendor_capacity_mean": 3000.0,
        "vendor_capacity_std": 300.0,
    }


def test_mc_output_has_all_keys():
    """run_monte_carlo output must have all required top-level keys."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 10, seed=42)
    required = [
        "n_samples",
        "crr_trajectory",
        "p_burn_activates",
        "p_ruin",
        "first_burn_month_distribution",
        "final_crr_distribution",
        "per_sample_summaries",
    ]
    for k in required:
        assert k in result, f"Missing key: {k}"


def test_mc_crr_trajectory_length():
    """crr_trajectory bands must each have length == simulation_months."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 10, seed=42)
    assert len(result["crr_trajectory"]["p10"]) == 60
    assert len(result["crr_trajectory"]["p50"]) == 60
    assert len(result["crr_trajectory"]["p90"]) == 60


def test_mc_p_ruin_in_range():
    """p_ruin must be in [0, 1]."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 20, seed=42)
    assert 0.0 <= result["p_ruin"] <= 1.0


def test_mc_n_samples_matches():
    """n_samples in output must match the requested count."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 50, seed=42)
    assert result["n_samples"] == 50


def test_mc_reproducible_with_seed():
    """Same seed must produce identical results."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    r1 = adbp2_mc.run_monte_carlo(params, mc, 20, seed=42)
    r2 = adbp2_mc.run_monte_carlo(params, mc, 20, seed=42)
    assert r1["p_ruin"] == r2["p_ruin"]
    assert r1["final_crr_distribution"]["p50"] == r2["final_crr_distribution"]["p50"]
    assert r1["crr_trajectory"]["p50"] == r2["crr_trajectory"]["p50"]


def test_mc_different_seeds_differ():
    """Different seeds must produce different results (with high probability)."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    r1 = adbp2_mc.run_monte_carlo(params, mc, 50, seed=1)
    r2 = adbp2_mc.run_monte_carlo(params, mc, 50, seed=999)
    # With N=50 and meaningful std, the p50 CRR should differ
    assert r1["final_crr_distribution"]["p50"] != r2["final_crr_distribution"]["p50"]


def test_mc_no_seed_randomness():
    """None seed must produce different results on repeated calls."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    r1 = adbp2_mc.run_monte_carlo(params, mc, 50, seed=None)
    r2 = adbp2_mc.run_monte_carlo(params, mc, 50, seed=None)
    # Statistical: with N=50 and real randomness, p50 should very likely differ
    # This test is probabilistic — failure probability is extremely low
    assert r1["final_crr_distribution"]["p50"] != r2["final_crr_distribution"]["p50"]


def test_mc_per_sample_summaries_included():
    """include_per_sample=True must return per_sample_summaries."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 5, seed=42, include_per_sample=True)
    assert len(result["per_sample_summaries"]) == 5
    for s in result["per_sample_summaries"]:
        assert "verdict" in s
        assert "final_crr" in s


def test_mc_per_sample_empty_by_default():
    """include_per_sample=False (default) must return empty per_sample_summaries."""
    import adbp2_mc

    params = _make_baseline_params()
    mc = _default_mc_config()
    result = adbp2_mc.run_monte_carlo(params, mc, 5, seed=42)
    assert len(result["per_sample_summaries"]) == 0
