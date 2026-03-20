"""
test_params.py — Tests for module loading, SimParams, and MCDistributionConfig.
Extends across Tasks 1, 2, 4, and 8.
"""

import pytest


# ── Task 1: Module smoke test ──────────────────────────────────────────────────

def test_module_loads():
    """The Rust extension must be importable."""
    import adbp2_mc  # noqa: F401


def test_hello():
    """hello() must return the exact sentinel string."""
    import adbp2_mc
    assert adbp2_mc.hello() == "adbp2_mc loaded"
