"""Runner dispatch — maps question mode to the correct runner."""

import asyncio


def run_question(question: dict) -> dict:
    """Dispatch to the correct mode runner and return a verdict envelope."""
    from bl.runners.agent import run_agent
    from bl.runners.correctness import run_correctness
    from bl.runners.performance import run_performance
    from bl.runners.quality import run_quality

    mode = question["mode"]
    qid = question["id"]

    if mode == "performance":
        result = asyncio.run(run_performance(question))
    elif mode == "correctness":
        result = run_correctness(question)
    elif mode == "quality":
        result = run_quality(question)
    elif mode == "agent":
        result = run_agent(question)
    else:
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": f"Unknown mode '{mode}'",
            "data": {},
            "details": "",
        }

    result["question_id"] = qid
    result["mode"] = mode
    return result
