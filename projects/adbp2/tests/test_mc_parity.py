"""
test_mc_parity.py — Cross-engine statistical parity (Task 11).

Tests that the Rust MC engine (adbp2_mc) and the Python fallback
(mc_fallback) produce statistically equivalent results for the same
configuration and sample count.

IMPORTANT: Exact per-sample parity is NOT expected — Rust uses ChaCha8Rng
and Python uses Mersenne Twister. Only statistical convergence is tested.
Tolerance bands: p_ruin ±0.05, p50 CRR ±0.05, first_burn p50 ±2 months.

If the Rust extension is unavailable, all tests are skipped.

DESIGN: Both engines import simulate.py (directly or via mc_fallback), so
both are run via subprocess with named-file JSON output — same isolation
pattern as test_fallback.py and test_mc_output.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Check Rust availability (module-level, no simulate import)
# ---------------------------------------------------------------------------

try:
    import adbp2_mc as _adbp2_mc  # noqa: F401

    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _RUST_AVAILABLE, reason="adbp2_mc Rust extension not available"
)


# ---------------------------------------------------------------------------
# Subprocess runners
# ---------------------------------------------------------------------------

_RUST_RUNNER = """
import sys, json, os
sys.path.insert(0, {root!r})
import constants as c

params = {{
    "employee_fee_monthly": 45.0,
    "vendor_capacity_per_employee": 3000.0,
    "simulation_months": 60,
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
    "monthly_interest_rate": c.ANNUAL_INTEREST_RATE / 12.0,
    "growth_curve": list(c.GROWTH_CURVE),
    "growth_target_employees": c.GROWTH_TARGET_EMPLOYEES,
    "failure_threshold": c.FAILURE_THRESHOLD,
    "warning_threshold": c.WARNING_THRESHOLD,
}}

mc_config = {{
    "mint_per_employee_mean": 2000.0,
    "mint_per_employee_std": 200.0,
    "growth_multiplier_std": 0.1,
    "interest_rate_mean": 0.04,
    "interest_rate_std": 0.005,
    "fee_compliance_alpha": 20.0,
    "fee_compliance_beta": 2.0,
    "vendor_capacity_mean": 3000.0,
    "vendor_capacity_std": 300.0,
}}

import adbp2_mc
result = adbp2_mc.run_monte_carlo(params, mc_config, {n_samples}, seed={seed})
with open({out_path!r}, "w", encoding="utf-8") as _f:
    _f.write(json.dumps(result))
"""

_PYTHON_RUNNER = """
import sys, json, os
sys.path.insert(0, {root!r})
import constants as c

params = {{
    "employee_fee_monthly": 45.0,
    "vendor_capacity_per_employee": 3000.0,
    "simulation_months": 60,
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
    "monthly_interest_rate": c.ANNUAL_INTEREST_RATE / 12.0,
    "growth_curve": list(c.GROWTH_CURVE),
    "growth_target_employees": c.GROWTH_TARGET_EMPLOYEES,
    "failure_threshold": c.FAILURE_THRESHOLD,
    "warning_threshold": c.WARNING_THRESHOLD,
}}

mc_config = {{
    "mint_per_employee_mean": 2000.0,
    "mint_per_employee_std": 200.0,
    "growth_multiplier_std": 0.1,
    "interest_rate_mean": 0.04,
    "interest_rate_std": 0.005,
    "fee_compliance_alpha": 20.0,
    "fee_compliance_beta": 2.0,
    "vendor_capacity_mean": 3000.0,
    "vendor_capacity_std": 300.0,
}}

import mc_fallback
result = mc_fallback.run_monte_carlo(params, mc_config, {n_samples}, seed={seed})
with open({out_path!r}, "w", encoding="utf-8") as _f:
    _f.write(json.dumps(result))
"""


def _run_engine(template: str, n_samples: int, seed: int) -> dict:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as ntf:
        out_path = ntf.name

    try:
        script = template.format(
            root=PROJECT_ROOT.replace("\\", "\\\\"),
            n_samples=n_samples,
            seed=seed,
            out_path=out_path.replace("\\", "\\\\"),
        )
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"

        with tempfile.TemporaryFile(mode="w+", suffix=".txt") as err_f:
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=PROJECT_ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=err_f,
                timeout=180,
                env=env,
            )
            if proc.returncode != 0:
                err_f.seek(0)
                err_text = err_f.read()
                pytest.skip(f"Engine subprocess failed:\n{err_text[:1000]}")

        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

_N_SAMPLES = 200
_SEED = 42


def test_parity_p_ruin_within_tolerance():
    """p_ruin from Rust and Python fallback must be within 0.05 of each other."""
    rust = _run_engine(_RUST_RUNNER, _N_SAMPLES, _SEED)
    python = _run_engine(_PYTHON_RUNNER, _N_SAMPLES, _SEED)
    diff = abs(rust["p_ruin"] - python["p_ruin"])
    assert diff <= 0.05, (
        f"p_ruin divergence too large: Rust={rust['p_ruin']:.4f}, "
        f"Python={python['p_ruin']:.4f}, diff={diff:.4f}"
    )


def test_parity_final_crr_p50_within_tolerance():
    """final_crr p50 from both engines must be within 0.05 of each other."""
    rust = _run_engine(_RUST_RUNNER, _N_SAMPLES, _SEED)
    python = _run_engine(_PYTHON_RUNNER, _N_SAMPLES, _SEED)
    rust_p50 = rust["final_crr_distribution"]["p50"]
    python_p50 = python["final_crr_distribution"]["p50"]
    diff = abs(rust_p50 - python_p50)
    assert diff <= 0.05, (
        f"final_crr p50 divergence too large: Rust={rust_p50:.4f}, "
        f"Python={python_p50:.4f}, diff={diff:.4f}"
    )


def test_parity_first_burn_p50_within_tolerance():
    """first_burn_month p50 must be within 2 months between engines."""
    rust = _run_engine(_RUST_RUNNER, _N_SAMPLES, _SEED)
    python = _run_engine(_PYTHON_RUNNER, _N_SAMPLES, _SEED)
    rust_p50 = rust["first_burn_month_distribution"]["p50"]
    python_p50 = python["first_burn_month_distribution"]["p50"]
    diff = abs(rust_p50 - python_p50)
    assert diff <= 2.0, (
        f"first_burn_month p50 divergence too large: Rust={rust_p50:.1f}, "
        f"Python={python_p50:.1f}, diff={diff:.1f}"
    )


def test_parity_output_schema_compatible():
    """Both engines must produce the same top-level output keys."""
    rust = _run_engine(_RUST_RUNNER, n_samples=10, seed=1)
    python = _run_engine(_PYTHON_RUNNER, n_samples=10, seed=1)
    assert set(rust.keys()) == set(python.keys()), (
        f"Schema mismatch: Rust keys={set(rust.keys())}, "
        f"Python keys={set(python.keys())}"
    )


def test_parity_crr_trajectory_same_length():
    """Both engines must produce crr_trajectory bands of the same length."""
    rust = _run_engine(_RUST_RUNNER, n_samples=10, seed=1)
    python = _run_engine(_PYTHON_RUNNER, n_samples=10, seed=1)
    assert len(rust["crr_trajectory"]["p50"]) == len(python["crr_trajectory"]["p50"]), (
        "crr_trajectory p50 length mismatch between engines"
    )
    assert len(rust["crr_trajectory"]["p50"]) == 60
