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
