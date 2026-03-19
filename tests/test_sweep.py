"""
tests/test_sweep.py — Tests for bl/sweep.py parameter sweep harness.

Task A1: TDD — tests written first (RED), then implementation (GREEN).
"""

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bl.sweep import sweep  # noqa: E402

TEMPLATE_DIR = REPO_ROOT / "template"


def _copy_template(tmp_path: Path) -> None:
    """Copy simulate.py and constants.py from template into tmp_path."""
    shutil.copy(TEMPLATE_DIR / "simulate.py", tmp_path / "simulate.py")
    shutil.copy(TEMPLATE_DIR / "constants.py", tmp_path / "constants.py")


class TestSweep:
    def test_returns_expected_length(self, tmp_path):
        """sweep with 3 values returns a list of length 3."""
        _copy_template(tmp_path)
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=[100, 300, 500],
        )
        assert len(results) == 3

    def test_result_keys_present(self, tmp_path):
        """Each result dict has all required keys."""
        _copy_template(tmp_path)
        required_keys = {
            "param_name",
            "param_value",
            "scenario",
            "verdict",
            "failure_reason",
            "final_primary",
            "record_count",
            "records",
        }
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=[100, 500],
        )
        for result in results:
            assert required_keys <= set(result.keys()), (
                f"Missing keys: {required_keys - set(result.keys())}"
            )

    def test_param_value_injected(self, tmp_path):
        """param_value in each result matches the corresponding input value."""
        _copy_template(tmp_path)
        values = [100, 250, 500]
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=values,
        )
        returned_values = sorted(r["param_value"] for r in results)
        assert returned_values == sorted(values)

    def test_verdict_populated(self, tmp_path):
        """verdict in each result is one of HEALTHY, WARNING, FAILURE."""
        _copy_template(tmp_path)
        valid_verdicts = {"HEALTHY", "WARNING", "FAILURE"}
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=[50, 500],
        )
        for result in results:
            assert result["verdict"] in valid_verdicts, (
                f"Unexpected verdict: {result['verdict']!r}"
            )

    def test_with_base_params(self, tmp_path):
        """sweep with base_params runs without error and returns results."""
        _copy_template(tmp_path)
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=[200, 400],
            base_params={"SIMULATION_MONTHS": 12},
        )
        assert len(results) == 2
        # With 12 months, record_count should be <= 12
        for result in results:
            assert result["record_count"] <= 12

    def test_multiple_scenarios(self, tmp_path):
        """sweep with 2 values and 2 scenarios returns 4 results (2×2)."""
        _copy_template(tmp_path)
        results = sweep(
            project_dir=tmp_path,
            param_name="INITIAL_UNITS",
            values=[100, 500],
            scenarios=["low", "high"],
        )
        assert len(results) == 4
        scenario_labels = {r["scenario"] for r in results}
        assert scenario_labels == {"low", "high"}
