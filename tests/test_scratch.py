"""
tests/test_scratch.py — Tests for bl/scratch.py (typed signal board).

Tests written before implementation. All must fail until developer completes task.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bl.scratch import (  # noqa: E402  — will fail until implemented
    load_scratch,
    parse_signals,
    render_scratch,
    save_scratch,
    trim_scratch,
)


# ---------------------------------------------------------------------------
# parse_signals
# ---------------------------------------------------------------------------


class TestParseSignals:
    def test_returns_watch_signal(self):
        text = "Some findings here.\n[SIGNAL: WATCH -- admin_fee near cliff at 3.5%]\nMore text."
        result = parse_signals(text)
        assert len(result) == 1
        assert result[0]["type"] == "WATCH"
        assert result[0]["signal"] == "admin_fee near cliff at 3.5%"

    def test_returns_block_signal(self):
        text = "[SIGNAL: BLOCK -- regulatory approval required before launch]"
        result = parse_signals(text)
        assert len(result) == 1
        assert result[0]["type"] == "BLOCK"
        assert result[0]["signal"] == "regulatory approval required before launch"

    def test_returns_data_signal(self):
        text = "[SIGNAL: DATA -- median churn observed at 4.2% across comparables]"
        result = parse_signals(text)
        assert len(result) == 1
        assert result[0]["type"] == "DATA"

    def test_returns_resolved_signal(self):
        text = "[SIGNAL: RESOLVED -- admin_fee cliff confirmed and model updated]"
        result = parse_signals(text)
        assert len(result) == 1
        assert result[0]["type"] == "RESOLVED"

    def test_ignores_unknown_type(self):
        text = "[SIGNAL: UNKNOWN -- some message]\n[SIGNAL: WATCH -- valid one]"
        result = parse_signals(text)
        assert len(result) == 1
        assert result[0]["type"] == "WATCH"

    def test_multiple_signals_in_one_text(self):
        text = (
            "[SIGNAL: WATCH -- first watch]\n"
            "[SIGNAL: DATA -- a data point]\n"
            "[SIGNAL: BLOCK -- a blocker]"
        )
        result = parse_signals(text)
        assert len(result) == 3
        types = {r["type"] for r in result}
        assert types == {"WATCH", "DATA", "BLOCK"}

    def test_source_and_date_are_empty_strings(self):
        text = "[SIGNAL: WATCH -- some concern]"
        result = parse_signals(text)
        assert result[0]["source"] == ""
        assert result[0]["date"] == ""

    def test_returns_empty_list_when_no_signals(self):
        text = "This finding has no signal lines at all."
        result = parse_signals(text)
        assert result == []

    def test_returns_empty_list_on_empty_string(self):
        result = parse_signals("")
        assert result == []

    def test_signal_message_is_stripped(self):
        text = "[SIGNAL: WATCH --   leading and trailing spaces   ]"
        result = parse_signals(text)
        assert result[0]["signal"] == "leading and trailing spaces"

    def test_signal_dict_has_required_keys(self):
        text = "[SIGNAL: DATA -- something]"
        result = parse_signals(text)
        assert set(result[0].keys()) == {"signal", "type", "source", "date"}

    def test_case_sensitive_type_matching(self):
        """Types must be uppercase; lowercase variant is not a valid type."""
        text = "[SIGNAL: watch -- lowercase type should be ignored]"
        result = parse_signals(text)
        assert result == []

    def test_signal_with_double_dash_in_message(self):
        """Messages that contain -- should not be truncated at the second --."""
        text = "[SIGNAL: DATA -- range is 1.2--1.8 per unit]"
        result = parse_signals(text)
        assert len(result) == 1
        assert "1.2" in result[0]["signal"]


# ---------------------------------------------------------------------------
# load_scratch / save_scratch
# ---------------------------------------------------------------------------


class TestLoadScratch:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        path = tmp_path / "scratch.md"
        result = load_scratch(path)
        assert result == []

    def test_loads_rows_written_by_save_scratch(self, tmp_path):
        path = tmp_path / "scratch.md"
        rows = [
            {"signal": "admin_fee cliff at 3.5%", "type": "WATCH", "source": "Q1.3", "date": "2026-03-20"},
            {"signal": "churn data from comp set", "type": "DATA", "source": "Q2.1", "date": "2026-03-19"},
        ]
        save_scratch(path, rows)
        loaded = load_scratch(path)
        assert len(loaded) == 2
        assert loaded[0]["signal"] == "admin_fee cliff at 3.5%"
        assert loaded[0]["type"] == "WATCH"
        assert loaded[1]["type"] == "DATA"

    def test_loaded_rows_have_all_keys(self, tmp_path):
        path = tmp_path / "scratch.md"
        rows = [
            {"signal": "test signal", "type": "BLOCK", "source": "Q3.1", "date": "2026-03-18"}
        ]
        save_scratch(path, rows)
        loaded = load_scratch(path)
        assert set(loaded[0].keys()) == {"signal", "type", "source", "date"}

    def test_round_trip_preserves_all_fields(self, tmp_path):
        path = tmp_path / "scratch.md"
        rows = [
            {"signal": "pipe | character in message", "type": "DATA", "source": "Q4.0", "date": "2026-03-17"},
        ]
        save_scratch(path, rows)
        loaded = load_scratch(path)
        assert loaded[0]["source"] == "Q4.0"
        assert loaded[0]["date"] == "2026-03-17"


class TestSaveScratch:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "scratch.md"
        save_scratch(path, [])
        assert path.exists()

    def test_file_contains_header(self, tmp_path):
        path = tmp_path / "scratch.md"
        save_scratch(path, [])
        content = path.read_text()
        assert "# Campaign Scratch Pad" in content

    def test_file_contains_table_header(self, tmp_path):
        path = tmp_path / "scratch.md"
        save_scratch(path, [])
        content = path.read_text()
        assert "| # |" in content
        assert "Signal" in content
        assert "Type" in content

    def test_file_contains_row_data(self, tmp_path):
        path = tmp_path / "scratch.md"
        rows = [{"signal": "fee sensitivity", "type": "WATCH", "source": "Q1.1", "date": "2026-03-20"}]
        save_scratch(path, rows)
        content = path.read_text()
        assert "fee sensitivity" in content
        assert "WATCH" in content
        assert "Q1.1" in content

    def test_overwrites_existing_file(self, tmp_path):
        path = tmp_path / "scratch.md"
        save_scratch(path, [{"signal": "old signal", "type": "DATA", "source": "", "date": ""}])
        save_scratch(path, [{"signal": "new signal", "type": "BLOCK", "source": "", "date": ""}])
        content = path.read_text()
        assert "new signal" in content
        assert "old signal" not in content

    def test_rows_numbered_sequentially(self, tmp_path):
        path = tmp_path / "scratch.md"
        rows = [
            {"signal": "first", "type": "WATCH", "source": "", "date": ""},
            {"signal": "second", "type": "DATA", "source": "", "date": ""},
            {"signal": "third", "type": "BLOCK", "source": "", "date": ""},
        ]
        save_scratch(path, rows)
        content = path.read_text()
        assert "| 1 |" in content
        assert "| 2 |" in content
        assert "| 3 |" in content


# ---------------------------------------------------------------------------
# trim_scratch
# ---------------------------------------------------------------------------


class TestTrimScratch:
    def _make_row(self, signal: str, sig_type: str) -> dict:
        return {"signal": signal, "type": sig_type, "source": "", "date": ""}

    def test_no_trim_when_under_cap(self):
        rows = [self._make_row(f"signal {i}", "WATCH") for i in range(10)]
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 10

    def test_no_trim_exactly_at_cap(self):
        rows = [self._make_row(f"signal {i}", "DATA") for i in range(15)]
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 15

    def test_removes_oldest_resolved_first(self):
        rows = (
            [self._make_row(f"resolved {i}", "RESOLVED") for i in range(3)]
            + [self._make_row(f"data {i}", "DATA") for i in range(10)]
            + [self._make_row(f"watch {i}", "WATCH") for i in range(5)]
        )
        # 18 total, cap 15 → remove 3 oldest (RESOLVED entries)
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 15
        # All RESOLVED entries should be gone (oldest 3 are exactly the RESOLVED ones)
        remaining_types = [r["type"] for r in result]
        assert "RESOLVED" not in remaining_types

    def test_removes_data_after_resolved_exhausted(self):
        rows = (
            [self._make_row(f"resolved {i}", "RESOLVED") for i in range(2)]
            + [self._make_row(f"data {i}", "DATA") for i in range(10)]
            + [self._make_row(f"watch {i}", "WATCH") for i in range(6)]
        )
        # 18 total, cap 15 → remove 3; 2 RESOLVED + 1 oldest DATA
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 15
        resolved_remaining = [r for r in result if r["type"] == "RESOLVED"]
        assert len(resolved_remaining) == 0
        data_remaining = [r for r in result if r["type"] == "DATA"]
        assert len(data_remaining) == 9  # 10 - 1

    def test_watch_never_auto_removed(self):
        rows = [self._make_row(f"watch {i}", "WATCH") for i in range(20)]
        result = trim_scratch(rows, max_entries=15)
        # Cannot trim WATCH — result should retain all 20 (no removable candidates)
        assert len(result) == 20

    def test_block_never_auto_removed(self):
        rows = [self._make_row(f"block {i}", "BLOCK") for i in range(20)]
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 20

    def test_trim_preserves_watch_and_block_when_mixed(self):
        rows = (
            [self._make_row(f"watch {i}", "WATCH") for i in range(5)]
            + [self._make_row(f"block {i}", "BLOCK") for i in range(5)]
            + [self._make_row(f"resolved {i}", "RESOLVED") for i in range(3)]
            + [self._make_row(f"data {i}", "DATA") for i in range(5)]
        )
        # 18 total, cap 15 → remove 3 RESOLVED
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 15
        watch_count = sum(1 for r in result if r["type"] == "WATCH")
        block_count = sum(1 for r in result if r["type"] == "BLOCK")
        assert watch_count == 5
        assert block_count == 5

    def test_empty_rows_unchanged(self):
        result = trim_scratch([], max_entries=15)
        assert result == []

    def test_default_cap_is_15(self):
        rows = [self._make_row(f"resolved {i}", "RESOLVED") for i in range(20)]
        result = trim_scratch(rows)
        assert len(result) == 15

    def test_oldest_removed_first_within_type(self):
        """When trimming DATA, the oldest (earliest in list) are removed first."""
        rows = [self._make_row(f"data {i}", "DATA") for i in range(17)]
        result = trim_scratch(rows, max_entries=15)
        assert len(result) == 15
        remaining_signals = [r["signal"] for r in result]
        # The first two ("data 0", "data 1") should be gone
        assert "data 0" not in remaining_signals
        assert "data 1" not in remaining_signals
        # The last one ("data 16") should remain
        assert "data 16" in remaining_signals


# ---------------------------------------------------------------------------
# render_scratch
# ---------------------------------------------------------------------------


class TestRenderScratch:
    def test_returns_string(self):
        result = render_scratch([])
        assert isinstance(result, str)

    def test_contains_table_header_row(self):
        result = render_scratch([])
        assert "| # |" in result
        assert "Signal" in result
        assert "Type" in result
        assert "Source" in result
        assert "Date" in result

    def test_contains_separator_row(self):
        result = render_scratch([])
        assert "|---|" in result or "|--" in result

    def test_contains_row_data(self):
        rows = [{"signal": "fee sensitivity", "type": "WATCH", "source": "Q1.1", "date": "2026-03-20"}]
        result = render_scratch(rows)
        assert "fee sensitivity" in result
        assert "WATCH" in result
        assert "Q1.1" in result
        assert "2026-03-20" in result

    def test_does_not_contain_file_header(self):
        """render_scratch returns only the table, not the # Campaign Scratch Pad header."""
        result = render_scratch([])
        assert "# Campaign Scratch Pad" not in result

    def test_multiple_rows_all_present(self):
        rows = [
            {"signal": "alpha", "type": "WATCH", "source": "Q1", "date": "2026-03-18"},
            {"signal": "beta", "type": "DATA", "source": "Q2", "date": "2026-03-19"},
            {"signal": "gamma", "type": "BLOCK", "source": "Q3", "date": "2026-03-20"},
        ]
        result = render_scratch(rows)
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result

    def test_rows_numbered_in_output(self):
        rows = [
            {"signal": "first", "type": "WATCH", "source": "", "date": ""},
            {"signal": "second", "type": "DATA", "source": "", "date": ""},
        ]
        result = render_scratch(rows)
        assert "| 1 |" in result
        assert "| 2 |" in result
