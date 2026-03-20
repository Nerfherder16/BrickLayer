"""
conftest.py — Shared pytest fixtures for the ADBP v2 test suite (Task 12).

IMPORTANT: This file does NOT import simulate.py. All fixtures that need
simulate.py values hardcode the known baseline scenario parameters to avoid
the sys.stdout side-effect that simulate.py triggers at module load time.

See test_params.py docstring for full explanation of the simulate.py
sys.stdout conflict.
"""

import pytest


@pytest.fixture
def baseline_params():
    """
    Return a complete params dict with baseline scenario values + system constants.

    Scenario parameters are hardcoded here (not imported from simulate.py) to
    avoid the sys.stdout replacement side-effect. The values match the SCENARIO
    PARAMETERS section of simulate.py exactly.

    Returns
    -------
    dict
        Full params dict suitable for adbp2_mc.run_simulation(),
        adbp2_mc.run_monte_carlo(), and mc_fallback.run_monte_carlo().
    """
    import constants as c

    return {
        # Scenario parameters (hardcoded from simulate.py SCENARIO PARAMETERS)
        "employee_fee_monthly": 45.0,
        "vendor_capacity_per_employee": 3000.0,
        "simulation_months": 60,
        # System constants from constants.py
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
        "expected_monthly_mint_per_employee": float(
            c.EXPECTED_MONTHLY_MINT_PER_EMPLOYEE
        ),
        "annual_interest_rate": c.ANNUAL_INTEREST_RATE,
        "monthly_interest_rate": c.ANNUAL_INTEREST_RATE / 12.0,
        "growth_curve": list(c.GROWTH_CURVE),
        "growth_target_employees": c.GROWTH_TARGET_EMPLOYEES,
        "failure_threshold": c.FAILURE_THRESHOLD,
        "warning_threshold": c.WARNING_THRESHOLD,
    }


@pytest.fixture
def mc_config_default():
    """
    Return the default MCDistributionConfig dict.

    Matches the defaults used in monte_carlo.py's _DEFAULT_MC_CONFIG.

    Returns
    -------
    dict
        MC distribution config suitable for adbp2_mc.run_monte_carlo()
        and mc_fallback.run_monte_carlo().
    """
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


@pytest.fixture
def rust_available():
    """
    Return True if the adbp2_mc Rust extension can be imported.

    Tests that require Rust should use this fixture and skip if False.

    Returns
    -------
    bool
    """
    try:
        import adbp2_mc  # noqa: F401

        return True
    except ImportError:
        return False
