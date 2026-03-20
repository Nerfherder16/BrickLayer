"""
test_params.py — Tests for module loading, SimParams, and MCDistributionConfig.
Extends across Tasks 1, 2, 4, and 8.

NOTE: This file deliberately does NOT import simulate.py.
simulate.py has a module-level side effect (sys.stdout = io.TextIOWrapper(...))
that breaks pytest's fd-level capture. All simulate-dependent tests are in
test_sim_parity.py which runs with --no-header or uses subprocess isolation.
"""

import sys
import os
import pytest

# Add project root to path so we can import constants
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_baseline_params():
    """Build a complete params dict from constants.py + baseline scenario values.

    Scenario parameter values are taken directly from simulate.py's SCENARIO PARAMETERS
    section (lines 51-63 of simulate.py). These are intentionally inlined here so we
    don't need to import simulate.py (which has sys.stdout side effects).
    Baseline: EMPLOYEE_FEE_MONTHLY=45.0, VENDOR_CAPACITY_PER_EMPLOYEE=3000, SIMULATION_MONTHS=60
    """
    import constants as c
    return {
        # Scenario parameters (from simulate.py SCENARIO PARAMETERS section)
        "employee_fee_monthly": 45.0,
        "vendor_capacity_per_employee": 3000.0,
        "simulation_months": 60,
        # System constants (from constants.py)
        "token_face_value": c.TOKEN_FACE_VALUE,
        "mint_price": c.MINT_PRICE,
        "escrow_start_per_token": c.ESCROW_START_PER_TOKEN,
        "burn_eligible_crr": c.BURN_ELIGIBLE_CRR,
        "burn_rate_floor": c.BURN_RATE_FLOOR,
        "burn_rate_ceiling": c.BURN_RATE_CEILING,
        "admin_fee_floor": c.ADMIN_FEE_FLOOR,
        "admin_fee_cap": c.ADMIN_FEE_CAP,
        "crr_operational_target": c.CRR_OPERATIONAL_TARGET,
        "crr_mint_pause": c.CRR_MINT_PAUSE,
        "crr_critical": c.CRR_CRITICAL,
        "crr_overcapitalized": c.CRR_OVERCAPITALIZED,
        "capacity_ratio": c.CAPACITY_RATIO,
        "monthly_mint_cap_per_employee": float(c.MONTHLY_MINT_CAP_PER_EMPLOYEE),
        "expected_monthly_mint_per_employee": float(c.EXPECTED_MONTHLY_MINT_PER_EMPLOYEE),
        "annual_interest_rate": c.ANNUAL_INTEREST_RATE,
        "growth_curve": list(c.GROWTH_CURVE),
        "growth_target_employees": c.GROWTH_TARGET_EMPLOYEES,
        "failure_threshold": c.FAILURE_THRESHOLD,
        "warning_threshold": c.WARNING_THRESHOLD,
    }


# ── Task 1: Module smoke test ──────────────────────────────────────────────────

def test_module_loads():
    """The Rust extension must be importable."""
    import adbp2_mc  # noqa: F401


def test_hello():
    """hello() must return the exact sentinel string."""
    import adbp2_mc
    assert adbp2_mc.hello() == "adbp2_mc loaded"


# ── Task 2: SimParams construction ────────────────────────────────────────────

def test_sim_params_constructs_from_dict():
    """SimParams must accept a complete params dict and expose all fields."""
    import adbp2_mc
    params = _make_baseline_params()
    sp = adbp2_mc.SimParams(params)
    assert sp is not None


def test_sim_params_field_values():
    """SimParams fields must match the input dict values."""
    import adbp2_mc
    import constants as c
    params = _make_baseline_params()
    sp = adbp2_mc.SimParams(params)
    rt = sp.to_py_dict()
    assert abs(rt["employee_fee_monthly"] - 45.0) < 1e-9
    assert abs(rt["token_face_value"] - c.TOKEN_FACE_VALUE) < 1e-9
    assert abs(rt["annual_interest_rate"] - c.ANNUAL_INTEREST_RATE) < 1e-9
    # monthly_interest_rate is computed internally from annual_interest_rate
    assert abs(rt["monthly_interest_rate"] - c.ANNUAL_INTEREST_RATE / 12.0) < 1e-9
    assert rt["simulation_months"] == 60
    assert rt["growth_curve"] == list(c.GROWTH_CURVE)


def test_sim_params_missing_field_raises():
    """SimParams must raise an error when a required key is missing."""
    import adbp2_mc
    params = _make_baseline_params()
    del params["employee_fee_monthly"]
    with pytest.raises((ValueError, KeyError, Exception)):
        adbp2_mc.SimParams(params)


# ── Task 4: MCDistributionConfig ──────────────────────────────────────────────

def test_mc_config_constructs_empty():
    """MCDistributionConfig must accept an empty dict (all fields default to None)."""
    import adbp2_mc
    config = adbp2_mc.MCDistributionConfig({})
    assert config is not None


def test_mc_config_constructs_full():
    """MCDistributionConfig must accept all optional fields."""
    import adbp2_mc
    config = adbp2_mc.MCDistributionConfig({
        "mint_per_employee_mean": 2000.0,
        "mint_per_employee_std": 200.0,
        "growth_multiplier_std": 0.1,
        "interest_rate_mean": 0.04,
        "interest_rate_std": 0.005,
        "fee_compliance_alpha": 20.0,
        "fee_compliance_beta": 2.0,
        "vendor_capacity_mean": 3000.0,
        "vendor_capacity_std": 300.0,
    })
    assert config is not None


# ── Task 8: Module-level function exports ──────────────────────────────────────

def test_module_has_run_simulation():
    import adbp2_mc
    assert hasattr(adbp2_mc, "run_simulation")


def test_module_has_run_monte_carlo():
    import adbp2_mc
    assert hasattr(adbp2_mc, "run_monte_carlo")


def test_module_has_evaluate():
    import adbp2_mc
    assert hasattr(adbp2_mc, "evaluate")
