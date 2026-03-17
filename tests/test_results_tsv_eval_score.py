"""
tests/test_results_tsv_eval_score.py — C-22 integration: eval_score written to results.tsv.

Covers:
  - update_results_tsv() writes eval_score column
  - header includes eval_score
  - parse_results() (dashboard) reads eval_score back
  - score=None writes empty string, not "None"
  - backward-compat: existing rows without eval_score don't crash dashboard parser
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers that patch cfg so findings.py uses tmp_path files
# ---------------------------------------------------------------------------


def _make_cfg(tmp_path: Path, monkeypatch):
    """Patch bl.config.cfg to point at tmp_path."""
    import bl.config as config_mod

    cfg = config_mod.cfg
    monkeypatch.setattr(cfg, "results_tsv", tmp_path / "results.tsv")
    monkeypatch.setattr(cfg, "questions_md", tmp_path / "questions.md")
    # Write empty questions.md so _mark_question_done doesn't crash
    (tmp_path / "questions.md").write_text("")
    return cfg


# ---------------------------------------------------------------------------
# update_results_tsv — eval_score column
# ---------------------------------------------------------------------------


class TestUpdateResultsTsvEvalScore:
    def test_header_includes_eval_score(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "HEALTHY", "ok", None, 0.95)
        lines = (tmp_path / "results.tsv").read_text().splitlines()
        assert "eval_score" in lines[0]

    def test_eval_score_written_to_row(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "HEALTHY", "ok", None, 0.750)
        lines = (tmp_path / "results.tsv").read_text().splitlines()
        assert "0.750" in lines[1]

    def test_none_score_writes_empty_string(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q2", "FAILURE", "bad", "logic", None)
        lines = (tmp_path / "results.tsv").read_text().splitlines()
        # eval_score field should be empty, not "None"
        parts = lines[1].split("\t")
        headers = lines[0].split("\t")
        score_idx = headers.index("eval_score")
        assert parts[score_idx] == ""

    def test_upsert_updates_score(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "FAILURE", "bad", "logic", 0.3)
        update_results_tsv("Q1", "HEALTHY", "fixed", None, 0.95)
        lines = [
            row
            for row in (tmp_path / "results.tsv").read_text().splitlines()
            if row.strip()
        ]
        # Only one data row (upsert, not append)
        assert len(lines) == 2  # header + 1 row
        assert "0.950" in lines[1]

    def test_score_precision_3_decimal_places(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "HEALTHY", "ok", None, 1.0)
        lines = (tmp_path / "results.tsv").read_text().splitlines()
        assert "1.000" in lines[1]

    def test_column_order(self, tmp_path, monkeypatch):
        """eval_score should be between failure_type and summary."""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "HEALTHY", "ok", None, 0.9)
        headers = (tmp_path / "results.tsv").read_text().splitlines()[0].split("\t")
        ft_idx = headers.index("failure_type")
        es_idx = headers.index("eval_score")
        sm_idx = headers.index("summary")
        assert ft_idx < es_idx < sm_idx


# ---------------------------------------------------------------------------
# Dashboard parse_results — reads eval_score via zip(headers, parts)
# ---------------------------------------------------------------------------


class TestDashboardParsesEvalScore:
    def test_parse_results_reads_eval_score(self, tmp_path, monkeypatch):
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import update_results_tsv

        update_results_tsv("Q1", "HEALTHY", "all good", None, 0.85)

        # Import dashboard parser (needs project root path, not cfg)
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "dashboard_main",
            Path(__file__).parent.parent / "dashboard" / "backend" / "main.py",
        )
        dm = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("dashboard_main", dm)
        spec.loader.exec_module(dm)  # type: ignore[union-attr]

        rows = dm.parse_results(tmp_path)
        assert rows, "Expected at least one result row"
        assert rows[0].get("eval_score") == "0.850"

    def test_parse_results_tolerates_missing_eval_score_column(self, tmp_path):
        """Old TSV without eval_score column doesn't crash the dashboard."""
        tsv = tmp_path / "results.tsv"
        tsv.write_text(
            "question_id\tverdict\tfailure_type\tsummary\ttimestamp\n"
            "Q1\tHEALTHY\t\tall good\t2025-01-01T00:00:00Z\n"
        )

        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "dashboard_main_compat",
            Path(__file__).parent.parent / "dashboard" / "backend" / "main.py",
        )
        dm = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("dashboard_main_compat", dm)
        spec.loader.exec_module(dm)  # type: ignore[union-attr]

        rows = dm.parse_results(tmp_path)
        assert rows, "Expected one result row"
        # eval_score absent — should not raise, just won't be in dict
        assert rows[0].get("eval_score") is None
