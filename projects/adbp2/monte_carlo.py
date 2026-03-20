"""
monte_carlo.py — Monte Carlo wrapper for ADBP v2.

User-facing entry point for stochastic scenario analysis. Reads scenario
parameters from simulate.py module globals, reads system constants from
constants.py, and delegates to the Rust engine (adbp2_mc) or falls back
to the pure-Python engine (mc_fallback) transparently.

Build
-----
    pip install maturin
    maturin build --release
    pip install target/wheels/*.whl --force-reinstall

Run
---
    python monte_carlo.py --samples 10000 --seed 42
    python monte_carlo.py --samples 1000

Fallback
--------
If the Rust extension (adbp2_mc) cannot be imported, mc_fallback.py is
used automatically. The output schema is identical in both cases. The
active engine is printed at startup.

Output
------
- reports/mc_results.json   Full MC output, pretty-printed.
- results.tsv               Appended row: run_type=MC, key summary stats.
"""

from __future__ import annotations

import csv
import json
import os
import sys

# ---------------------------------------------------------------------------
# Engine selection
# ---------------------------------------------------------------------------

try:
    import adbp2_mc as _engine

    _USE_RUST = True
    _ENGINE_NAME = "rust"
except ImportError:
    import mc_fallback as _engine  # type: ignore[no-redef]

    _USE_RUST = False
    _ENGINE_NAME = "python"

# ---------------------------------------------------------------------------
# Default MC distribution config
# ---------------------------------------------------------------------------

_DEFAULT_MC_CONFIG = {
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


# ---------------------------------------------------------------------------
# Parameter assembly
# ---------------------------------------------------------------------------


def _build_params() -> dict:
    """Pack simulate.py scenario params + constants.py into a flat dict."""
    import constants as c

    # Import simulate lazily to avoid capturing the sys.stdout replacement
    # in non-__main__ contexts (e.g., when imported from tests).
    import importlib.util as _ilu

    _sim_path = os.path.join(os.path.dirname(__file__), "simulate.py")
    if "simulate" in sys.modules:
        sim = sys.modules["simulate"]
    else:
        spec = _ilu.spec_from_file_location("simulate", _sim_path)
        sim = _ilu.module_from_spec(spec)
        sys.modules["simulate"] = sim
        spec.loader.exec_module(sim)

    return {
        # Scenario parameters from simulate.py
        "employee_fee_monthly": float(sim.EMPLOYEE_FEE_MONTHLY),
        "vendor_capacity_per_employee": float(sim.VENDOR_CAPACITY_PER_EMPLOYEE),
        "simulation_months": int(sim.SIMULATION_MONTHS),
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(
    n_samples: int = 10_000,
    seed: int | None = None,
    mc_config: dict | None = None,
    include_per_sample: bool = False,
) -> dict:
    """
    Run Monte Carlo simulation and return the result dict.

    Parameters
    ----------
    n_samples : int
        Number of Monte Carlo samples. Default: 10,000.
    seed : int | None
        RNG seed for reproducibility. None = random.
    mc_config : dict | None
        Distribution overrides. None = use sensible defaults.
    include_per_sample : bool
        If True, include per-sample evaluate() results in output.

    Returns
    -------
    dict
        MC output dict with keys: n_samples, crr_trajectory,
        p_burn_activates, p_ruin, first_burn_month_distribution,
        final_crr_distribution, per_sample_summaries.
    """
    params = _build_params()
    config = mc_config if mc_config is not None else _DEFAULT_MC_CONFIG

    if _USE_RUST:
        result = _engine.run_monte_carlo(
            params, config, n_samples, seed=seed, include_per_sample=include_per_sample
        )
    else:
        result = _engine.run_monte_carlo(
            params, config, n_samples, seed=seed, include_per_sample=include_per_sample
        )

    return result


def write_outputs(result: dict, seed: int | None = None) -> None:
    """
    Write MC results to reports/mc_results.json and append a row to results.tsv.

    Parameters
    ----------
    result : dict
        The dict returned by run().
    seed : int | None
        The seed used for the run (included in the TSV row).
    """
    os.makedirs("reports", exist_ok=True)

    # Full JSON output
    json_path = os.path.join("reports", "mc_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Summary TSV row
    tsv_path = "results.tsv"
    fieldnames = [
        "run_type",
        "n_samples",
        "p50_final_crr",
        "p10_final_crr",
        "p90_final_crr",
        "p_ruin",
        "p_burn_12mo",
        "seed",
        "engine",
    ]
    row = {
        "run_type": "MC",
        "n_samples": result["n_samples"],
        "p50_final_crr": result["final_crr_distribution"]["p50"],
        "p10_final_crr": result["final_crr_distribution"]["p10"],
        "p90_final_crr": result["final_crr_distribution"]["p90"],
        "p_ruin": result["p_ruin"],
        "p_burn_12mo": result["p_burn_activates"]["within_12mo"],
        "seed": seed if seed is not None else "random",
        "engine": _ENGINE_NAME,
    }

    write_header = not os.path.exists(tsv_path)
    with open(tsv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _print_summary(result: dict, seed: int | None = None) -> None:
    """Print a human-readable summary of the MC result."""
    fcd = result["final_crr_distribution"]
    burn = result["p_burn_activates"]
    fbm = result["first_burn_month_distribution"]
    print(f"\nEngine: {'Rust (adbp2_mc)' if _USE_RUST else 'Python fallback'}")
    print(
        f"Samples: {result['n_samples']}  Seed: {seed if seed is not None else 'random'}"
    )
    print(f"\nFinal CRR Distribution:")
    print(f"  P10={fcd['p10']:.4f}  P50={fcd['p50']:.4f}  P90={fcd['p90']:.4f}")
    print(f"  Mean={fcd['mean']:.4f}  Std={fcd['std']:.4f}")
    print(f"\nP(ruin):           {result['p_ruin']:.4f}")
    print(f"P(burn ≤12mo):    {burn['within_12mo']:.4f}")
    print(f"P(burn ≤24mo):    {burn['within_24mo']:.4f}")
    print(f"P(burn ≤60mo):    {burn['within_60mo']:.4f}")
    print(f"\nFirst burn month (of samples with burn):")
    print(f"  P10={fbm['p10']:.1f}  P50={fbm['p50']:.1f}  P90={fbm['p90']:.1f}")
    print(f"  Never activated: {fbm['never_pct']:.1%}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="ADBP v2 Monte Carlo simulation runner"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10_000,
        help="Number of MC samples (default: 10000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducibility (default: random)",
    )
    args = parser.parse_args()

    result = run(n_samples=args.samples, seed=args.seed)
    _print_summary(result, seed=args.seed)
    write_outputs(result, seed=args.seed)
    print(f"\nOutputs written to reports/mc_results.json and results.tsv")
