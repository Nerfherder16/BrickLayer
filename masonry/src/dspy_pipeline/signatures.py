"""masonry/src/dspy_pipeline/signatures.py

DSPy Signature classes for Masonry agent optimization.

DSPy must be installed for full functionality. If not installed, stub classes
are provided so other modules can import without error.
"""

from __future__ import annotations

try:
    import dspy

    class ResearchAgentSig(dspy.Signature):
        """Analyze a research question about a business model and produce a structured finding."""

        question_text: str = dspy.InputField(desc="The research question to investigate")
        project_context: str = dspy.InputField(desc="Background context about the project under analysis")
        constraints: str = dspy.InputField(desc="Known constraints or invariants for this project")

        verdict: str = dspy.OutputField(desc="HEALTHY | WARNING | FAILURE | OK | NON_COMPLIANT | COMPLIANT")
        severity: str = dspy.OutputField(desc="Info | Low | Medium | High | Critical")
        evidence: str = dspy.OutputField(desc="Detailed evidence supporting the verdict (min 100 chars)")
        mitigation: str = dspy.OutputField(desc="Recommended mitigation steps, or empty if none needed")
        confidence: str = dspy.OutputField(desc="Confidence score as a float string between 0.0 and 1.0")

    class KarenSig(dspy.Signature):
        """Organize project documentation, roadmaps, and changelogs."""

        task_description: str = dspy.InputField(desc="Description of the documentation or organization task")
        project_context: str = dspy.InputField(desc="Background context about the project")
        existing_content: str = dspy.InputField(desc="Existing content to update or organize")

        updated_content: str = dspy.OutputField(desc="The organized or updated document content")
        summary: str = dspy.OutputField(desc="Brief summary of changes made")
        confidence: str = dspy.OutputField(desc="Confidence score as a float string between 0.0 and 1.0")

    class DiagnoseAgentSig(dspy.Signature):
        """Diagnose a failing system or test and propose a fix strategy."""

        symptoms: str = dspy.InputField(desc="Observed symptoms or error messages")
        affected_files: str = dspy.InputField(desc="Files or modules involved in the failure")
        prior_attempts: str = dspy.InputField(desc="Previous fix attempts that did not resolve the issue")

        root_cause: str = dspy.OutputField(desc="Root cause analysis of the failure")
        fix_strategy: str = dspy.OutputField(desc="Concrete strategy to fix the root cause")
        affected_scope: str = dspy.OutputField(desc="Scope of files or components affected by the fix")
        confidence: str = dspy.OutputField(desc="Confidence in the diagnosis as a float string 0.0-1.0")

    class SynthesizerSig(dspy.Signature):
        """Synthesize a set of research findings into a coherent summary."""

        findings_summary: str = dspy.InputField(desc="Combined text of all findings to synthesize")
        question_list: str = dspy.InputField(desc="List of questions that were investigated")

        synthesis_text: str = dspy.OutputField(desc="Narrative synthesis of the findings")
        key_themes: str = dspy.OutputField(desc="Comma-separated list of key themes identified")
        recommendations: str = dspy.OutputField(desc="Prioritized list of recommendations")

    class QuestionDesignerSig(dspy.Signature):
        """Design a targeted question bank for stress-testing a business model."""

        project_brief: str = dspy.InputField(desc="Project brief describing the system under test")
        docs_summary: str = dspy.InputField(desc="Summary of supporting documentation")
        prior_findings: str = dspy.InputField(desc="Prior findings to avoid duplicating questions")

        questions_yaml: str = dspy.OutputField(desc="YAML-formatted question bank")
        coverage_rationale: str = dspy.OutputField(desc="Rationale for domain coverage decisions")

except ImportError:
    # Stub classes for environments without DSPy installed.
    class ResearchAgentSig:  # type: ignore[no-redef]
        pass

    class KarenSig:  # type: ignore[no-redef]
        pass

    class DiagnoseAgentSig:  # type: ignore[no-redef]
        pass

    class SynthesizerSig:  # type: ignore[no-redef]
        pass

    class QuestionDesignerSig:  # type: ignore[no-redef]
        pass
