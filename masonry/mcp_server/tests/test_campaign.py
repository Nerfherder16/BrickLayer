"""Tests for masonry/mcp_server/tools/campaign.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from masonry.mcp_server.tools.campaign import (
    _tool_masonry_status,
    _tool_masonry_questions,
    _tool_masonry_run_question,
    _store_question_finding,
)


class TestMasonryStatus:
    def test_js_engine_result_returned_directly(self):
        js_payload = {"state": "research", "questions": {"total": 5, "answered": 3, "pending": 2}, "wave": 2, "findings": 4}
        with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=js_payload):
            result = _tool_masonry_status({"project_dir": "/tmp/fake"})
        assert result == js_payload

    def test_python_fallback_when_js_returns_none(self, tmp_path):
        with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=None):
            result = _tool_masonry_status({"project_dir": str(tmp_path)})
        assert "project_dir" in result
        assert result["has_campaign"] is False

    def test_python_fallback_reads_questions_md(self, tmp_path):
        (tmp_path / "questions.md").write_text(
            "## Wave 1\n### Q1\n**Status**: PENDING\n### Q2\n**Status**: DONE\n"
        )
        with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=None):
            result = _tool_masonry_status({"project_dir": str(tmp_path)})
        assert result["questions"]["total"] == 2
        assert result["questions"]["pending"] == 1
        assert result["questions"]["done"] == 1

    def test_missing_project_dir_uses_cwd(self):
        js_payload = {"state": "no_project"}
        with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=js_payload):
            result = _tool_masonry_status({})
        assert result == js_payload


class TestMasonryRunQuestion:
    def _make_question_fixture(self, tmp_path: Path, question_id: str = "Q1") -> Path:
        qfile = tmp_path / "questions.md"
        qfile.write_text(f"### {question_id}\n**Status**: PENDING\n**Mode**: correctness\n")
        return qfile

    def test_missing_question_id_returns_error(self):
        result = _tool_masonry_run_question({})
        assert "error" in result
        assert "question_id" in result["error"]

    def test_missing_questions_file_returns_error(self, tmp_path):
        result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q1"})
        assert "error" in result

    def test_unknown_question_id_returns_error(self, tmp_path):
        self._make_question_fixture(tmp_path)
        with patch("bl.questions.load_questions", return_value=[{"id": "Q1", "mode": "correctness"}]):
            result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q99"})
        assert "error" in result

    def test_success_returns_result(self, tmp_path):
        self._make_question_fixture(tmp_path)
        with patch("bl.questions.load_questions", return_value=[{"id": "Q1", "mode": "correctness"}]):
            with patch("bl.runners.run_question", return_value={"verdict": "HEALTHY", "summary": "ok"}):
                with patch("masonry.mcp_server.tools.campaign._store_question_finding"):
                    with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=None):
                        result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q1"})
        assert result["question_id"] == "Q1"
        assert result["result"]["verdict"] == "HEALTHY"

    def test_failure_verdict_triggers_healloop(self, tmp_path):
        self._make_question_fixture(tmp_path)
        heal_payload = {"ran": True, "cycles": 1, "final_verdict": "FIXED"}
        with patch("bl.questions.load_questions", return_value=[{"id": "Q1", "mode": "correctness"}]):
            with patch("bl.runners.run_question", return_value={"verdict": "FAILURE", "summary": "broken"}):
                with patch("masonry.mcp_server.tools.campaign._store_question_finding"):
                    with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=heal_payload) as mock_js:
                        result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q1"})
        assert result.get("heal_loop") == heal_payload
        mock_js.assert_called_once()
        call_args = mock_js.call_args[0]
        assert call_args[0] == "healloop.js"
        assert "--verdict" in call_args[1]
        assert "FAILURE" in call_args[1]

    def test_healthy_verdict_does_not_trigger_healloop(self, tmp_path):
        self._make_question_fixture(tmp_path)
        with patch("bl.questions.load_questions", return_value=[{"id": "Q1", "mode": "correctness"}]):
            with patch("bl.runners.run_question", return_value={"verdict": "HEALTHY", "summary": "ok"}):
                with patch("masonry.mcp_server.tools.campaign._store_question_finding"):
                    with patch("masonry.mcp_server.tools.campaign._call_js_engine") as mock_js:
                        result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q1"})
        mock_js.assert_not_called()
        assert "heal_loop" not in result

    def test_healloop_failure_does_not_break_response(self, tmp_path):
        self._make_question_fixture(tmp_path)
        with patch("bl.questions.load_questions", return_value=[{"id": "Q1", "mode": "correctness"}]):
            with patch("bl.runners.run_question", return_value={"verdict": "FAILURE", "summary": "broken"}):
                with patch("masonry.mcp_server.tools.campaign._store_question_finding"):
                    with patch("masonry.mcp_server.tools.campaign._call_js_engine", return_value=None):
                        result = _tool_masonry_run_question({"project_dir": str(tmp_path), "question_id": "Q1"})
        assert result["question_id"] == "Q1"
        assert "heal_loop" not in result


class TestStoreQuestionFinding:
    def test_no_verdict_is_noop(self, tmp_path):
        with patch("bl.recall_bridge.store_finding") as mock_store:
            _store_question_finding({"summary": "ok"}, {"id": "Q1"}, tmp_path)
        mock_store.assert_not_called()

    def test_no_summary_is_noop(self, tmp_path):
        with patch("bl.recall_bridge.store_finding") as mock_store:
            _store_question_finding({"verdict": "HEALTHY"}, {"id": "Q1"}, tmp_path)
        mock_store.assert_not_called()

    def test_exception_never_raises(self, tmp_path):
        with patch("bl.recall_bridge.store_finding", side_effect=Exception("recall down")):
            # Should not raise
            _store_question_finding({"verdict": "HEALTHY", "summary": "ok"}, {"id": "Q1"}, tmp_path)
