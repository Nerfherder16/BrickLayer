"""BL-PluginEval 3-layer scoring infrastructure.

Exports the public API for all scoring layers:
  - StaticAnalyzer functions (Layer 1)
  - LLMJudge (Layer 2)
  - Monte Carlo (Layer 3)
  - Elo ranking utilities
"""
from masonry.src.scoring.static_analyzer import score_agent_file
from masonry.src.scoring.llm_judge import JUDGE_DIMENSIONS, run_judge  # noqa: F401
from masonry.src.scoring.monte_carlo import MonteCarloResult, run_monte_carlo  # noqa: F401
from masonry.src.scoring.elo_ranking import get_leaderboard, update_elo  # noqa: F401

# StaticAnalyzer — expose as a callable namespace alias
StaticAnalyzer = score_agent_file

# LLMJudge — expose as a namespace alias for the run_judge function
LLMJudge = run_judge

__all__ = [
    "StaticAnalyzer",
    "LLMJudge",
    "JUDGE_DIMENSIONS",
    "MonteCarloResult",
    "run_monte_carlo",
    "get_leaderboard",
    "update_elo",
]
