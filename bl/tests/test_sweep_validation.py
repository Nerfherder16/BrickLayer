"""Tests for validate_sweep_parameter in bl/sweep.py"""


SCENARIO_BLOCK = """\
# Some preamble

# SCENARIO PARAMETERS
GROWTH_RATE = 0.05
CHURN_RATE = 0.02
"""

NO_BLOCK = """\
GROWTH_RATE = 0.05
CHURN_RATE = 0.02
"""

PARAM_BEFORE_BLOCK = """\
TARGET_PARAM = 1.0

# SCENARIO PARAMETERS
GROWTH_RATE = 0.05
"""


def _write_simulate(tmp_path, content):
    (tmp_path / "simulate.py").write_text(content, encoding="utf-8")


def test_valid_param_passes(tmp_path):
    from bl.sweep import validate_sweep_parameter
    _write_simulate(tmp_path, SCENARIO_BLOCK)
    ok, msg = validate_sweep_parameter(tmp_path, "GROWTH_RATE")
    assert ok is True
    assert msg == ""


def test_missing_param_fails_with_sweep_blocked(tmp_path):
    from bl.sweep import validate_sweep_parameter
    _write_simulate(tmp_path, SCENARIO_BLOCK)
    ok, msg = validate_sweep_parameter(tmp_path, "MISSING_PARAM")
    assert ok is False
    assert "SWEEP_BLOCKED" in msg
    assert "MISSING_PARAM" in msg


def test_no_scenario_parameters_block_fails(tmp_path):
    from bl.sweep import validate_sweep_parameter
    _write_simulate(tmp_path, NO_BLOCK)
    ok, msg = validate_sweep_parameter(tmp_path, "GROWTH_RATE")
    assert ok is False
    assert "SWEEP_BLOCKED" in msg


def test_param_before_block_does_not_count(tmp_path):
    from bl.sweep import validate_sweep_parameter
    _write_simulate(tmp_path, PARAM_BEFORE_BLOCK)
    ok, msg = validate_sweep_parameter(tmp_path, "TARGET_PARAM")
    assert ok is False
    assert "SWEEP_BLOCKED" in msg


def test_no_simulate_file_fails(tmp_path):
    from bl.sweep import validate_sweep_parameter
    ok, msg = validate_sweep_parameter(tmp_path, "ANY_PARAM")
    assert ok is False
    assert "SWEEP_BLOCKED" in msg
