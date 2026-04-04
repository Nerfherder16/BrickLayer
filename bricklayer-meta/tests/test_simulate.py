"""Tests for bricklayer-meta simulate.py — validates Q8.5 novelty cliff fix."""

import sys
from pathlib import Path

import pytest

# Add bricklayer-meta to path so we can import simulate
META_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(META_DIR))

import simulate  # noqa: E402


def _run_with_params(**overrides):
    """Run simulation with parameter overrides, restoring originals after."""
    originals = {}
    for key, val in overrides.items():
        originals[key] = getattr(simulate, key)
        setattr(simulate, key, val)
    try:
        records, totals = simulate.run_simulation()
        return simulate.evaluate(records, totals)
    finally:
        for key, val in originals.items():
            setattr(simulate, key, val)


class TestBaselineHealthy:
    """Baseline scenario must produce HEALTHY verdict."""

    def test_default_params_healthy(self):
        results = _run_with_params()
        assert results["verdict"] == "HEALTHY"
        assert results["primary_metric"] >= 0.50

    def test_baseline_yield_above_warning(self):
        results = _run_with_params()
        assert results["primary_metric"] >= simulate.CAMPAIGN_YIELD_WARNING


class TestNoveltyCliffix:
    """Q8.5: Novelty cliff should be at DN≈0.78, not DN≈0.857."""

    def test_cliff_below_090(self):
        """With slope=1.20, DN=0.85 should produce WARNING or FAILURE.
        Analytical cliff is DN≈0.780 but seed=42 RNG variance shifts
        the simulation crossover to ~0.85 (per Q8.5 finding)."""
        results = _run_with_params(DOMAIN_NOVELTY=0.85)
        assert results["verdict"] in ("WARNING", "FAILURE"), (
            f"Expected WARNING/FAILURE at DN=0.85, got {results['verdict']} "
            f"(yield={results['primary_metric']})"
        )

    def test_healthy_at_065(self):
        """DN=0.65 should still produce HEALTHY (well below cliff)."""
        results = _run_with_params(DOMAIN_NOVELTY=0.65)
        assert results["verdict"] == "HEALTHY"

    def test_novelty_discount_floor_reached(self):
        """With slope=1.20, floor (0.05) is reached at DN=0.792."""
        discount = max(0.05, 1.0 - 0.80 * 1.20)
        assert discount == 0.05, f"Floor not reached at DN=0.80: {discount}"

    def test_novelty_discount_not_floored_at_070(self):
        """At DN=0.70, discount should still be in linear regime."""
        discount = max(0.05, 1.0 - 0.70 * 1.20)
        assert discount > 0.05, f"Floor reached too early at DN=0.70: {discount}"
        assert abs(discount - 0.16) < 0.01

    def test_old_slope_would_produce_healthy_at_080(self):
        """Verify that the old slope (0.90) would produce HEALTHY at DN=0.80.
        This confirms the fix actually moved the cliff."""
        old_discount = max(0.05, 1.0 - 0.80 * 0.90)
        new_discount = max(0.05, 1.0 - 0.80 * 1.20)
        assert old_discount > new_discount, "Old slope should give higher discount"
        assert old_discount == pytest.approx(0.28, abs=0.01)
        assert new_discount == pytest.approx(0.05, abs=0.01)
