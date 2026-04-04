"""Pydantic v2 payload schemas for Masonry agent-to-agent data contracts.

All models use ConfigDict(extra="forbid") to reject unknown fields,
ensuring strict payload validation at agent handoff boundaries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Valid verdict strings (all ~30 BL2.0 verdict strings)
# ---------------------------------------------------------------------------

VALID_VERDICTS = frozenset({
    "HEALTHY",
    "WARNING",
    "FAILURE",
    "INCONCLUSIVE",
    "DIAGNOSIS_COMPLETE",
    "FIXED",
    "FIX_FAILED",
    "COMPLIANT",
    "NON_COMPLIANT",
    "PARTIAL",
    "NOT_APPLICABLE",
    "CALIBRATED",
    "UNCALIBRATED",
    "NOT_MEASURABLE",
    "IMPROVEMENT",
    "REGRESSION",
    "IMMINENT",
    "PROBABLE",
    "POSSIBLE",
    "UNLIKELY",
    "OK",
    "DEGRADED",
    "DEGRADED_TRENDING",
    "ALERT",
    "UNKNOWN",
    "PROMISING",
    "BLOCKED",
    "WEAK",
    "SUBJECTIVE",
    "PENDING_EXTERNAL",
})


def _validate_verdict(v: str) -> str:
    if v not in VALID_VERDICTS:
        raise ValueError(
            f"Invalid verdict '{v}'. Must be one of: {sorted(VALID_VERDICTS)}"
        )
    return v


# ---------------------------------------------------------------------------
# QuestionPayload — input to every specialist agent
# ---------------------------------------------------------------------------

class QuestionPayload(BaseModel):
    """Structured input payload delivered to every specialist agent."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    question_text: str
    mode: Literal[
        "simulate",
        "diagnose",
        "fix",
        "audit",
        "research",
        "benchmark",
        "validate",
        "evolve",
        "monitor",
        "predict",
        "frontier",
        "agent",
    ]
    agent_hint: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    wave: int = 1
    override_count: int = 0

    @model_validator(mode="after")
    def check_agent_hint_when_mode_agent(self) -> QuestionPayload:
        if self.mode == "agent" and self.agent_hint is None:
            raise ValueError("agent_hint is required when mode='agent'")
        return self


# ---------------------------------------------------------------------------
# FindingPayload — output from every specialist agent
# ---------------------------------------------------------------------------

class FindingPayload(BaseModel):
    """Structured output payload returned by every specialist agent."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    verdict: str
    severity: Literal["Critical", "High", "Medium", "Low", "Info"]
    summary: str = Field(max_length=200)
    evidence: str
    mitigation: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    recommend: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_verdict(self) -> FindingPayload:
        _validate_verdict(self.verdict)
        return self


# ---------------------------------------------------------------------------
# RoutingDecision — output of the four-layer routing engine
# ---------------------------------------------------------------------------

class RoutingDecision(BaseModel):
    """Routing decision returned by any layer of the four-layer router."""

    model_config = ConfigDict(extra="forbid")

    target_agent: str
    layer: Literal["deterministic", "semantic", "llm", "fallback"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(max_length=100)
    fallback_agents: list[str] = Field(default_factory=list)
    fallback_reason: Optional[Literal[
        "ambiguous", "ollama_timeout", "llm_timeout", "registry_empty", "multi_failure"
    ]] = None


# ---------------------------------------------------------------------------
# DiagnosePayload — input to the diagnose-analyst agent
# ---------------------------------------------------------------------------

class DiagnosePayload(BaseModel):
    """Input payload for the diagnose-analyst agent."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    symptoms: list[str]
    affected_files: list[str]
    prior_attempts: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# DiagnosisPayload — output from the diagnose-analyst agent
# ---------------------------------------------------------------------------

class DiagnosisPayload(BaseModel):
    """Output payload from the diagnose-analyst agent."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    root_cause: str
    fix_strategy: str
    affected_scope: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    verdict: Literal["DIAGNOSIS_COMPLETE", "INCONCLUSIVE"]


# ---------------------------------------------------------------------------
# AgentRegistryEntry — one entry in agent_registry.yml
# ---------------------------------------------------------------------------

class AgentRegistryEntry(BaseModel):
    """Registry entry for a Masonry agent, sourced from agent_registry.yml.

    Uses ``extra="ignore"`` (not ``extra="forbid"``) so that onboarding-added
    fields (``dspy_status``, ``drift_status``, ``last_score``,
    ``runs_since_optimization``, ``registrySource``) do not fail validation
    when the registry is loaded by registry_loader or run_drift_check (F11.1).
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    file: str
    model: Literal["opus", "sonnet", "haiku"] = "sonnet"
    description: str = ""
    modes: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    input_schema: str = "QuestionPayload"
    output_schema: str = "FindingPayload"
    tier: Literal["draft", "candidate", "trusted", "retired"] = "draft"
    # Optimization status is tracked via `dspy_status`/`last_optimized` in agent_registry.yml
    # and by the presence of masonry/optimized_prompts/{agent}.json. Do not add an inline
    # optimized_prompt field here — it is never written by any optimization script.
    routing_keywords: list[str] = Field(default_factory=list)
