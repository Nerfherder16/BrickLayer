"""
evaluate.py — Evidence-based evaluation for BrickLayer 2.0 non-simulation modes.

Used by: Research, Audit, Diagnose modes
Not used by: Benchmark, Evolve (use simulate.py), Frontier, Fix (use tests directly)

Usage:
    python evaluate.py > run.log 2>&1
    grep "^verdict:" run.log
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# EVALUATION TARGET — Set this to what you are measuring
# =============================================================================

EVALUATION_NAME = "Baseline — describe what is being evaluated"
TARGET_ENDPOINT = ""  # HTTP endpoint to probe, or "" if not applicable
TARGET_FILE = ""  # File path to analyze, or "" if not applicable
TARGET_COMMAND = ""  # Shell command to run, or "" if not applicable

# =============================================================================
# EVIDENCE COLLECTION — Replace with actual measurements
# =============================================================================


def collect_evidence() -> dict:
    """
    Gather evidence about the target system or codebase.
    Returns a dict of raw measurements.

    Replace this stub with actual evidence collection:
    - HTTP requests to TARGET_ENDPOINT
    - File reads from TARGET_FILE
    - Subprocess calls using TARGET_COMMAND
    - Database queries
    """
    return {
        "measured": False,
        "reason": "evaluate.py not yet implemented for this project",
    }


def evaluate(evidence: dict) -> dict:
    """
    Apply verdict thresholds to collected evidence.
    Returns verdict envelope.
    """
    if not evidence.get("measured"):
        return {
            "verdict": "INCONCLUSIVE",
            "primary_metric": "N/A",
            "secondary_metric": "N/A",
            "failure_reason": evidence.get("reason", "Not measured"),
        }

    # TODO: implement project-specific verdict logic
    return {
        "verdict": "HEALTHY",
        "primary_metric": 1.0,
        "secondary_metric": 1.0,
        "failure_reason": "NONE",
    }


if __name__ == "__main__":
    print(f"Evaluation -- {EVALUATION_NAME}")
    evidence = collect_evidence()
    results = evaluate(evidence)
    for key, val in results.items():
        print(f"{key}: {val}")
