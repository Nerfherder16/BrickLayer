"""Tests for masonry/src/training/collector.py"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Make src importable
_MASONRY = Path(__file__).resolve().parents[2]
if str(_MASONRY) not in sys.path:
    sys.path.insert(0, str(_MASONRY))

from src.training.collector import compute_ema, ALPHA, COLD_START


def _write_telemetry(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "telemetry.jsonl"
    with open(p, "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return p


def _output_path(tmp_path: Path) -> Path:
    return tmp_path / "ema_history.json"


class TestComputeEma:
    def test_empty_telemetry_returns_empty_dict(self, tmp_path):
        tel = _write_telemetry(tmp_path, [])
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)
        assert result == {}

    def test_missing_telemetry_file_returns_empty_dict(self, tmp_path):
        out = _output_path(tmp_path)
        result = compute_ema(tmp_path / "nonexistent.jsonl", out)
        assert result == {}

    def test_single_success_from_cold_start(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd", "success": True, "timestamp": "2024-01-01T00:00:00Z"}
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        expected = ALPHA * 1.0 + (1 - ALPHA) * COLD_START
        assert "build" in result
        assert "tdd" in result["build"]
        assert abs(result["build"]["tdd"] - expected) < 1e-9

    def test_single_failure_from_cold_start(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd", "success": False, "timestamp": "2024-01-01T00:00:00Z"}
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        expected = ALPHA * 0.0 + (1 - ALPHA) * COLD_START
        assert abs(result["build"]["tdd"] - expected) < 1e-9

    def test_multiple_records_ema_accumulates(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd", "success": True,  "timestamp": "2024-01-01T00:00:00Z"},
            {"task_type": "build", "strategy": "tdd", "success": False, "timestamp": "2024-01-01T00:01:00Z"},
            {"task_type": "build", "strategy": "tdd", "success": True,  "timestamp": "2024-01-01T00:02:00Z"},
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        ema = COLD_START
        for s in [True, False, True]:
            ema = ALPHA * (1.0 if s else 0.0) + (1 - ALPHA) * ema

        assert abs(result["build"]["tdd"] - ema) < 1e-9

    def test_chronological_sort_applied(self, tmp_path):
        # Records are out of order; result must equal sorted processing
        records = [
            {"task_type": "build", "strategy": "tdd", "success": False, "timestamp": "2024-01-01T00:01:00Z"},
            {"task_type": "build", "strategy": "tdd", "success": True,  "timestamp": "2024-01-01T00:00:00Z"},
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        # Sorted: True then False
        ema = COLD_START
        ema = ALPHA * 1.0 + (1 - ALPHA) * ema
        ema = ALPHA * 0.0 + (1 - ALPHA) * ema

        assert abs(result["build"]["tdd"] - ema) < 1e-9

    def test_multiple_task_types_independent(self, tmp_path):
        records = [
            {"task_type": "build",    "strategy": "tdd",      "success": True,  "timestamp": "2024-01-01T00:00:00Z"},
            {"task_type": "frontend", "strategy": "balanced", "success": False, "timestamp": "2024-01-01T00:01:00Z"},
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        assert "build" in result
        assert "frontend" in result
        assert "tdd" in result["build"]
        assert "balanced" in result["frontend"]

    def test_multiple_strategies_within_task_type(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd",      "success": True,  "timestamp": "2024-01-01T00:00:00Z"},
            {"task_type": "build", "strategy": "balanced", "success": False, "timestamp": "2024-01-01T00:01:00Z"},
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        assert "tdd" in result["build"]
        assert "balanced" in result["build"]
        # They should be independent of each other
        tdd_expected = ALPHA * 1.0 + (1 - ALPHA) * COLD_START
        bal_expected = ALPHA * 0.0 + (1 - ALPHA) * COLD_START
        assert abs(result["build"]["tdd"] - tdd_expected) < 1e-9
        assert abs(result["build"]["balanced"] - bal_expected) < 1e-9

    def test_output_json_written(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd", "success": True, "timestamp": "2024-01-01T00:00:00Z"}
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        compute_ema(tel, out)

        assert out.exists()
        loaded = json.loads(out.read_text())
        assert "build" in loaded
        assert "tdd" in loaded["build"]

    def test_records_missing_fields_are_skipped(self, tmp_path):
        records = [
            {"task_type": "build", "strategy": "tdd"},       # no success
            {"task_type": "build", "success": True},          # no strategy
            {"strategy": "tdd", "success": True},             # no task_type
            {"task_type": "build", "strategy": "tdd", "success": True, "timestamp": "2024-01-01T00:00:00Z"},
        ]
        tel = _write_telemetry(tmp_path, records)
        out = _output_path(tmp_path)
        result = compute_ema(tel, out)

        # Only the last record should contribute
        expected = ALPHA * 1.0 + (1 - ALPHA) * COLD_START
        assert abs(result["build"]["tdd"] - expected) < 1e-9

    def test_cold_start_value_is_correct(self):
        assert COLD_START == 0.688

    def test_alpha_value_is_correct(self):
        assert ALPHA == 0.3
