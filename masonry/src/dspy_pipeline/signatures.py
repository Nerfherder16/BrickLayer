"""DSPy signatures for BrickLayer agent optimization."""
from __future__ import annotations

import dspy


class ResearchAgentSig(dspy.Signature):
    """Signature for research and analysis agents."""
    question_text: str = dspy.InputField(desc="The research question to investigate")
    project_context: str = dspy.InputField(desc="Project context and background", default="")
    constraints: str = dspy.InputField(desc="Any constraints or scope limitations", default="")

    verdict: str = dspy.OutputField(desc="HEALTHY | WARNING | FAILURE | INCONCLUSIVE | PROMISING")
    severity: str = dspy.OutputField(desc="Critical | High | Medium | Low")
    evidence: str = dspy.OutputField(desc="Detailed evidence supporting the verdict")
    mitigation: str = dspy.OutputField(desc="Recommended mitigations if applicable", default="")
    confidence: str = dspy.OutputField(desc="Confidence score 0.0-1.0")


class KarenSig(dspy.Signature):
    """Signature for documentation and project management agents (karen)."""
    request: str = dspy.InputField(desc="Documentation or organization request")
    project_context: str = dspy.InputField(desc="Project context", default="")

    output: str = dspy.OutputField(desc="Documentation output or organized content")
    files_updated: str = dspy.OutputField(desc="Comma-separated list of files updated")
    summary: str = dspy.OutputField(desc="Brief summary of changes made")


class DiagnoseAgentSig(dspy.Signature):
    """Signature for diagnosis agents — root cause analysis and fix strategy."""
    symptoms: str = dspy.InputField(desc="Observed symptoms or error descriptions")
    affected_files: str = dspy.InputField(desc="Files or modules involved in the issue", default="")
    prior_attempts: str = dspy.InputField(desc="Previous fix attempts that failed", default="")

    root_cause: str = dspy.OutputField(desc="Identified root cause of the issue")
    fix_strategy: str = dspy.OutputField(desc="Recommended fix strategy")
    affected_scope: str = dspy.OutputField(desc="Scope of affected code or systems")
    confidence: str = dspy.OutputField(desc="Confidence score 0.0-1.0")


class SynthesizerSig(dspy.Signature):
    """Signature for synthesis agents — integrating findings into a coherent narrative."""
    findings_summary: str = dspy.InputField(desc="Summary of all findings from the campaign")
    question_list: str = dspy.InputField(desc="List of questions investigated", default="")

    synthesis_text: str = dspy.OutputField(desc="Integrated synthesis narrative")
    key_themes: str = dspy.OutputField(desc="Key themes and patterns identified")
    recommendations: str = dspy.OutputField(desc="Prioritized recommendations")


class QuestionDesignerSig(dspy.Signature):
    """Signature for question designer agents — generating research questions from project briefs."""
    project_brief: str = dspy.InputField(desc="Project brief describing the system under investigation")
    docs_summary: str = dspy.InputField(desc="Summary of available documentation", default="")
    prior_findings: str = dspy.InputField(desc="Findings from previous waves", default="")

    questions_yaml: str = dspy.OutputField(desc="Generated questions in YAML format")
    coverage_rationale: str = dspy.OutputField(desc="Rationale for question coverage and priorities")
