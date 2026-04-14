"""Typed payload schemas for Masonry routing and agent communication."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ──────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────

class GradeConfidence(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


# ──────────────────────────────────────────────────────────────────────────
# Agent registry
# ──────────────────────────────────────────────────────────────────────────

class AgentRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    file: str = ""
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    modes: list[str] = Field(default_factory=list)
    tier: Literal["draft", "candidate", "trusted", "retired"] = "draft"
    routing_keywords: list[str] = Field(default_factory=list)
    model: Literal["opus", "sonnet", "haiku"] = "sonnet"
    input_schema: str = "QuestionPayload"
    output_schema: str = "FindingPayload"
    optimized_prompt: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────
# Routing
# ──────────────────────────────────────────────────────────────────────────

class RoutingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_agent: str
    layer: Literal["deterministic", "semantic", "llm", "fallback"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(max_length=100)
    fallback_agents: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────
# Question / Finding payloads
# ──────────────────────────────────────────────────────────────────────────

_VALID_MODES = {
    "simulate", "diagnose", "fix", "audit", "research",
    "benchmark", "validate", "evolve", "monitor", "predict",
    "frontier", "agent",
}

_VALID_VERDICTS = {
    "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "DIAGNOSIS_COMPLETE",
    "FIXED", "FIX_FAILED", "COMPLIANT", "NON_COMPLIANT", "PARTIAL",
    "NOT_APPLICABLE", "CALIBRATED", "UNCALIBRATED", "NOT_MEASURABLE",
    "IMPROVEMENT", "REGRESSION", "IMMINENT", "PROBABLE", "POSSIBLE",
    "UNLIKELY", "OK", "DEGRADED", "DEGRADED_TRENDING", "ALERT",
    "UNKNOWN", "PROMISING", "BLOCKED", "WEAK", "SUBJECTIVE",
    "PENDING_EXTERNAL",
}


class QuestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    question_text: str
    mode: str
    agent_hint: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    context: dict = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    wave: int = 1
    override_count: int = 0

    @model_validator(mode="after")
    def validate_mode_and_agent_hint(self) -> "QuestionPayload":
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {sorted(_VALID_MODES)!r}, got {self.mode!r}"
            )
        if self.mode == "agent" and not self.agent_hint:
            raise ValueError("agent_hint is required when mode='agent'")
        return self


class FindingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    verdict: str
    severity: Literal["Critical", "High", "Medium", "Low", "Info"]
    summary: str = Field(max_length=200)
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    mitigation: Optional[str] = None
    recommend: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    grade_confidence: Optional[GradeConfidence] = None

    @model_validator(mode="after")
    def validate_verdict_and_grade(self) -> "FindingPayload":
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(
                f"verdict must be one of the 30 valid verdicts, got {self.verdict!r}"
            )
        if self.grade_confidence is None and self.confidence is not None:
            c = self.confidence
            if c >= 0.8:
                self.grade_confidence = GradeConfidence.HIGH
            elif c >= 0.6:
                self.grade_confidence = GradeConfidence.MODERATE
            elif c >= 0.4:
                self.grade_confidence = GradeConfidence.LOW
            else:
                self.grade_confidence = GradeConfidence.VERY_LOW
        return self


# ──────────────────────────────────────────────────────────────────────────
# Diagnose payloads
# ──────────────────────────────────────────────────────────────────────────

class DiagnosePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    symptoms: list[str]
    affected_files: list[str]
    prior_attempts: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)


class DiagnosisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    root_cause: str
    fix_strategy: str
    affected_scope: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    verdict: Literal["DIAGNOSIS_COMPLETE", "INCONCLUSIVE"]


# ──────────────────────────────────────────────────────────────────────────
# Pattern record
# ──────────────────────────────────────────────────────────────────────────

class PatternRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    INITIAL_CONFIDENCE: ClassVar[float] = 0.7
    PRUNE_THRESHOLD: ClassVar[float] = 0.2

    pattern_id: str
    content: str
    domain: str = "general"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    last_used: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
