"""Tests for masonry/src/training/selector.py"""

import json
import sys
from pathlib import Path


_MASONRY = Path(__file__).resolve().parents[2]
if str(_MASONRY) not in sys.path:
    sys.path.insert(0, str(_MASONRY))

from src.training import selector as sel_module


def _patch_history_path(monkeypatch, tmp_path, data: dict):
    """Write ema_history.json to tmp_path and patch the module's path constant."""
    p = tmp_path / "ema_history.json"
    p.write_text(json.dumps(data))
    monkeypatch.setattr(sel_module, "_EMA_HISTORY_PATH", p)


class TestSelectStrategy:
    def test_returns_highest_ema_strategy(self, monkeypatch, tmp_path):
        data = {
            "build": {
                "tdd": 0.9,
                "balanced": 0.6,
                "exploratory": 0.7,
            }
        }
        _patch_history_path(monkeypatch, tmp_path, data)
        assert sel_module.select_strategy("build") == "tdd"

    def test_returns_balanced_when_no_task_type_history(self, monkeypatch, tmp_path):
        data = {"frontend": {"tdd": 0.8}}
        _patch_history_path(monkeypatch, tmp_path, data)
        assert sel_module.select_strategy("build") == "balanced"

    def test_returns_balanced_when_history_file_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sel_module, "_EMA_HISTORY_PATH", tmp_path / "nonexistent.json")
        assert sel_module.select_strategy("build") == "balanced"

    def test_returns_balanced_when_history_file_empty_dict(self, monkeypatch, tmp_path):
        _patch_history_path(monkeypatch, tmp_path, {})
        assert sel_module.select_strategy("build") == "balanced"

    def test_single_strategy_is_selected(self, monkeypatch, tmp_path):
        data = {"frontend": {"tdd": 0.5}}
        _patch_history_path(monkeypatch, tmp_path, data)
        assert sel_module.select_strategy("frontend") == "tdd"

    def test_ties_resolved_deterministically(self, monkeypatch, tmp_path):
        # Both strategies have the same score — must not raise, must return one of them
        data = {"build": {"tdd": 0.7, "balanced": 0.7}}
        _patch_history_path(monkeypatch, tmp_path, data)
        result = sel_module.select_strategy("build")
        assert result in ("tdd", "balanced")

    def test_multiple_task_types_independent(self, monkeypatch, tmp_path):
        data = {
            "build": {"tdd": 0.9, "balanced": 0.5},
            "frontend": {"tdd": 0.4, "balanced": 0.95},
        }
        _patch_history_path(monkeypatch, tmp_path, data)
        assert sel_module.select_strategy("build") == "tdd"
        assert sel_module.select_strategy("frontend") == "balanced"

    def test_corrupt_json_falls_back_to_balanced(self, monkeypatch, tmp_path):
        p = tmp_path / "ema_history.json"
        p.write_text("not valid json {{{")
        monkeypatch.setattr(sel_module, "_EMA_HISTORY_PATH", p)
        assert sel_module.select_strategy("build") == "balanced"
