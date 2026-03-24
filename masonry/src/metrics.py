"""masonry/src/metrics.py

Heuristic scoring metrics for Masonry agent evaluation.
No DSPy dependency — pure Python.
"""

from __future__ import annotations

import re
from typing import Any


def build_metric(signature_cls: type = object) -> Any:
    """Heuristic scoring metric for research-domain agents.

    Components:
    - verdict_match (0.4): exact string match
    - evidence_quality (0.4): len > 300 AND (numbers OR threshold language) = 1.0, else 0.5
    - confidence_calibration (0.2): 1 - |predicted - 0.75|
    """
    _THRESHOLD_KEYWORDS = ("threshold", "baseline", "%", "ms", "pts", "seconds")

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0

        try:
            ex_verdict = str(getattr(example, "verdict", "") or "").strip()
            pred_verdict = str(getattr(prediction, "verdict", "") or "").strip()
            if ex_verdict and pred_verdict and ex_verdict == pred_verdict:
                score += 0.4
        except Exception:
            pass

        try:
            evidence = str(getattr(prediction, "evidence", "") or "")
            has_numbers = bool(re.search(r"\d+\.?\d*", evidence))
            has_threshold_language = any(kw in evidence.lower() for kw in _THRESHOLD_KEYWORDS)
            if len(evidence) > 300 and (has_numbers or has_threshold_language):
                score += 0.4
            else:
                score += 0.2
        except Exception:
            pass

        try:
            raw = str(getattr(prediction, "confidence", "0.75") or "0.75")
            pred_conf = float(raw)
            score += 0.2 * (1.0 - abs(pred_conf - 0.75))
        except (ValueError, TypeError):
            pass

        return score

    return metric


def build_karen_metric() -> Any:
    """Heuristic scoring metric for the karen ops-domain agent.

    Components:
    - quality_score_proximity (0.5)
    - action_match (0.3)
    - changelog_quality (0.2)
    """

    def _derive_expected(example: Any) -> tuple[float, str]:
        ex_reverted = getattr(example, "reverted", None)
        if ex_reverted is not None:
            if ex_reverted:
                return 0.0, "reverted"
            ex_doc_files = getattr(example, "doc_files_written", 0) or 0
            return (1.0, "updated") if ex_doc_files > 0 else (1.0, "skipped")
        ex_qs = float(str(getattr(example, "quality_score", "1.0") or "1.0"))
        ex_action = str(getattr(example, "action", "") or "").lower().strip()
        return ex_qs, ex_action

    def metric(example: Any, prediction: Any, trace: Any = None) -> float:
        score = 0.0
        try:
            ex_val, ex_action = _derive_expected(example)
        except Exception:
            ex_val, ex_action = 1.0, ""

        try:
            pred_qs_raw = str(getattr(prediction, "quality_score", "") or "")
            m = re.search(r"\d+\.?\d*", pred_qs_raw)
            if m:
                pred_val = float(m.group())
                score += 0.5 if abs(ex_val - pred_val) <= 0.1 else 0.25
            else:
                score += 0.25
        except Exception:
            score += 0.25

        try:
            pred_action = str(getattr(prediction, "action", "") or "").lower().strip()
            if ex_action and pred_action and ex_action == pred_action:
                score += 0.3
            elif ex_action and pred_action and (
                (ex_action in ("updated", "created")) == (pred_action in ("updated", "created"))
            ):
                score += 0.15
        except Exception:
            pass

        try:
            entry = str(getattr(prediction, "changelog_entry", "") or "")
            if ex_action != "skipped" and len(entry) > 10:
                score += 0.2
            elif ex_action == "skipped":
                score += 0.2
        except Exception:
            pass

        return score

    return metric
