"""
bl/quality.py — Remediation feasibility estimation (C-29).
"""


def estimate_remediation_feasibility(
    action_type: str,
    current_mean: float,
    healthy_threshold: float,
    floor: float | None = None,
    n_affected: int = 0,
    corpus_size: int = 1,
) -> dict:
    """
    Model whether a corrective action can move current_mean past healthy_threshold.
    Returns dict with: feasible (bool), projected_mean (float), delta (float), reason (str).
    """
    if action_type == "amnesty" and floor is not None:
        # Amnesty boosts memories below floor TO floor. Only affects mean if floor > current_mean.
        if floor <= current_mean:
            projected = current_mean
            delta = 0.0
            reason = f"amnesty floor={floor:.2f} <= current mean={current_mean:.3f} — no delta possible"
        else:
            # Max possible delta: if ALL corpus moved from current_mean to floor
            max_delta = (floor - current_mean) * (n_affected / corpus_size)
            projected = current_mean + max_delta
            delta = max_delta
            reason = f"amnesty floor={floor:.2f} on {n_affected}/{corpus_size} memories → projected_mean={projected:.3f}"
        feasible = projected >= healthy_threshold
        return {
            "feasible": feasible,
            "projected_mean": projected,
            "delta": delta,
            "reason": reason,
        }

    # Generic: unknown action type
    return {
        "feasible": None,
        "projected_mean": None,
        "delta": None,
        "reason": f"unknown action_type '{action_type}' — cannot estimate",
    }
