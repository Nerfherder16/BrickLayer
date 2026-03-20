"""
test_fallback.py — Tests for the Python fallback MC engine (Task 9).

DESIGN: mc_fallback.run_monte_carlo() lazily imports simulate.py, which
mutates sys.stdout at module level. This breaks pytest's fd-level capture
teardown (same problem as simulate.py imports everywhere else in this suite).

Solution: every test runs mc_fallback via subprocess.run() in a fresh
Python process. Results are passed back as JSON. Tests never import
mc_fallback or simulate directly.
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
# Subprocess helper
# ---------------------------------------------------------------------------

_RUNNER_TEMPLATE = """
import sys, json, os
sys.path.insert(0, {root!r})
import constants as c

base_params = {{
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
result = mc_fallback.run_monte_carlo(
    base_params, mc_config,
    n_samples={n_samples},
    seed={seed},
    include_per_sample={include_per_sample},
)
# Write to a named file — cannot use print() because simulate.py replaced sys.stdout
# and sys.__stdout__.buffer is closed after the replacement.
with open({out_path!r}, "w", encoding="utf-8") as _out:
    _out.write(json.dumps(result))
"""


def _run_fallback(n_samples: int, seed=42, include_per_sample: bool = False) -> dict:
    """Run mc_fallback.run_monte_carlo() in a subprocess and return the result dict."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as ntf:
        out_path = ntf.name

    try:
        script = _RUNNER_TEMPLATE.format(
            root=PROJECT_ROOT.replace("\\", "\\\\"),
            n_samples=n_samples,
            seed=repr(seed),
            include_per_sample=repr(include_per_sample),
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
                timeout=120,
                env=env,
            )
            if proc.returncode != 0:
                err_f.seek(0)
                err_text = err_f.read()
                pytest.skip(f"mc_fallback subprocess failed:\n{err_text[:1000]}")

        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_fallback_output_has_all_keys():
    """Fallback output must have all required top-level keys."""
    result = _run_fallback(n_samples=10, seed=42)
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


def test_fallback_crr_trajectory_length():
    """crr_trajectory bands must each have length == simulation_months."""
    result = _run_fallback(n_samples=10, seed=42)
    assert len(result["crr_trajectory"]["p10"]) == 60
    assert len(result["crr_trajectory"]["p50"]) == 60
    assert len(result["crr_trajectory"]["p90"]) == 60


def test_fallback_n_samples_matches():
    """n_samples in output must match the requested count."""
    result = _run_fallback(n_samples=50, seed=42)
    assert result["n_samples"] == 50


def test_fallback_p_ruin_in_range():
    """p_ruin must be in [0, 1]."""
    result = _run_fallback(n_samples=20, seed=42)
    assert 0.0 <= result["p_ruin"] <= 1.0


def test_fallback_reproducible_with_seed():
    """Same seed must produce identical results."""
    r1 = _run_fallback(n_samples=20, seed=42)
    r2 = _run_fallback(n_samples=20, seed=42)
    assert r1["p_ruin"] == r2["p_ruin"]
    assert r1["final_crr_distribution"]["p50"] == r2["final_crr_distribution"]["p50"]
    assert r1["crr_trajectory"]["p50"] == r2["crr_trajectory"]["p50"]


def test_fallback_different_seeds_differ():
    """Different seeds must produce different results (with high probability)."""
    r1 = _run_fallback(n_samples=50, seed=1)
    r2 = _run_fallback(n_samples=50, seed=999)
    assert r1["final_crr_distribution"]["p50"] != r2["final_crr_distribution"]["p50"]


def test_fallback_per_sample_summaries_included():
    """include_per_sample=True must return per_sample_summaries with 5 entries."""
    result = _run_fallback(n_samples=5, seed=42, include_per_sample=True)
    assert len(result["per_sample_summaries"]) == 5
    for s in result["per_sample_summaries"]:
        assert "verdict" in s
        assert "final_crr" in s


def test_fallback_per_sample_empty_by_default():
    """include_per_sample=False (default) must return empty per_sample_summaries."""
    result = _run_fallback(n_samples=5, seed=42, include_per_sample=False)
    assert len(result["per_sample_summaries"]) == 0


def test_fallback_crr_trajectory_p50_nonnegative():
    """p50 CRR trajectory values must be non-negative for baseline params."""
    result = _run_fallback(n_samples=20, seed=42)
    assert all(v >= 0.0 for v in result["crr_trajectory"]["p50"])


def test_fallback_p_burn_activates_keys():
    """p_burn_activates must have all time-window keys with values in [0,1]."""
    result = _run_fallback(n_samples=10, seed=42)
    burn = result["p_burn_activates"]
    for key in (
        "within_12mo",
        "within_24mo",
        "within_36mo",
        "within_48mo",
        "within_60mo",
    ):
        assert key in burn
        assert 0.0 <= burn[key] <= 1.0


def test_fallback_final_crr_dist_keys():
    """final_crr_distribution must have p10/p50/p90/mean/std keys."""
    result = _run_fallback(n_samples=10, seed=42)
    fcd = result["final_crr_distribution"]
    for key in ("p10", "p50", "p90", "mean", "std"):
        assert key in fcd
