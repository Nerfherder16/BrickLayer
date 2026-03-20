"""
tests/test_findings_confidence.py — TDD for Phase 6 Task 1: confidence float + needs_human fields.

Covers:
  - write_finding() writes **Confidence** and **Needs Human** to finding file
  - _CONFIDENCE_FLOAT mapping: high→0.9, medium→0.6, low→0.3, uncertain→0.1
  - needs_human threshold: < 0.35 → True, >= 0.35 → False
  - C-30 path: code_audit + high confidence → capped to medium → 0.6
  - Missing confidence key defaults to uncertain → 0.1 / needs_human True
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cfg(tmp_path: Path, monkeypatch):
    """Patch bl.config.cfg to point findings_dir at tmp_path."""
    import bl.config as config_mod

    cfg = config_mod.cfg
    monkeypatch.setattr(cfg, "findings_dir", tmp_path / "findings")
    (tmp_path / "findings").mkdir(exist_ok=True)
    return cfg


def _minimal_question(qid: str = "Q1.1", question_type: str = "behavioral") -> dict:
    return {
        "id": qid,
        "title": "Test question title",
        "hypothesis": "Does the system behave correctly?",
        "mode": "simulate",
        "operational_mode": "simulate",
        "target": "test_target",
        "verdict_threshold": "FAILURE if x < 0",
        "question_type": question_type,
    }


def _minimal_result(
    verdict: str = "HEALTHY", confidence: str | None = "medium"
) -> dict:
    r: dict = {
        "verdict": verdict,
        "summary": "All good",
        "details": "No issues detected.",
        "data": {"key": "value"},
    }
    if confidence is not None:
        r["confidence"] = confidence
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFindingsConfidenceFloat:
    def test_high_confidence_writes_09_and_false(self, tmp_path, monkeypatch):
        """confidence=high → **Confidence**: 0.9 and **Needs Human**: False"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence="high")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.9" in content
        assert "**Needs Human**: False" in content

    def test_uncertain_confidence_writes_01_and_true(self, tmp_path, monkeypatch):
        """confidence=uncertain → **Confidence**: 0.1 and **Needs Human**: True"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence="uncertain")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.1" in content
        assert "**Needs Human**: True" in content

    def test_low_confidence_needs_human_true(self, tmp_path, monkeypatch):
        """confidence=low → 0.3 < 0.35 → **Needs Human**: True"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence="low")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.3" in content
        assert "**Needs Human**: True" in content

    def test_medium_confidence_needs_human_false(self, tmp_path, monkeypatch):
        """confidence=medium → 0.6 >= 0.35 → **Needs Human**: False"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence="medium")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.6" in content
        assert "**Needs Human**: False" in content

    def test_code_audit_caps_high_to_medium(self, tmp_path, monkeypatch):
        """C-30: code_audit + confidence=high → capped to medium → **Confidence**: 0.6"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question(question_type="code_audit")
        r = _minimal_result(verdict="WARNING", confidence="high")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.6" in content
        assert "**Needs Human**: False" in content

    def test_missing_confidence_key_defaults_to_uncertain(self, tmp_path, monkeypatch):
        """No confidence key in result → defaults to uncertain → 0.1 / True"""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence=None)  # no "confidence" key
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        assert "**Confidence**: 0.1" in content
        assert "**Needs Human**: True" in content

    def test_confidence_fields_appear_before_summary(self, tmp_path, monkeypatch):
        """Both new fields appear before the ## Summary section."""
        _make_cfg(tmp_path, monkeypatch)
        from bl.findings import write_finding

        q = _minimal_question()
        r = _minimal_result(confidence="high")
        path = write_finding(q, r)
        content = path.read_text(encoding="utf-8")
        conf_pos = content.index("**Confidence**")
        needs_pos = content.index("**Needs Human**")
        summary_pos = content.index("## Summary")
        assert conf_pos < summary_pos
        assert needs_pos < summary_pos
