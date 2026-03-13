"""
bl/runners/__init__.py — Runner dispatch and built-in runner registration.

Built-in runners are registered at import time. External runners can be
added via `bl.runners.base.register(mode, runner)` before run_question()
is called.
"""

import asyncio

from bl.runners.base import Runner, get, register, registered_modes  # noqa: F401


def _register_builtins() -> None:
    """Register the four built-in runners. Called once at module import."""
    from bl.runners.agent import run_agent
    from bl.runners.correctness import run_correctness
    from bl.runners.performance import run_performance
    from bl.runners.quality import run_quality

    def _performance_sync(question: dict) -> dict:
        return asyncio.run(run_performance(question))

    register("performance", _performance_sync)
    register("correctness", run_correctness)
    register("quality", run_quality)
    register("agent", run_agent)
    # static and http are aliases for quality/agent until dedicated runners land
    register("static", run_quality)
    register("http", _performance_sync)


_register_builtins()


def run_question(question: dict) -> dict:
    """Dispatch to the registered runner for question['mode'] and return a verdict envelope."""
    mode = question["mode"]
    qid = question["id"]

    runner = get(mode)
    if runner is not None:
        result = runner(question)
    else:
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": f"Unknown mode '{mode}' — no runner registered",
            "data": {"registered_modes": registered_modes()},
            "details": (
                f"Mode '{mode}' has no registered runner. "
                f"Available: {registered_modes()}. "
                "Use bl.runners.base.register() to add one."
            ),
        }

    result["question_id"] = qid
    result["mode"] = mode
    return result
