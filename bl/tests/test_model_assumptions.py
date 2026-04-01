"""Tests for bl/model_assumptions.py"""
from datetime import date


def test_ensure_exists_creates_file(tmp_path):
    from bl.model_assumptions import ensure_exists
    result = ensure_exists(tmp_path)
    assert result == tmp_path / "model_assumptions.md"
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "# Model Assumptions Log" in content
    assert "<!-- Trowel appends below -->" in content


def test_ensure_exists_skips_if_already_present(tmp_path):
    from bl.model_assumptions import ensure_exists
    p = tmp_path / "model_assumptions.md"
    p.write_text("# existing content", encoding="utf-8")
    ensure_exists(tmp_path)
    assert p.read_text(encoding="utf-8") == "# existing content"


def test_append_entry_correct_format(tmp_path):
    from bl.model_assumptions import append_entry
    append_entry(tmp_path, "trowel", "added revenue cap", "REVENUE_CAP", "cap was too high", "D1 D2")
    content = (tmp_path / "model_assumptions.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    assert f"## [{today}] trowel — added revenue cap" in content
    assert "**Changed**: REVENUE_CAP" in content
    assert "**Why**: cap was too high" in content
    assert "**Impact**: D1 D2" in content


def test_append_entry_multiple_in_order(tmp_path):
    from bl.model_assumptions import append_entry
    append_entry(tmp_path, "agent-a", "first change", "param_a", "reason a", "Q1")
    append_entry(tmp_path, "agent-b", "second change", "param_b", "reason b", "Q2")
    content = (tmp_path / "model_assumptions.md").read_text(encoding="utf-8")
    pos_a = content.index("first change")
    pos_b = content.index("second change")
    assert pos_a < pos_b


def test_append_entry_creates_file_if_missing(tmp_path):
    from bl.model_assumptions import append_entry
    assert not (tmp_path / "model_assumptions.md").exists()
    append_entry(tmp_path, "trowel", "summary", "changed", "why", "impact")
    assert (tmp_path / "model_assumptions.md").exists()
