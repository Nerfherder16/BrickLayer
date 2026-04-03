"""Tests for masonry/src/dspy_pipeline/signatures.py — DSPy Signature classes."""

from __future__ import annotations



# ──────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────

from masonry.src.dspy_pipeline.signatures import (
    DiagnoseAgentSig,
    QuestionDesignerSig,
    ResearchAgentSig,
    SynthesizerSig,
)


# ──────────────────────────────────────────────────────────────────────────
# ResearchAgentSig
# ──────────────────────────────────────────────────────────────────────────


class TestResearchAgentSig:
    def test_has_expected_input_fields(self):
        inputs = list(ResearchAgentSig.input_fields.keys())
        assert "question_text" in inputs
        assert "project_context" in inputs
        assert "constraints" in inputs

    def test_has_expected_output_fields(self):
        outputs = list(ResearchAgentSig.output_fields.keys())
        assert "verdict" in outputs
        assert "severity" in outputs
        assert "evidence" in outputs
        assert "mitigation" in outputs
        assert "confidence" in outputs

    def test_has_docstring(self):
        doc = ResearchAgentSig.__doc__
        assert doc is not None
        assert len(doc) > 10


# ──────────────────────────────────────────────────────────────────────────
# DiagnoseAgentSig
# ──────────────────────────────────────────────────────────────────────────


class TestDiagnoseAgentSig:
    def test_has_expected_input_fields(self):
        inputs = list(DiagnoseAgentSig.input_fields.keys())
        assert "symptoms" in inputs
        assert "affected_files" in inputs
        assert "prior_attempts" in inputs

    def test_has_expected_output_fields(self):
        outputs = list(DiagnoseAgentSig.output_fields.keys())
        assert "root_cause" in outputs
        assert "fix_strategy" in outputs
        assert "affected_scope" in outputs
        assert "confidence" in outputs


# ──────────────────────────────────────────────────────────────────────────
# SynthesizerSig
# ──────────────────────────────────────────────────────────────────────────


class TestSynthesizerSig:
    def test_has_expected_input_fields(self):
        inputs = list(SynthesizerSig.input_fields.keys())
        assert "findings_summary" in inputs
        assert "question_list" in inputs

    def test_has_expected_output_fields(self):
        outputs = list(SynthesizerSig.output_fields.keys())
        assert "synthesis_text" in outputs
        assert "key_themes" in outputs
        assert "recommendations" in outputs


# ──────────────────────────────────────────────────────────────────────────
# QuestionDesignerSig
# ──────────────────────────────────────────────────────────────────────────


class TestQuestionDesignerSig:
    def test_has_expected_input_fields(self):
        inputs = list(QuestionDesignerSig.input_fields.keys())
        assert "project_brief" in inputs
        assert "docs_summary" in inputs
        assert "prior_findings" in inputs

    def test_has_expected_output_fields(self):
        outputs = list(QuestionDesignerSig.output_fields.keys())
        assert "questions_yaml" in outputs
        assert "coverage_rationale" in outputs

    def test_has_docstring(self):
        doc = QuestionDesignerSig.__doc__
        assert doc is not None


# ──────────────────────────────────────────────────────────────────────────
# All signatures are proper DSPy Signature subclasses
# ──────────────────────────────────────────────────────────────────────────


class TestSignatureTypes:
    def test_all_are_dspy_signatures(self):
        import dspy

        for sig_cls in [
            ResearchAgentSig,
            DiagnoseAgentSig,
            SynthesizerSig,
            QuestionDesignerSig,
        ]:
            assert issubclass(sig_cls, dspy.Signature), (
                f"{sig_cls.__name__} should be a dspy.Signature subclass"
            )
