"""Monte Carlo agent evaluation with Wilson confidence intervals and Elo delta."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Optional

_ELO_BASE = 1200
_ELO_K = 32
_WILSON_Z = 1.96  # 95% CI


@dataclass
class MonteCarloResult:
    n_trials: int
    n_pass: int
    accuracy: float
    wilson_ci_low: float
    wilson_ci_high: float
    elo_delta: float


def _wilson_ci(n_pass: int, n_trials: int, z: float = _WILSON_Z) -> tuple[float, float]:
    """Wilson score interval for a proportion."""
    if n_trials == 0:
        return 0.0, 1.0
    p = n_pass / n_trials
    denom = 1 + z**2 / n_trials
    centre = (p + z**2 / (2 * n_trials)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n_trials + z**2 / (4 * n_trials**2))) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def compute_elo_delta(wins: int, losses: int, opponent_elo: int = _ELO_BASE) -> float:
    """Expected Elo delta for an agent with wins/losses against a fixed opponent."""
    n = wins + losses
    if n == 0:
        return 0.0
    score = wins / n
    # Assume agent starts at 1200 for expected calculation
    expected = 1 / (1 + 10 ** ((opponent_elo - _ELO_BASE) / 400))
    return _ELO_K * (score - expected)


def run_monte_carlo(
    agent_name: str,
    test_cases: list[dict[str, Any]],
    n: int,
    base_dir: Any,
    _run_fn: Optional[Callable[[str, dict, Any], bool]] = None,
) -> MonteCarloResult:
    """Run n Monte Carlo trials sampling from test_cases with replacement."""
    if not test_cases:
        return MonteCarloResult(
            n_trials=n, n_pass=0, accuracy=0.0,
            wilson_ci_low=0.0, wilson_ci_high=0.0, elo_delta=compute_elo_delta(0, n),
        )

    n_pass = 0
    for _ in range(n):
        task = random.choice(test_cases)
        if _run_fn is not None and _run_fn(agent_name, task, base_dir):
            n_pass += 1

    accuracy = n_pass / n if n > 0 else 0.0
    ci_low, ci_high = _wilson_ci(n_pass, n)
    delta = compute_elo_delta(n_pass, n - n_pass)

    return MonteCarloResult(
        n_trials=n,
        n_pass=n_pass,
        accuracy=accuracy,
        wilson_ci_low=ci_low,
        wilson_ci_high=ci_high,
        elo_delta=delta,
    )
