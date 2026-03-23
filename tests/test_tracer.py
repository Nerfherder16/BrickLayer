"""
tests/test_tracer.py — C-23: introspection tracer.

Covers:
  - traced() wraps a callable and returns the result unchanged
  - trace record written to traces.jsonl
  - trace fields: timestamp, thought, tool_call, verdict, latency_ms, confidence, error_type
  - exceptions propagate and trace is still written
  - load_traces() reads traces.jsonl
  - no crash when traces.jsonl absent
"""

import json
import time

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_project(tmp_path, monkeypatch):
    """Patch bl.config.cfg to point project_root at tmp_path."""
    import bl.config as config_mod

    monkeypatch.setattr(config_mod.cfg, "project_root", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# traced() decorator
# ---------------------------------------------------------------------------


class TestTraced:
    def test_returns_result_unchanged(self, tmp_project):
        from bl.tracer import traced

        expected = {"verdict": "HEALTHY", "summary": "all good", "data": {}}

        @traced
        def runner(q):
            return expected

        result = runner({"id": "Q1", "mode": "test", "title": "Is it healthy?"})
        assert result == expected

    def test_writes_to_traces_jsonl(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "HEALTHY", "summary": "ok", "data": {}}

        runner({"id": "Q1", "mode": "subprocess", "title": "Does it pass?"})
        traces_path = tmp_project / "traces.jsonl"
        assert traces_path.exists()
        trace = json.loads(traces_path.read_text().strip())
        assert trace["verdict"] == "HEALTHY"

    def test_trace_has_required_fields(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "FAILURE", "summary": "broke", "confidence": "high"}

        runner({"id": "Q2", "mode": "http", "title": "Is endpoint up?"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())

        required = {
            "timestamp",
            "thought",
            "tool_call",
            "verdict",
            "result_summary",
            "latency_ms",
            "confidence",
            "question_id",
        }
        for field in required:
            assert field in trace, f"Missing field: {field}"

    def test_latency_ms_is_positive(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            time.sleep(0.01)
            return {"verdict": "HEALTHY", "summary": "ok"}

        runner({"id": "Q1", "mode": "agent", "title": "Quick test"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())
        assert trace["latency_ms"] > 0

    def test_thought_comes_from_title(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "HEALTHY", "summary": ""}

        runner({"id": "Q3", "mode": "quality", "title": "Check code patterns"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())
        assert trace["thought"] == "Check code patterns"

    def test_confidence_propagated(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "FAILURE", "summary": "bad", "confidence": "low"}

        runner({"id": "Q1", "mode": "agent", "title": "x"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())
        assert trace["confidence"] == "low"

    def test_default_confidence_is_uncertain(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "INCONCLUSIVE", "summary": ""}

        runner({"id": "Q1", "mode": "agent", "title": "x"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())
        assert trace["confidence"] == "uncertain"

    def test_error_type_captured(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {
                "verdict": "FAILURE",
                "summary": "timed out",
                "failure_type": "timeout",
            }

        runner({"id": "Q1", "mode": "http", "title": "x"})
        trace = json.loads((tmp_project / "traces.jsonl").read_text().strip())
        assert trace["error_type"] == "timeout"

    def test_multiple_calls_append_to_jsonl(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            return {"verdict": "HEALTHY", "summary": "ok"}

        runner({"id": "Q1", "mode": "agent", "title": "first"})
        runner({"id": "Q2", "mode": "agent", "title": "second"})

        lines = [
            line
            for line in (tmp_project / "traces.jsonl").read_text().splitlines()
            if line.strip()
        ]
        assert len(lines) == 2

    def test_exception_still_writes_trace(self, tmp_project):
        from bl.tracer import traced

        @traced
        def runner(q):
            raise RuntimeError("exploded")

        with pytest.raises(RuntimeError):
            runner({"id": "Q1", "mode": "agent", "title": "x"})

        assert (tmp_project / "traces.jsonl").exists()


# ---------------------------------------------------------------------------
# load_traces()
# ---------------------------------------------------------------------------


class TestLoadTraces:
    def test_returns_empty_when_no_file(self, tmp_project):
        from bl.tracer import load_traces

        assert load_traces(tmp_project) == []

    def test_returns_traces_in_order(self, tmp_project):
        from bl.tracer import load_traces

        records = [
            {"question_id": "Q1", "verdict": "HEALTHY"},
            {"question_id": "Q2", "verdict": "FAILURE"},
        ]
        path = tmp_project / "traces.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n")

        traces = load_traces(tmp_project)
        assert len(traces) == 2
        assert traces[0]["question_id"] == "Q1"
        assert traces[1]["question_id"] == "Q2"

    def test_skips_malformed_lines(self, tmp_project):
        from bl.tracer import load_traces

        path = tmp_project / "traces.jsonl"
        path.write_text('{"ok": true}\nnot-json\n{"also": "fine"}\n')
        traces = load_traces(tmp_project)
        assert len(traces) == 2
