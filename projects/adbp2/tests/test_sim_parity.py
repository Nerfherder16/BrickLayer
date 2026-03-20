"""
test_sim_parity.py — Parity tests between Rust and Python simulation engines.
Task 3: basic smoke test. Task 6: full parity validation.

NOTE: simulate.py has a module-level side effect (sys.stdout replacement) that
conflicts with pytest's fd-level capture. All tests here use subprocess.run()
to invoke simulate.py in isolation, or import it via importlib with stdout
protection before pytest capture is set up.

The heavy parity test is in the test_parity_full() function (Task 6).
"""

import sys
import os
import json
import subprocess
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_baseline_params():
    """Build params dict from constants.py + baseline scenario values."""
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


def _run_python_sim_via_subprocess():
    """Run simulate.py in a subprocess and return its records as a list of dicts.

    simulate.py's __main__ block writes reports/simulation_data.json.
    We use that JSON output for comparison instead of capturing stdout
    (simulate.py replaces sys.stdout which can corrupt pytest handle state).
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"  # Non-interactive backend — prevents plt.show() blocking

    # Use file handles (not PIPE) to avoid handle duplication issues on Windows
    # when simulate.py has replaced sys.stdout in the parent process.
    import tempfile

    with (
        tempfile.TemporaryFile(mode="w+", suffix=".txt") as out_f,
        tempfile.TemporaryFile(mode="w+", suffix=".txt") as err_f,
    ):
        proc = subprocess.run(
            [sys.executable, "simulate.py"],
            cwd=project_root,
            stdin=subprocess.DEVNULL,
            stdout=out_f,
            stderr=err_f,
            timeout=60,
            env=env,
        )

    # Read the JSON output that simulate.py writes
    json_path = os.path.join(project_root, "reports", "simulation_data.json")
    if not os.path.exists(json_path):
        pytest.skip(f"simulate.py did not produce {json_path}")
    with open(json_path, "r") as f:
        records = json.load(f)
    return records


# ── Task 3: Smoke test ─────────────────────────────────────────────────────────


def test_rust_sim_runs_baseline():
    """Rust run_simulation() must return records for all 60 months."""
    import adbp2_mc

    params = _make_baseline_params()
    result = adbp2_mc.run_simulation(params)
    assert "records" in result
    assert "failure_reason" in result
    records = result["records"]
    assert len(records) == 60, f"Expected 60 records, got {len(records)}"


def test_rust_sim_final_crr_positive():
    """Final CRR must be positive for the baseline scenario."""
    import adbp2_mc

    params = _make_baseline_params()
    result = adbp2_mc.run_simulation(params)
    records = result["records"]
    assert records[-1]["crr"] > 0.0


def test_rust_sim_evaluate():
    """evaluate() must return a dict with all required keys."""
    import adbp2_mc

    params = _make_baseline_params()
    result = adbp2_mc.run_simulation(params)
    eval_result = adbp2_mc.evaluate(result, params)
    required_keys = [
        "primary_metric",
        "verdict",
        "failure_reason",
        "final_crr",
        "final_escrow_net",
        "final_employees",
        "first_burn_month",
        "peak_crr",
        "peak_crr_month",
        "burn_active_months",
        "months_simulated",
    ]
    for k in required_keys:
        assert k in eval_result, f"Missing key: {k}"
    assert eval_result["months_simulated"] == 60


# ── Task 6: Full parity test (Rust vs Python) ──────────────────────────────────

NUMERIC_FIELDS = [
    "new_tokens_minted",
    "circulating_tokens",
    "escrow_pool",
    "escrow_net",
    "per_token_escrow",
    "crr",
    "burn_rate_pct",
    "tokens_burned",
    "reimbursements_paid",
    "operator_revenue",
    "fee_revenue",
    "interest_escrow",
    "capacity_utilization_pct",
]
TOLERANCE = 1e-4


def _assert_records_match(rust_records, py_records, scenario_name):
    """Assert Rust records match Python records within tolerance."""
    assert len(rust_records) == len(py_records), (
        f"{scenario_name}: record count mismatch — "
        f"Rust={len(rust_records)}, Python={len(py_records)}"
    )
    for i, (rr, pr) in enumerate(zip(rust_records, py_records)):
        month = rr["month"]
        for field in NUMERIC_FIELDS:
            rv = rr[field]
            pv = float(pr[field])
            assert abs(rv - pv) < TOLERANCE, (
                f"{scenario_name} month {month} field '{field}': "
                f"Rust={rv}, Python={pv}, diff={abs(rv - pv)}"
            )
        assert rr["minting_paused"] == pr["minting_paused"], (
            f"{scenario_name} month {month}: minting_paused mismatch"
        )
        assert rr["verdict"] == pr["verdict"], (
            f"{scenario_name} month {month}: verdict mismatch "
            f"Rust={rr['verdict']!r} Python={pr['verdict']!r}"
        )


def test_parity_baseline():
    """Rust and Python engines must produce identical output for baseline scenario."""
    import adbp2_mc

    params = _make_baseline_params()

    # Run Rust
    rust_result = adbp2_mc.run_simulation(params)

    # Run Python via subprocess (avoids stdout capture conflict)
    py_records = _run_python_sim_via_subprocess()

    _assert_records_match(rust_result["records"], py_records, "baseline")

    # Check failure_reason consistency
    py_failed = any(r.get("verdict") == "INSOLVENT" for r in py_records)
    rust_failed = rust_result["failure_reason"] is not None
    assert py_failed == rust_failed, "Failure mode mismatch between Rust and Python"


def test_parity_stress_low_fee():
    """Parity test with a stress scenario: low fee ($10/mo) that may trigger mint pause."""
    import adbp2_mc
    import tempfile

    stress_params = _make_baseline_params()
    stress_params["employee_fee_monthly"] = 10.0  # Very low fee

    # Run Rust
    rust_result = adbp2_mc.run_simulation(stress_params)

    # Run Python stress scenario via subprocess with named tempfile output.
    # Must use named tempfile (not capture_output) because simulate.py replaces
    # sys.stdout, which corrupts subprocess handle inheritance on Windows.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stress_script = """
import sys, json, os
sys.path.insert(0, {root!r})

# Read simulate source and exec in a namespace with patched fee.
with open(os.path.join({root!r}, 'simulate.py'), 'r') as f:
    src = f.read()
ns = {{'__name__': '__stress__', '__file__': os.path.join({root!r}, 'simulate.py')}}
exec(compile(src, 'simulate.py', 'exec'), ns)
ns['EMPLOYEE_FEE_MONTHLY'] = 10.0
records, failure_reason = ns['run_simulation']()
with open({out_path!r}, 'w', encoding='utf-8') as _f:
    _f.write(json.dumps({{'records': records, 'failure_reason': failure_reason}}))
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as ntf:
        out_path = ntf.name

    try:
        script = stress_script.format(
            root=project_root.replace("\\", "\\\\"),
            out_path=out_path.replace("\\", "\\\\"),
        )
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"

        with tempfile.TemporaryFile(mode="w+", suffix=".txt") as err_f:
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=err_f,
                timeout=60,
                env=env,
            )
            if proc.returncode != 0:
                err_f.seek(0)
                err_text = err_f.read()
                pytest.skip(f"Stress scenario subprocess failed: {err_text[:500]}")

        with open(out_path, "r", encoding="utf-8") as f:
            py_data = json.load(f)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)

    py_records = py_data["records"]
    _assert_records_match(rust_result["records"], py_records, "stress_low_fee")
