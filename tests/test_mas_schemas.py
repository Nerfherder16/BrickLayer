"""
Tests for masonry/src/schemas/mas_schemas.py

Run with: python -m pytest tests/test_mas_schemas.py --capture=no -q
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from masonry.src.schemas.mas_schemas import (
    AgentScoreEntry,
    ContributionsFile,
    ErrorEntry,
    KilnIdentity,
    OpenIssue,
    PulseEntry,
    RecallLogEntry,
    SessionRecord,
    TimingEntry,
    WaveLogEntry,
)


class TestPulseEntry:
    def test_valid_construction(self):
        e = PulseEntry(timestamp="2026-03-23T00:00:00Z", session_id="s1", tool="Edit", cwd="/tmp")
        assert e.session_id == "s1"
        assert e.tool == "Edit"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            PulseEntry(timestamp="2026-03-23T00:00:00Z", session_id="s1", tool="Edit")  # missing cwd

    def test_extra_fields_allowed(self):
        e = PulseEntry(timestamp="T", session_id="s", tool="t", cwd="/", extra_field="hello")
        assert e.extra_field == "hello"


class TestSessionRecord:
    def test_valid_minimal(self):
        s = SessionRecord(session_id="s1", started_at="2026-03-23T00:00:00Z", cwd="/tmp")
        assert s.ended_at is None
        assert s.duration_ms is None
        assert s.branch is None

    def test_valid_full(self):
        s = SessionRecord(
            session_id="s2",
            started_at="2026-03-23T00:00:00Z",
            ended_at="2026-03-23T01:00:00Z",
            duration_ms=3600000,
            cwd="/tmp",
            branch="main",
        )
        assert s.duration_ms == 3600000
        assert s.branch == "main"

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            SessionRecord(session_id="s")  # missing started_at and cwd

    def test_extra_fields_allowed(self):
        s = SessionRecord(session_id="s", started_at="T", cwd="/", new_field=42)
        assert s.new_field == 42


class TestTimingEntry:
    def test_valid_construction(self):
        t = TimingEntry(qid="D1", agent="quant", verdict="WARNING", timestamp="T")
        assert t.wave is None
        assert t.started_at is None
        assert t.duration_ms is None

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            TimingEntry(qid="D1", agent="quant")  # missing verdict and timestamp


class TestErrorEntry:
    def test_valid_construction(self):
        e = ErrorEntry(
            timestamp="T",
            tool="Edit",
            error="ENOENT: file not found",
            retries=1,
            fingerprint="Edit:ENOENT",
        )
        assert e.retries == 1

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            ErrorEntry(timestamp="T", tool="Edit")  # missing error, retries, fingerprint


class TestAgentScoreEntry:
    def test_defaults(self):
        a = AgentScoreEntry()
        assert a.count == 0
        assert a.verdicts == {}
        assert a.last_seen is None

    def test_with_values(self):
        a = AgentScoreEntry(count=5, verdicts={"WARNING": 3, "HEALTHY": 2}, last_seen="T")
        assert a.count == 5
        assert a.verdicts["WARNING"] == 3


class TestKilnIdentity:
    def test_valid_construction(self):
        k = KilnIdentity(display_name="ADBP Research", created_at="2026-03-23T00:00:00Z")
        assert k.pinned is False
        assert k.phase == "research"
        assert k.status == "active"
        assert k.description == ""

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            KilnIdentity(display_name="Test")  # missing created_at


class TestOpenIssue:
    def test_valid_all_statuses(self):
        for status in ("open", "mitigated", "accepted", "resolved"):
            issue = OpenIssue(
                finding_id="D1",
                verdict="WARNING",
                severity="High",
                summary="Test summary",
                wave=3,
                opened_at="T",
                status=status,
            )
            assert issue.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            OpenIssue(
                finding_id="D1",
                verdict="WARNING",
                severity="High",
                summary="Test",
                wave=3,
                opened_at="T",
                status="invalid_status",
            )

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            OpenIssue(
                finding_id="D1",
                verdict="WARNING",
                severity="SuperCritical",  # not in Literal
                summary="Test",
                wave=3,
                opened_at="T",
            )

    def test_summary_max_length(self):
        with pytest.raises(ValidationError):
            OpenIssue(
                finding_id="D1",
                verdict="WARNING",
                severity="High",
                summary="x" * 201,  # exceeds max_length=200
                wave=3,
                opened_at="T",
            )

    def test_all_severity_values(self):
        for sev in ("Critical", "High", "Medium", "Low", "Info"):
            issue = OpenIssue(
                finding_id="D1", verdict="W", severity=sev,
                summary="s", wave=1, opened_at="T"
            )
            assert issue.severity == sev


class TestWaveLogEntry:
    def test_valid_recommendations(self):
        for rec in ("CONTINUE", "PIVOT", "STOP"):
            w = WaveLogEntry(
                wave=1,
                questions_total=10,
                recommendation=rec,
                synthesis_path="findings/synthesis.md",
                timestamp="T",
            )
            assert w.recommendation == rec

    def test_invalid_recommendation(self):
        with pytest.raises(ValidationError):
            WaveLogEntry(
                wave=1,
                questions_total=10,
                recommendation="MAYBE",  # not in Literal
                synthesis_path="s",
                timestamp="T",
            )


class TestContributionsFile:
    def test_defaults(self):
        c = ContributionsFile()
        assert c.recall_memories == 0
        assert c.skills_forged == 0
        assert c.fixes_applied == 0
        assert c.agents_improved == 0
        assert c.updated_at is None


class TestRecallLogEntry:
    def test_valid_construction(self):
        r = RecallLogEntry(qid="D1", query="discount credit", memory_id=None, domain="adbp-autoresearch", timestamp="T")
        assert r.memory_id is None

    def test_with_memory_id(self):
        r = RecallLogEntry(qid="D2", query="q", memory_id="mem-abc", domain="d", timestamp="T")
        assert r.memory_id == "mem-abc"
