"""DSPy Signatures for Masonry agent types.

Each Signature defines the structured I/O contract for a class of agent.
DSPy uses these to generate optimized prompts via MIPROv2.
"""

from __future__ import annotations

import dspy


class ResearchAgentSig(dspy.Signature):
    """Given a research question and project context, produce a structured finding."""

    question_text: str = dspy.InputField(
        desc="The full research question to investigate"
    )
    project_context: str = dspy.InputField(
        desc="Project brief summary, prior findings, and key constraints"
    )
    constraints: str = dspy.InputField(
        default="",
        desc="Special instructions or scope limits for this question",
    )

    verdict: str = dspy.OutputField(
        desc="One of: HEALTHY, WARNING, FAILURE, INCONCLUSIVE, etc."
    )
    severity: str = dspy.OutputField(
        desc="One of: Critical, High, Medium, Low, Info"
    )
    evidence: str = dspy.OutputField(
        desc="Detailed evidence supporting the verdict"
    )
    mitigation: str = dspy.OutputField(
        default="",
        desc="Recommended fix or mitigation if applicable",
    )
    confidence: str = dspy.OutputField(
        desc="Calibrated confidence 0.0-1.0 as a decimal string"
    )


class DiagnoseAgentSig(dspy.Signature):
    """Diagnose the root cause of observed symptoms."""

    symptoms: str = dspy.InputField(
        desc="List of observed symptoms, one per line"
    )
    affected_files: str = dspy.InputField(
        desc="Files or components involved in the failure"
    )
    prior_attempts: str = dspy.InputField(
        default="",
        desc="Previously attempted fixes that did not resolve the issue",
    )

    root_cause: str = dspy.OutputField(
        desc="The identified root cause of the failure"
    )
    fix_strategy: str = dspy.OutputField(
        desc="Recommended strategy to fix the root cause"
    )
    affected_scope: str = dspy.OutputField(
        desc="Files, modules, or systems that need to be modified"
    )
    confidence: str = dspy.OutputField(
        desc="Confidence in this diagnosis 0.0-1.0"
    )


class SynthesizerSig(dspy.Signature):
    """Synthesize multiple findings into a coherent analysis."""

    findings_summary: str = dspy.InputField(
        desc="Summaries of all findings from the current campaign wave"
    )
    question_list: str = dspy.InputField(
        desc="The original question bank that was investigated"
    )

    synthesis_text: str = dspy.OutputField(
        desc="Coherent synthesis narrative connecting all findings"
    )
    key_themes: str = dspy.OutputField(
        desc="Comma-separated list of key themes identified across findings"
    )
    recommendations: str = dspy.OutputField(
        desc="Prioritized recommendations based on the findings"
    )


class QuestionDesignerSig(dspy.Signature):
    """Generate research questions from project context."""

    project_brief: str = dspy.InputField(
        desc="The full project brief describing the system and goals"
    )
    docs_summary: str = dspy.InputField(
        desc="Summary of supporting documentation in docs/ directory"
    )
    prior_findings: str = dspy.InputField(
        default="",
        desc="Summary of findings from prior campaign waves if any",
    )

    questions_yaml: str = dspy.OutputField(
        desc="YAML-formatted question bank following the BL2.0 question schema"
    )
    coverage_rationale: str = dspy.OutputField(
        desc="Explanation of why these questions cover the most important risk areas"
    )
