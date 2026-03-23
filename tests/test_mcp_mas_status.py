"""
Tests for .mas/ telemetry integration in _tool_masonry_status.

Run with: python -m pytest tests/test_mcp_mas_status.py --capture=no -q
"""

import json
import sys
from pathlib import Path

import pytest

# Bootstrap repo root into sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masonry.mcp_server.server import _tool_masonry_status


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def write_jsonl(path: Path, records: list) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


class TestMasStatusTelemetry:
    def test_mas_session_included(self, tmp_path: Path):
        mas_dir = tmp_path / ".mas"
        mas_dir.mkdir()
        write_json(mas_dir / "session.json", {"session_id": "s1", "started_at": "2026-03-23T00:00:00Z"})
        write_jsonl(mas_dir / "pulse.jsonl", [
            {"timestamp": "2026-03-23T00:00:01Z", "session_id": "s1", "tool": "Read", "cwd": str(tmp_path)},
            {"timestamp": "2026-03-23T00:01:00Z", "session_id": "s1", "tool": "Write", "cwd": str(tmp_path)},
        ])
        write_json(mas_dir / "agent_scores.json", {"quant": {"count": 5, "verdicts": {}, "last_seen": None}})
        # 3 error lines
        (mas_dir / "errors.jsonl").write_text(
            '{"tool":"Edit","error":"e1","retries":1}\n'
            '{"tool":"Edit","error":"e2","retries":2}\n'
            '{"tool":"Bash","error":"e3","retries":1}\n'
        )

        result = _tool_masonry_status({"project_dir": str(tmp_path)})

        assert "mas" in result, "mas key should be present"
        assert result["mas"]["session"]["session_id"] == "s1"
        assert result["mas"]["last_pulse"]["tool"] == "Write"  # last line
        assert result["mas"]["agent_scores"]["quant"]["count"] == 5
        assert result["mas"]["error_count"] == 3

    def test_mas_open_issues_included(self, tmp_path: Path):
        mas_dir = tmp_path / ".mas"
        mas_dir.mkdir()
        write_json(mas_dir / "open_issues.json", {
            "issues": [{"finding_id": "D1", "verdict": "CRITICAL"}],
            "last_wave": 3,
            "updated_at": "2026-03-23T00:00:00Z",
        })

        result = _tool_masonry_status({"project_dir": str(tmp_path)})

        assert "mas" in result
        assert result["mas"]["open_issues"]["last_wave"] == 3

    def test_empty_mas_dir_omits_mas_key(self, tmp_path: Path):
        mas_dir = tmp_path / ".mas"
        mas_dir.mkdir()
        # No files written

        result = _tool_masonry_status({"project_dir": str(tmp_path)})

        assert "mas" not in result, "mas key should be absent when .mas/ has no readable data"

    def test_no_mas_dir_omits_mas_key(self, tmp_path: Path):
        # No .mas/ directory at all
        result = _tool_masonry_status({"project_dir": str(tmp_path)})
        assert "mas" not in result

    def test_last_pulse_is_last_line(self, tmp_path: Path):
        mas_dir = tmp_path / ".mas"
        mas_dir.mkdir()
        write_jsonl(mas_dir / "pulse.jsonl", [
            {"timestamp": "T1", "session_id": "a", "tool": "Read", "cwd": str(tmp_path)},
            {"timestamp": "T2", "session_id": "b", "tool": "Write", "cwd": str(tmp_path)},
            {"timestamp": "T3", "session_id": "c", "tool": "Bash", "cwd": str(tmp_path)},
        ])

        result = _tool_masonry_status({"project_dir": str(tmp_path)})

        assert result["mas"]["last_pulse"]["session_id"] == "c"
        assert result["mas"]["last_pulse"]["timestamp"] == "T3"

    def test_malformed_files_dont_crash(self, tmp_path: Path):
        mas_dir = tmp_path / ".mas"
        mas_dir.mkdir()
        (mas_dir / "session.json").write_text("not valid json")
        (mas_dir / "pulse.jsonl").write_text("also not json\n")
        (mas_dir / "agent_scores.json").write_text("{broken}")

        # Should not raise
        result = _tool_masonry_status({"project_dir": str(tmp_path)})
        # mas key may or may not be present, but it must not crash
        assert isinstance(result, dict)
