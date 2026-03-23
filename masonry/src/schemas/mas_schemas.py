"""
masonry/src/schemas/mas_schemas.py

Pydantic v2 models defining the schema for every `.mas/` file.
These serve as documentation and validation contracts for consumers
(MCP tools, Kiln, agents).

All models use ConfigDict(extra="allow") for forward compatibility —
new fields added by future writers won't break existing readers.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PulseEntry(BaseModel):
    """One entry in .mas/pulse.jsonl — written by masonry-pulse.js."""

    model_config = ConfigDict(extra="allow")

    timestamp: str
    session_id: str
    tool: str
    cwd: str


class SessionRecord(BaseModel):
    """Contents of .mas/session.json and each line of .mas/history.jsonl."""

    model_config = ConfigDict(extra="allow")

    session_id: str
    started_at: str
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    cwd: str
    branch: Optional[str] = None


class TimingEntry(BaseModel):
    """One entry in .mas/timing.jsonl — written by masonry-observe.js."""

    model_config = ConfigDict(extra="allow")

    qid: str
    wave: Optional[int] = None
    agent: str
    started_at: Optional[str] = None
    duration_ms: Optional[int] = None
    verdict: str
    timestamp: str


class ErrorEntry(BaseModel):
    """One entry in .mas/errors.jsonl — written by masonry-tool-failure.js."""

    model_config = ConfigDict(extra="allow")

    timestamp: str
    tool: str
    error: str
    retries: int
    fingerprint: str


class AgentScoreEntry(BaseModel):
    """One value in .mas/agent_scores.json — keyed by agent name."""

    model_config = ConfigDict(extra="allow")

    count: int = 0
    verdicts: dict[str, int] = Field(default_factory=dict)
    last_seen: Optional[str] = None


class KilnIdentity(BaseModel):
    """Contents of .mas/kiln.json — written once by masonry-session-start.js."""

    model_config = ConfigDict(extra="allow")

    display_name: str
    description: str = ""
    color: Optional[str] = None
    icon: Optional[str] = None
    pinned: bool = False
    phase: str = "research"
    status: str = "active"
    created_at: str


class OpenIssue(BaseModel):
    """One issue in .mas/open_issues.json — written by synthesizer-bl2 (future)."""

    model_config = ConfigDict(extra="allow")

    finding_id: str
    verdict: str
    severity: Literal["Critical", "High", "Medium", "Low", "Info"]
    summary: str = Field(max_length=200)
    wave: int
    mitigation: Optional[str] = None
    status: Literal["open", "mitigated", "accepted", "resolved"] = "open"
    opened_at: str
    updated_at: Optional[str] = None


class OpenIssuesFile(BaseModel):
    """Contents of .mas/open_issues.json."""

    model_config = ConfigDict(extra="allow")

    issues: list[OpenIssue] = Field(default_factory=list)
    last_wave: int = 0
    updated_at: str


class WaveLogEntry(BaseModel):
    """One entry in .mas/wave_log.jsonl — written by synthesizer-bl2 (future)."""

    model_config = ConfigDict(extra="allow")

    wave: int
    questions_total: int
    verdict_summary: dict[str, int] = Field(default_factory=dict)
    recommendation: Literal["CONTINUE", "PIVOT", "STOP"]
    synthesis_path: str
    timestamp: str


class ContributionsFile(BaseModel):
    """Contents of .mas/contributions.json — written by synthesizer-bl2 (future)."""

    model_config = ConfigDict(extra="allow")

    recall_memories: int = 0
    skills_forged: int = 0
    fixes_applied: int = 0
    agents_improved: int = 0
    updated_at: Optional[str] = None


class RecallLogEntry(BaseModel):
    """One entry in .mas/recall_log.jsonl — written by masonry-observe.js."""

    model_config = ConfigDict(extra="allow")

    qid: str
    query: str
    memory_id: Optional[str] = None
    domain: str
    timestamp: str
