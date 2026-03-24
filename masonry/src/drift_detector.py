"""masonry/src/drift_detector.py

Public re-export shim for the drift detection module.

The canonical implementation lives in masonry.src.dspy_pipeline.drift_detector.
This module exists so that mcp_server/server.py can import run_drift_check
from a stable path (masonry.src.drift_detector) without embedding the
internal dspy_pipeline package path in the server.
"""

from masonry.src.dspy_pipeline.drift_detector import (  # noqa: F401
    DriftReport,
    detect_drift,
    run_drift_check,
)

__all__ = ["DriftReport", "detect_drift", "run_drift_check"]
