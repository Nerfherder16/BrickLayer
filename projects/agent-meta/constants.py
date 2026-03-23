"""
Agent Meta-Campaign — Constants
These are immutable thresholds for scoring the agent fleet.
Never edit these — they represent the minimum bar for a production-ready agent.
"""

# --- AGENT QUALITY THRESHOLDS ---

# Minimum description length (chars) for forge-check to consider an agent "covered"
MIN_DESCRIPTION_LENGTH = 50

# Minimum required sections in any agent .md file
REQUIRED_SECTIONS = [
    "## Inputs",
    "## Output contract",
    "## Recall",
]

# Sections required only for agents that write findings
FINDING_AGENT_REQUIRED_SECTIONS = [
    "## Evidence",
]

# Maximum acceptable responsibility overlap score (0.0–1.0, based on description similarity)
MAX_OVERLAP_SCORE = 0.35

# Minimum definitive rate for a healthy agent (from agent-auditor scoring)
MIN_DEFINITIVE_RATE = 0.80

# Minimum fix spec completeness for diagnose-analyst
MIN_FIX_SPEC_COMPLETENESS = 0.80

# Maximum number of phantom agents (agents called but no .md file)
MAX_PHANTOM_AGENTS = 0

# Minimum evidence depth (% of findings with code blocks or file paths in Evidence)
MIN_EVIDENCE_DEPTH = 0.80

# Required baseline fleet — these agents must always exist
REQUIRED_AGENTS = [
    "mortar",
    "question-designer",
    "hypothesis-generator",
    "diagnose-analyst",
    "fix-implementer",
    "synthesizer",
    "planner",
    "code-reviewer",
    "peer-reviewer",
    "forge-check",
    "agent-auditor",
]

# Verdict taxonomy — all valid verdicts in BL 2.0
VALID_VERDICTS = [
    "DIAGNOSIS_COMPLETE",
    "FIXED",
    "COMPLIANT",
    "NON_COMPLIANT",
    "HEALTHY",
    "CALIBRATED",
    "IMPROVEMENT",
    "PROBABLE",
    "IMMINENT",
    "ALERT",
    "CONFIRMED",
    "CONCERNS",
    "OVERRIDE",
    "INCONCLUSIVE",
    "FLEET_COMPLETE",
    "GAPS_FOUND",
    "FLEET_HEALTHY",
    "FLEET_WARNING",
    "FLEET_UNDERPERFORMING",
    "PLAN_COMPLETE",
    "APPROVED",
    "NEEDS_REVISION",
    "BLOCKED",
    "RE_QUEUED",
    "WAVE_COMPLETE",
    "CAMPAIGN_COMPLETE",
]
