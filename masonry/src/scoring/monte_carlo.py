"""Layer 3: Monte Carlo statistical validation via repeated sampling.

Runs an agent on N random samples from test_cases (with replacement),
computes accuracy, Wilson confidence interval, and Elo delta.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class MonteCarloResult:
    """Results from a Monte Carlo evaluation run."""

    n_trials: int
    n_pass: int
    accuracy: float
    wilson_ci_low: float
    wilson_ci_high: float
    elo_delta: float


def _wilson_ci(n_pass: int, n_trials: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score interval at given z-score (default 95% CI)."""
    if n_trials == 0:
        return 0.0, 1.0
    p_hat = n_pass / n_trials
    denominator = 1 + z * z / n_trials
    centre = (p_hat + z * z / (2 * n_trials)) / denominator
    margin = (z / denominator) * math.sqrt(
        p_hat * (1 - p_hat) / n_trials + z * z / (4 * n_trials * n_trials)
    )
    low = max(0.0, centre - margin)
    high = min(1.0, centre + margin)
    return low, high


def compute_elo_delta(
    wins: int,
    losses: int,
    k: float = 32.0,
    opponent_elo: float = 1200.0,
    agent_elo: float = 1200.0,
) -> float:
    """Compute net Elo delta from a batch of wins/losses.

    Uses the standard Elo formula: delta = K * (score - expected).
    Score = wins / (wins + losses).
    Expected = 1 / (1 + 10^((opponent_elo - agent_elo)/400)).
    """
    total = wins + losses
    if total == 0:
        return 0.0
    score = wins / total
    expected = 1.0 / (1.0 + 10.0 ** ((opponent_elo - agent_elo) / 400.0))
    return k * (score - expected)


def run_monte_carlo(
    agent_name: str,
    test_cases: list[dict[str, Any]],
    n: int = 50,
    base_dir: Any = None,
    _run_fn: Callable[[str, dict[str, Any], Any], bool] | None = None,
) -> MonteCarloResult:
    """Run agent on N random samples from test_cases (with replacement).

    Args:
        agent_name: Name of the agent being evaluated.
        test_cases: Pool of test cases to sample from.
        n: Number of trials to run.
        base_dir: Base directory for agent resolution (passed to _run_fn).
        _run_fn: Callable(agent_name, task, base_dir) -> bool.
                 If None, no trials run (n_pass = 0).

    Returns:
        MonteCarloResult with accuracy, Wilson CI, and Elo delta.
    """
    if not test_cases:
        return MonteCarloResult(
            n_trials=0,
            n_pass=0,
            accuracy=0.0,
            wilson_ci_low=0.0,
            wilson_ci_high=1.0,
            elo_delta=0.0,
        )

    n_pass = 0
    for _ in range(n):
        task = random.choice(test_cases)
        if _run_fn is not None:
            if _run_fn(agent_name, task, base_dir):
                n_pass += 1

    accuracy = n_pass / n if n > 0 else 0.0
    ci_low, ci_high = _wilson_ci(n_pass, n)
    elo_delta = compute_elo_delta(wins=n_pass, losses=n - n_pass)

    return MonteCarloResult(
        n_trials=n,
        n_pass=n_pass,
        accuracy=accuracy,
        wilson_ci_low=ci_low,
        wilson_ci_high=ci_high,
        elo_delta=elo_delta,
    )
