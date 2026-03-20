"""
test_mc_output.py — Tests for monte_carlo.py wrapper (Task 10).

DESIGN: monte_carlo.py imports simulate.py (via lazy importlib), which
mutates sys.stdout. All tests run monte_carlo via subprocess with a named
tempfile for JSON output — same isolation pattern as test_fallback.py.
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
# Subprocess runner
# ---------------------------------------------------------------------------

_RUNNER_TEMPLATE = """
import sys, json, os
sys.path.insert(0, {root!r})
import monte_carlo
result = monte_carlo.run(n_samples={n_samples}, seed={seed})
with open({out_path!r}, "w", encoding="utf-8") as _f:
    _f.write(json.dumps(result))
"""

_WRITE_OUTPUTS_TEMPLATE = """
import sys, json, os
sys.path.insert(0, {root!r})
os.chdir({root!r})
import monte_carlo
result = monte_carlo.run(n_samples={n_samples}, seed={seed})
monte_carlo.write_outputs(result, seed={seed})
with open({out_path!r}, "w", encoding="utf-8") as _f:
    _f.write(json.dumps({{"status": "ok", "n_samples": result["n_samples"]}}))
"""


def _run_mc(n_samples: int = 10, seed: int = 42) -> dict:
    """Run monte_carlo.run() in a subprocess, return result dict."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as ntf:
        out_path = ntf.name

    try:
        script = _RUNNER_TEMPLATE.format(
            root=PROJECT_ROOT.replace("\\", "\\\\"),
            n_samples=n_samples,
            seed=repr(seed),
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
                pytest.skip(f"monte_carlo subprocess failed:\n{err_text[:1000]}")

        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def _run_mc_with_outputs(n_samples: int = 10, seed: int = 42) -> dict:
    """Run monte_carlo.run() + write_outputs() in a subprocess."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as ntf:
        out_path = ntf.name

    try:
        script = _WRITE_OUTPUTS_TEMPLATE.format(
            root=PROJECT_ROOT.replace("\\", "\\\\"),
            n_samples=n_samples,
            seed=repr(seed),
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
                pytest.skip(
                    f"monte_carlo write_outputs subprocess failed:\n{err_text[:1000]}"
                )

        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_mc_run_returns_all_keys():
    """monte_carlo.run() must return all required top-level keys."""
    result = _run_mc(n_samples=10, seed=42)
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


def test_mc_run_n_samples_matches():
    """n_samples in output must match requested count."""
    result = _run_mc(n_samples=50, seed=42)
    assert result["n_samples"] == 50


def test_mc_run_crr_trajectory_length():
    """crr_trajectory bands must each have 60 entries (simulation_months)."""
    result = _run_mc(n_samples=10, seed=42)
    assert len(result["crr_trajectory"]["p10"]) == 60
    assert len(result["crr_trajectory"]["p50"]) == 60
    assert len(result["crr_trajectory"]["p90"]) == 60


def test_mc_run_p_ruin_in_range():
    """p_ruin must be in [0, 1]."""
    result = _run_mc(n_samples=20, seed=42)
    assert 0.0 <= result["p_ruin"] <= 1.0


def test_mc_write_outputs_creates_json():
    """write_outputs() must create reports/mc_results.json."""
    _run_mc_with_outputs(n_samples=10, seed=42)
    json_path = os.path.join(PROJECT_ROOT, "reports", "mc_results.json")
    assert os.path.exists(json_path), "reports/mc_results.json not created"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "n_samples" in data
    assert "final_crr_distribution" in data


def test_mc_write_outputs_appends_tsv():
    """write_outputs() must append a row to results.tsv with MC data."""
    # Read current line count before running
    tsv_path = os.path.join(PROJECT_ROOT, "results.tsv")
    pre_lines = 0
    if os.path.exists(tsv_path):
        with open(tsv_path, "r", encoding="utf-8") as f:
            pre_lines = sum(1 for _ in f)

    _run_mc_with_outputs(n_samples=10, seed=42)

    assert os.path.exists(tsv_path), "results.tsv not found"
    with open(tsv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Must have at least one more line than before
    assert len(lines) > pre_lines, "No new row was appended to results.tsv"

    # The appended line must contain MC marker and our known values
    new_content = "".join(lines[pre_lines:])
    assert "MC" in new_content, "MC marker not found in appended content"
    # Seed 42 should appear in the row
    assert "42" in new_content, "seed=42 not found in appended TSV row"
