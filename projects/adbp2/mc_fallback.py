"""
mc_fallback.py — Pure-Python Monte Carlo fallback engine for ADBP v2.

Used automatically by monte_carlo.py when the Rust adbp2_mc extension is
unavailable. Mirrors the Rust engine's interface and output schema exactly.

Interface
---------
run_monte_carlo(
    base_params: dict,
    mc_config: dict,
    n_samples: int,
    seed: int | None = None,
    include_per_sample: bool = False,
) -> dict

Sampling
--------
- mint_per_employee:           Normal(mean, std)   via random.gauss()
- growth_multiplier:           Normal(1.0, std)     via random.gauss()
- annual_interest_rate:        Normal(mean, std)    via random.gauss()
- fee_compliance_rate:         Beta(alpha, beta)    via random.betavariate()
- vendor_capacity_per_employee Normal(mean, std)    via random.gauss()

All clamping mirrors the Rust implementation.

Engine
------
Uses simulate.run_simulation() + simulate.evaluate() for the core loop.
Monkey-patches simulate module globals per-sample via a context manager.
Single-threaded (no Rayon equivalent needed for a fallback).

Note: sys.stdout is already replaced by simulate.py at import time, so
importing simulate here is safe *in isolation*. monte_carlo.py imports
simulate.py anyway. The caution is only in pytest — never import this
file inside a pytest context that hasn't already imported simulate.
"""

from __future__ import annotations

import math
import random
from contextlib import contextmanager
from typing import Any


# ---------------------------------------------------------------------------
# Percentile (mirrors stats.rs implementation — numpy linear interpolation)
# ---------------------------------------------------------------------------


def _percentile(data: list[float], p: float) -> float:
    """Compute the p-th percentile using linear interpolation (numpy default)."""
    if not data:
        raise ValueError("percentile: empty data")
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    index = (p / 100.0) * (n - 1)
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    frac = index - lower
    if lower == upper:
        return sorted_data[lower]
    return sorted_data[lower] * (1.0 - frac) + sorted_data[upper] * frac


# ---------------------------------------------------------------------------
# Sampling — mirrors mc.rs sample_params()
# ---------------------------------------------------------------------------


def _sample_params(base_params: dict, mc_config: dict, rng: random.Random) -> dict:
    """Return a perturbed copy of base_params for one MC sample."""
    p = dict(base_params)

    # mint_per_employee: Normal(mean, std)
    mean = mc_config.get("mint_per_employee_mean")
    std = mc_config.get("mint_per_employee_std")
    if mean is not None and std is not None:
        if std > 0.0:
            val = rng.gauss(mean, std)
        else:
            val = mean
        p["expected_monthly_mint_per_employee"] = max(0.0, val)

    # growth_multiplier: Normal(1.0, std)
    gstd = mc_config.get("growth_multiplier_std")
    if gstd is not None and gstd > 0.0:
        multiplier = max(0.01, rng.gauss(1.0, gstd))
        original_curve = base_params["growth_curve"]
        p["growth_curve"] = [max(1, round(v * multiplier)) for v in original_curve]

    # annual_interest_rate: Normal(mean, std)
    ir_mean = mc_config.get("interest_rate_mean")
    ir_std = mc_config.get("interest_rate_std")
    if ir_mean is not None and ir_std is not None:
        if ir_std > 0.0:
            rate = rng.gauss(ir_mean, ir_std)
        else:
            rate = ir_mean
        p["annual_interest_rate"] = max(0.0, rate)
        p["monthly_interest_rate"] = p["annual_interest_rate"] / 12.0

    # fee_compliance_rate: Beta(alpha, beta)
    alpha = mc_config.get("fee_compliance_alpha")
    beta_param = mc_config.get("fee_compliance_beta")
    if (
        alpha is not None
        and beta_param is not None
        and alpha > 0.0
        and beta_param > 0.0
    ):
        compliance = max(0.0, min(1.0, rng.betavariate(alpha, beta_param)))
        p["employee_fee_monthly"] = base_params["employee_fee_monthly"] * compliance

    # vendor_capacity_per_employee: Normal(mean, std)
    vc_mean = mc_config.get("vendor_capacity_mean")
    vc_std = mc_config.get("vendor_capacity_std")
    if vc_mean is not None and vc_std is not None:
        if vc_std > 0.0:
            val = rng.gauss(vc_mean, vc_std)
        else:
            val = vc_mean
        p["vendor_capacity_per_employee"] = max(0.0, val)

    return p


# ---------------------------------------------------------------------------
# Monkey-patching context manager
# ---------------------------------------------------------------------------


@contextmanager
def _patched_simulate(sim_module: Any, sampled: dict):
    """
    Temporarily override simulate module globals for one simulation run.

    Patches both the scenario params (EMPLOYEE_FEE_MONTHLY etc.) and the
    constants imported into the simulate namespace (EXPECTED_MONTHLY_MINT_PER_EMPLOYEE,
    MONTHLY_INTEREST_RATE, etc.).
    """
    PATCHES = {
        "EMPLOYEE_FEE_MONTHLY": "employee_fee_monthly",
        "VENDOR_CAPACITY_PER_EMPLOYEE": "vendor_capacity_per_employee",
        "SIMULATION_MONTHS": "simulation_months",
        "EXPECTED_MONTHLY_MINT_PER_EMPLOYEE": "expected_monthly_mint_per_employee",
        "MONTHLY_MINT_CAP_PER_EMPLOYEE": "monthly_mint_cap_per_employee",
        "ANNUAL_INTEREST_RATE": "annual_interest_rate",
        "MONTHLY_INTEREST_RATE": "monthly_interest_rate",
    }

    saved = {}
    for attr, key in PATCHES.items():
        if hasattr(sim_module, attr) and key in sampled:
            saved[attr] = getattr(sim_module, attr)
            setattr(sim_module, attr, sampled[key])

    # growth_curve — special: simulate reads from the constants import in its namespace
    saved_growth = None
    if hasattr(sim_module, "GROWTH_CURVE") and "growth_curve" in sampled:
        saved_growth = sim_module.GROWTH_CURVE
        sim_module.GROWTH_CURVE = sampled["growth_curve"]

    try:
        yield
    finally:
        for attr, val in saved.items():
            setattr(sim_module, attr, val)
        if saved_growth is not None:
            sim_module.GROWTH_CURVE = saved_growth


# ---------------------------------------------------------------------------
# Summarise a batch of (records, failure_reason, eval_result) triples
# ---------------------------------------------------------------------------


def _summarize(
    results: list[tuple[list[dict], str | None, dict]],
    simulation_months: int,
    include_per_sample: bool,
) -> dict:
    n = len(results)
    if n == 0:
        return {
            "n_samples": 0,
            "crr_trajectory": {"p10": [], "p50": [], "p90": []},
            "p_burn_activates": {
                "within_12mo": 0.0,
                "within_24mo": 0.0,
                "within_36mo": 0.0,
                "within_48mo": 0.0,
                "within_60mo": 0.0,
            },
            "p_ruin": 0.0,
            "first_burn_month_distribution": {
                "p10": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "never_pct": 1.0,
            },
            "final_crr_distribution": {
                "p10": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "mean": 0.0,
                "std": 0.0,
            },
            "per_sample_summaries": [],
        }

    records_list = [r for r, _, _ in results]
    eval_list = [e for _, _, e in results]

    # CRR trajectory bands
    p10_traj = []
    p50_traj = []
    p90_traj = []
    for month_idx in range(simulation_months):
        crr_at_month = [
            recs[month_idx]["crr"] for recs in records_list if month_idx < len(recs)
        ]
        if not crr_at_month:
            p10_traj.append(0.0)
            p50_traj.append(0.0)
            p90_traj.append(0.0)
        else:
            short_count = n - len(crr_at_month)
            crr_at_month.extend([0.0] * short_count)
            p10_traj.append(_percentile(crr_at_month, 10.0))
            p50_traj.append(_percentile(crr_at_month, 50.0))
            p90_traj.append(_percentile(crr_at_month, 90.0))

    # P(burn activates within N months)
    def burn_within(limit: int) -> float:
        count = sum(
            1
            for e in eval_list
            if e.get("first_burn_month") not in (None, "never")
            and isinstance(e["first_burn_month"], int)
            and e["first_burn_month"] <= limit
        )
        return count / n

    # P(ruin)
    ruin_count = sum(
        1 for e in eval_list if e.get("verdict") in ("FAILURE", "INSOLVENT")
    )
    p_ruin = ruin_count / n

    # First burn month distribution
    burn_months = [
        float(e["first_burn_month"])
        for e in eval_list
        if e.get("first_burn_month") not in (None, "never")
        and isinstance(e.get("first_burn_month"), int)
    ]
    never_pct = (n - len(burn_months)) / n
    if burn_months:
        fbm = {
            "p10": _percentile(burn_months, 10.0),
            "p50": _percentile(burn_months, 50.0),
            "p90": _percentile(burn_months, 90.0),
            "never_pct": never_pct,
        }
    else:
        fbm = {"p10": 0.0, "p50": 0.0, "p90": 0.0, "never_pct": 1.0}

    # Final CRR distribution
    final_crrs = [e["final_crr"] for e in eval_list]
    mean_crr = sum(final_crrs) / n
    variance = sum((x - mean_crr) ** 2 for x in final_crrs) / n
    fcd = {
        "p10": _percentile(final_crrs, 10.0),
        "p50": _percentile(final_crrs, 50.0),
        "p90": _percentile(final_crrs, 90.0),
        "mean": mean_crr,
        "std": math.sqrt(variance),
    }

    per_sample = list(eval_list) if include_per_sample else []

    return {
        "n_samples": n,
        "crr_trajectory": {"p10": p10_traj, "p50": p50_traj, "p90": p90_traj},
        "p_burn_activates": {
            "within_12mo": burn_within(12),
            "within_24mo": burn_within(24),
            "within_36mo": burn_within(36),
            "within_48mo": burn_within(48),
            "within_60mo": burn_within(60),
        },
        "p_ruin": p_ruin,
        "first_burn_month_distribution": fbm,
        "final_crr_distribution": fcd,
        "per_sample_summaries": per_sample,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_monte_carlo(
    base_params: dict,
    mc_config: dict,
    n_samples: int,
    seed: int | None = None,
    include_per_sample: bool = False,
) -> dict:
    """
    Run n_samples Monte Carlo iterations using the Python simulation engine.

    Parameters
    ----------
    base_params : dict
        Full params dict (scenario + constants), same schema as Rust engine.
    mc_config : dict
        Distribution overrides dict, same schema as Rust MCDistributionConfig.
    n_samples : int
        Number of samples to run.
    seed : int | None
        RNG seed for reproducibility. None = random.
    include_per_sample : bool
        If True, include per-sample evaluate() results in output.

    Returns
    -------
    dict
        Same output schema as adbp2_mc.run_monte_carlo().
    """
    import importlib
    import sys as _sys

    # Lazy import to avoid sys.stdout mutation at module level in pytest
    if "simulate" in _sys.modules:
        sim = _sys.modules["simulate"]
    else:
        import importlib.util as _ilu
        import os as _os

        spec_path = _os.path.join(_os.path.dirname(__file__), "simulate.py")
        spec = _ilu.spec_from_file_location("simulate", spec_path)
        sim = _ilu.module_from_spec(spec)
        _sys.modules["simulate"] = sim
        spec.loader.exec_module(sim)

    rng = random.Random(seed)
    simulation_months = base_params["simulation_months"]
    results = []

    for _ in range(n_samples):
        sampled = _sample_params(base_params, mc_config, rng)
        with _patched_simulate(sim, sampled):
            records, failure_reason = sim.run_simulation()
            eval_result = sim.evaluate(records, failure_reason)
        results.append((records, failure_reason, eval_result))

    return _summarize(results, simulation_months, include_per_sample)
