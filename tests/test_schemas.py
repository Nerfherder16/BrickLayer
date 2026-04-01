"""Tests for masonry/src/schemas/payloads.py — Pydantic v2 payload models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


# ──────────────────────────────────────────────────────────────────────────
# Imports (will fail until implementation exists)
# ──────────────────────────────────────────────────────────────────────────

from masonry.src.schemas import (
    QuestionPayload,
    FindingPayload,
    RoutingDecision,
    DiagnosePayload,
    DiagnosisPayload,
    AgentRegistryEntry,
    GradeConfidence,
)


# ──────────────────────────────────────────────────────────────────────────
# QuestionPayload
# ──────────────────────────────────────────────────────────────────────────


class TestQuestionPayload:
    def test_valid_minimal(self):
        q = QuestionPayload(
            question_id="Q1.1",
            question_text="What is the revenue risk?",
            mode="simulate",
        )
        assert q.question_id == "Q1.1"
        assert q.priority == 3
        assert q.wave == 1
        assert q.context == {}
        assert q.constraints == []
        assert q.override_count == 0

    def test_valid_full(self):
        q = QuestionPayload(
            question_id="Q2.3",
            question_text="Stress-test the margin model.",
            mode="agent",
            agent_hint="quantitative-analyst",
            priority=1,
            context={"key": "value"},
            constraints=["max 5 scenarios"],
            wave=2,
            override_count=1,
        )
        assert q.agent_hint == "quantitative-analyst"
        assert q.priority == 1

    def test_all_valid_modes(self):
        valid_modes = [
            "simulate", "diagnose", "fix", "audit", "research",
            "benchmark", "validate", "evolve", "monitor", "predict",
            "frontier", "agent",
        ]
        for mode in valid_modes:
            hint = "quantitative-analyst" if mode == "agent" else None
            q = QuestionPayload(
                question_id="Q1.1",
                question_text="test",
                mode=mode,
                agent_hint=hint,
            )
            assert q.mode == mode

    def test_invalid_mode_rejected(self):
        with pytest.raises(ValidationError):
            QuestionPayload(
                question_id="Q1.1",
                question_text="test",
                mode="unknown_mode",
            )

    def test_priority_range_validation(self):
        # Valid range: 1-5
        for p in range(1, 6):
            q = QuestionPayload(question_id="Q1", question_text="t", mode="simulate", priority=p)
            assert q.priority == p

        # Out of range
        with pytest.raises(ValidationError):
            QuestionPayload(question_id="Q1", question_text="t", mode="simulate", priority=0)
        with pytest.raises(ValidationError):
            QuestionPayload(question_id="Q1", question_text="t", mode="simulate", priority=6)

    def test_mode_agent_requires_agent_hint(self):
        with pytest.raises(ValidationError):
            QuestionPayload(
                question_id="Q1.1",
                question_text="test",
                mode="agent",
                agent_hint=None,
            )

    def test_mode_agent_with_agent_hint_passes(self):
        q = QuestionPayload(
            question_id="Q1.1",
            question_text="test",
            mode="agent",
            agent_hint="quantitative-analyst",
        )
        assert q.agent_hint == "quantitative-analyst"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            QuestionPayload(
                question_id="Q1.1",
                question_text="test",
                mode="simulate",
                unknown_field="bad",
            )

    def test_model_dump_round_trip(self):
        q = QuestionPayload(
            question_id="Q1.1",
            question_text="Test question",
            mode="research",
            priority=2,
        )
        dumped = q.model_dump()
        restored = QuestionPayload.model_validate(dumped)
        assert restored.question_id == q.question_id
        assert restored.mode == q.mode
        assert restored.priority == q.priority


# ──────────────────────────────────────────────────────────────────────────
# FindingPayload
# ──────────────────────────────────────────────────────────────────────────


# All 30 valid verdict strings from the spec
VALID_VERDICTS = [
    "HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE", "DIAGNOSIS_COMPLETE",
    "FIXED", "FIX_FAILED", "COMPLIANT", "NON_COMPLIANT", "PARTIAL",
    "NOT_APPLICABLE", "CALIBRATED", "UNCALIBRATED", "NOT_MEASURABLE",
    "IMPROVEMENT", "REGRESSION", "IMMINENT", "PROBABLE", "POSSIBLE",
    "UNLIKELY", "OK", "DEGRADED", "DEGRADED_TRENDING", "ALERT",
    "UNKNOWN", "PROMISING", "BLOCKED", "WEAK", "SUBJECTIVE",
    "PENDING_EXTERNAL",
]


class TestFindingPayload:
    def test_valid_minimal(self):
        f = FindingPayload(
            question_id="Q1.1",
            verdict="HEALTHY",
            severity="Info",
            summary="System is healthy.",
            evidence="All metrics within bounds.",
            confidence=0.9,
        )
        assert f.verdict == "HEALTHY"
        assert f.mitigation is None
        assert f.recommend is None
        assert f.metadata == {}

    def test_all_valid_verdicts(self):
        for v in VALID_VERDICTS:
            f = FindingPayload(
                question_id="Q1.1",
                verdict=v,
                severity="Info",
                summary="test",
                evidence="test",
                confidence=0.5,
            )
            assert f.verdict == v

    def test_invalid_verdict_rejected(self):
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1",
                verdict="INVALID_VERDICT",
                severity="Info",
                summary="test",
                evidence="test",
                confidence=0.5,
            )

    def test_confidence_range_validation(self):
        # Valid range: 0.0 to 1.0
        FindingPayload(
            question_id="Q1.1", verdict="HEALTHY", severity="Info",
            summary="ok", evidence="ok", confidence=0.0,
        )
        FindingPayload(
            question_id="Q1.1", verdict="HEALTHY", severity="Info",
            summary="ok", evidence="ok", confidence=1.0,
        )
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity="Info",
                summary="ok", evidence="ok", confidence=1.5,
            )
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity="Info",
                summary="ok", evidence="ok", confidence=-0.1,
            )

    def test_summary_max_200_chars(self):
        # Exactly 200 chars OK
        FindingPayload(
            question_id="Q1.1", verdict="HEALTHY", severity="Info",
            summary="x" * 200, evidence="ok", confidence=0.5,
        )
        # 201 chars rejected
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity="Info",
                summary="x" * 201, evidence="ok", confidence=0.5,
            )

    def test_all_severity_levels(self):
        for sev in ["Critical", "High", "Medium", "Low", "Info"]:
            f = FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity=sev,
                summary="ok", evidence="ok", confidence=0.5,
            )
            assert f.severity == sev

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity="unknown",
                summary="ok", evidence="ok", confidence=0.5,
            )

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            FindingPayload(
                question_id="Q1.1", verdict="HEALTHY", severity="Info",
                summary="ok", evidence="ok", confidence=0.5,
                unknown_field="bad",
            )

    def test_model_dump_round_trip(self):
        f = FindingPayload(
            question_id="Q1.1",
            verdict="WARNING",
            severity="High",
            summary="Something risky.",
            evidence="Evidence here.",
            confidence=0.75,
            mitigation="Apply fix.",
        )
        dumped = f.model_dump()
        restored = FindingPayload.model_validate(dumped)
        assert restored.verdict == f.verdict
        assert restored.confidence == f.confidence


# ──────────────────────────────────────────────────────────────────────────
# RoutingDecision
# ──────────────────────────────────────────────────────────────────────────


class TestRoutingDecision:
    def test_valid_minimal(self):
        r = RoutingDecision(
            target_agent="quantitative-analyst",
            layer="deterministic",
            confidence=1.0,
            reason="Matched slash command",
        )
        assert r.target_agent == "quantitative-analyst"
        assert r.fallback_agents == []

    def test_all_valid_layers(self):
        for layer in ["deterministic", "semantic", "llm", "fallback"]:
            r = RoutingDecision(
                target_agent="agent",
                layer=layer,
                confidence=0.5,
                reason="test",
            )
            assert r.layer == layer

    def test_invalid_layer_rejected(self):
        with pytest.raises(ValidationError):
            RoutingDecision(
                target_agent="agent",
                layer="neural",
                confidence=0.5,
                reason="test",
            )

    def test_reason_max_100_chars(self):
        # Exactly 100 OK
        RoutingDecision(
            target_agent="agent", layer="llm",
            confidence=0.6, reason="x" * 100,
        )
        # 101 rejected
        with pytest.raises(ValidationError):
            RoutingDecision(
                target_agent="agent", layer="llm",
                confidence=0.6, reason="x" * 101,
            )

    def test_confidence_range(self):
        RoutingDecision(target_agent="a", layer="fallback", confidence=0.0, reason="ok")
        RoutingDecision(target_agent="a", layer="fallback", confidence=1.0, reason="ok")
        with pytest.raises(ValidationError):
            RoutingDecision(target_agent="a", layer="fallback", confidence=1.1, reason="ok")

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            RoutingDecision(
                target_agent="a", layer="llm", confidence=0.5,
                reason="ok", bad_field="no",
            )


# ──────────────────────────────────────────────────────────────────────────
# DiagnosePayload
# ──────────────────────────────────────────────────────────────────────────


class TestDiagnosePayload:
    def test_valid(self):
        d = DiagnosePayload(
            question_id="Q1.1",
            symptoms=["high latency", "memory spike"],
            affected_files=["bl/runners/agent.py"],
        )
        assert len(d.symptoms) == 2
        assert d.prior_attempts == []
        assert d.context == {}

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            DiagnosePayload(
                question_id="Q1.1",
                symptoms=["symptom"],
                affected_files=["file.py"],
                bad_field="no",
            )

    def test_model_dump_round_trip(self):
        d = DiagnosePayload(
            question_id="Q1.1",
            symptoms=["symptom"],
            affected_files=["file.py"],
            prior_attempts=["attempt 1"],
        )
        restored = DiagnosePayload.model_validate(d.model_dump())
        assert restored.prior_attempts == ["attempt 1"]


# ──────────────────────────────────────────────────────────────────────────
# DiagnosisPayload
# ──────────────────────────────────────────────────────────────────────────


class TestDiagnosisPayload:
    def test_valid(self):
        d = DiagnosisPayload(
            question_id="Q1.1",
            root_cause="Memory leak in agent runner.",
            fix_strategy="Reduce buffer size.",
            affected_scope=["bl/runners/agent.py"],
            confidence=0.85,
            verdict="DIAGNOSIS_COMPLETE",
        )
        assert d.verdict == "DIAGNOSIS_COMPLETE"

    def test_invalid_verdict_rejected(self):
        with pytest.raises(ValidationError):
            DiagnosisPayload(
                question_id="Q1.1",
                root_cause="x",
                fix_strategy="y",
                affected_scope=[],
                confidence=0.5,
                verdict="HEALTHY",
            )

    def test_both_valid_verdicts(self):
        for v in ["DIAGNOSIS_COMPLETE", "INCONCLUSIVE"]:
            d = DiagnosisPayload(
                question_id="Q1.1",
                root_cause="x",
                fix_strategy="y",
                affected_scope=[],
                confidence=0.5,
                verdict=v,
            )
            assert d.verdict == v

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            DiagnosisPayload(
                question_id="Q1.1",
                root_cause="x",
                fix_strategy="y",
                affected_scope=[],
                confidence=0.5,
                verdict="INCONCLUSIVE",
                bad_field="no",
            )


# ──────────────────────────────────────────────────────────────────────────
# AgentRegistryEntry
# ──────────────────────────────────────────────────────────────────────────


class TestAgentRegistryEntry:
    def test_valid_minimal(self):
        a = AgentRegistryEntry(
            name="quantitative-analyst",
            file="agents/quantitative-analyst.md",
        )
        assert a.model == "sonnet"
        assert a.tier == "draft"
        assert a.input_schema == "QuestionPayload"
        assert a.output_schema == "FindingPayload"
        assert a.optimized_prompt is None

    def test_valid_full(self):
        a = AgentRegistryEntry(
            name="quantitative-analyst",
            file="agents/quantitative-analyst.md",
            model="opus",
            description="Runs simulations.",
            modes=["simulate"],
            capabilities=["simulation", "boundary-finding"],
            tier="trusted",
            optimized_prompt="masonry/optimized_prompts/quantitative-analyst.json",
        )
        assert a.model == "opus"
        assert a.tier == "trusted"

    def test_invalid_model_rejected(self):
        with pytest.raises(ValidationError):
            AgentRegistryEntry(
                name="x", file="x.md", model="gpt4",
            )

    def test_invalid_tier_rejected(self):
        with pytest.raises(ValidationError):
            AgentRegistryEntry(
                name="x", file="x.md", tier="active",
            )

    def test_all_valid_tiers(self):
        for tier in ["draft", "candidate", "trusted", "retired"]:
            a = AgentRegistryEntry(name="x", file="x.md", tier=tier)
            assert a.tier == tier

    def test_all_valid_models(self):
        for model in ["opus", "sonnet", "haiku"]:
            a = AgentRegistryEntry(name="x", file="x.md", model=model)
            assert a.model == model

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            AgentRegistryEntry(name="x", file="x.md", bad_field="no")

    def test_model_dump_round_trip(self):
        a = AgentRegistryEntry(
            name="x",
            file="x.md",
            model="haiku",
            modes=["simulate", "research"],
        )
        restored = AgentRegistryEntry.model_validate(a.model_dump())
        assert restored.modes == ["simulate", "research"]


# ──────────────────────────────────────────────────────────────────────────
# GradeConfidence enum + FindingPayload auto-population
# ──────────────────────────────────────────────────────────────────────────


_FINDING_DEFAULTS = dict(
    question_id="Q1.1",
    verdict="HEALTHY",
    severity="Info",
    summary="ok",
    evidence="ok",
)


class TestGradeConfidence:
    def test_enum_values(self):
        assert GradeConfidence.HIGH == "HIGH"
        assert GradeConfidence.MODERATE == "MODERATE"
        assert GradeConfidence.LOW == "LOW"
        assert GradeConfidence.VERY_LOW == "VERY_LOW"

    def test_auto_populate_high(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.9)
        assert f.grade_confidence == GradeConfidence.HIGH

    def test_auto_populate_high_boundary(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.8)
        assert f.grade_confidence == GradeConfidence.HIGH

    def test_auto_populate_moderate(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.7)
        assert f.grade_confidence == GradeConfidence.MODERATE

    def test_auto_populate_moderate_boundary(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.6)
        assert f.grade_confidence == GradeConfidence.MODERATE

    def test_auto_populate_low(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.5)
        assert f.grade_confidence == GradeConfidence.LOW

    def test_auto_populate_low_boundary(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.4)
        assert f.grade_confidence == GradeConfidence.LOW

    def test_auto_populate_very_low(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.3)
        assert f.grade_confidence == GradeConfidence.VERY_LOW

    def test_auto_populate_very_low_zero(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.0)
        assert f.grade_confidence == GradeConfidence.VERY_LOW

    def test_explicit_grade_not_overridden(self):
        # Explicitly setting LOW should not be overridden by confidence=0.9
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.9, grade_confidence=GradeConfidence.LOW)
        assert f.grade_confidence == GradeConfidence.LOW

    def test_explicit_very_low_not_overridden_by_high_confidence(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=1.0, grade_confidence=GradeConfidence.VERY_LOW)
        assert f.grade_confidence == GradeConfidence.VERY_LOW

    def test_backward_compat_no_grade(self):
        # Old code that doesn't set grade_confidence still works
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.75)
        assert f.grade_confidence == GradeConfidence.MODERATE  # auto-populated

    def test_grade_confidence_none_when_confidence_none(self):
        # If somehow confidence is not set but grade is not set either,
        # grade_confidence stays None — but confidence has a ge=0.0 constraint
        # so we test with explicit None via model_construct (bypass validation)
        f = FindingPayload.model_construct(
            question_id="Q1.1",
            verdict="HEALTHY",
            severity="Info",
            summary="ok",
            evidence="ok",
            confidence=None,
            grade_confidence=None,
        )
        # model_construct skips validators — just confirm field exists
        assert f.grade_confidence is None

    def test_round_trip_preserves_grade(self):
        f = FindingPayload(**_FINDING_DEFAULTS, confidence=0.5, grade_confidence=GradeConfidence.HIGH)
        restored = FindingPayload.model_validate(f.model_dump())
        assert restored.grade_confidence == GradeConfidence.HIGH
