"""
bl/runners/__init__.py — Runner dispatch and built-in runner registration.

Built-in runners are registered at import time. External runners can be
added via `bl.runners.base.register(mode, runner)` before run_question()
is called.
"""

import asyncio

from bl.runners.base import Runner as Runner
from bl.runners.base import RunnerInfo as RunnerInfo
from bl.runners.base import describe as describe
from bl.runners.base import get as get
from bl.runners.base import list_runners as list_runners
from bl.runners.base import register as register
from bl.runners.base import registered_modes as registered_modes
from bl.runners.base import runner_menu as runner_menu


def _register_builtins() -> None:
    """Register the built-in runners. Called once at module import."""
    from bl.runners.agent import run_agent
    from bl.runners.benchmark import run_benchmark
    from bl.runners.browser import run_browser
    from bl.runners.correctness import run_correctness
    from bl.runners.contract import run_contract
    from bl.runners.baseline_check import run_baseline_check
    from bl.runners.document import run_document
    from bl.runners.http import run_http
    from bl.runners.performance import run_performance
    from bl.runners.quality import run_quality
    from bl.runners.simulate import run_simulate
    from bl.runners.subprocess_runner import run_subprocess

    def _performance_sync(question: dict) -> dict:
        return asyncio.run(run_performance(question))

    register(
        "agent",
        run_agent,
        RunnerInfo(
            mode="agent",
            description="LLM agent runner — spawns a specialist Claude agent to investigate a question",
            target_types=["codebase", "api", "document", "any"],
            syntax_summary="Agent:, Target:, Test: (optional)",
            example_question="**Mode**: agent\n**Agent**: diagnose-analyst\n**Target**: src/core/\n**Test**: Does X behave correctly when Y?",
        ),
    )
    register(
        "code_audit",
        run_agent,
        RunnerInfo(
            mode="code_audit",
            description="Semantic alias for agent mode — code audit questions routed to diagnose-analyst",
            target_types=["codebase"],
            syntax_summary="Target: (source files or dirs)",
        ),
    )
    register(
        "http",
        run_http,
        RunnerInfo(
            mode="http",
            description="HTTP runner — fires real HTTP requests, checks status, body, and latency",
            target_types=["api", "service", "url"],
            syntax_summary="GET/POST {url}, expect_status:, expect_body:, latency_threshold_ms:",
            example_question="**Mode**: http\n**Test**: GET http://localhost:8200/health\n  expect_status: 200\n  latency_threshold_ms: 500",
        ),
    )
    register(
        "browser",
        run_browser,
        RunnerInfo(
            mode="browser",
            description="Browser runner — headless Playwright UI testing, checks page content, elements, and load time",
            target_types=["web_ui", "dashboard", "url"],
            syntax_summary="url:, expect_title:, expect_text:, expect_element:, latency_threshold_ms:, screenshot:",
            example_question="**Mode**: browser\n**Test**: url: https://example.com\n  expect_title: Example Domain\n  expect_text: Example\n  screenshot: true",
        ),
    )
    register(
        "subprocess",
        run_subprocess,
        RunnerInfo(
            mode="subprocess",
            description="Subprocess runner — executes shell commands, checks exit codes and stdout patterns",
            target_types=["codebase", "test_suite", "cli"],
            syntax_summary="{command}, expect_exit:, expect_stdout:, expect_not_stdout:, timeout:",
            example_question="**Mode**: subprocess\n**Test**: python -m pytest tests/test_core.py -q\n  expect_exit: 0",
        ),
    )
    register(
        "quality",
        run_quality,
        RunnerInfo(
            mode="quality",
            description="Quality/static analysis runner — reads source files and pattern-matches against quality criteria",
            target_types=["codebase"],
            syntax_summary="Target: (source files or dirs)",
            example_question="**Mode**: quality\n**Target**: src/bl/campaign.py",
        ),
    )
    register(
        "static",
        run_quality,
        RunnerInfo(
            mode="static",
            description="Static analysis runner (alias for quality) — reads source, checks patterns",
            target_types=["codebase"],
            syntax_summary="Target: (source files or dirs)",
        ),
    )
    register(
        "correctness",
        run_correctness,
        RunnerInfo(
            mode="correctness",
            description="Correctness runner — verifies functional correctness by running test suites and checking assertions",
            target_types=["codebase", "test_suite"],
            syntax_summary="Target: (test file or module), Test: (assertion or pattern to verify)",
            example_question="**Mode**: correctness\n**Target**: tests/test_campaign.py\n**Test**: All questions reach a terminal verdict",
        ),
    )
    register(
        "performance",
        _performance_sync,
        RunnerInfo(
            mode="performance",
            description="Performance runner — measures async latency, throughput, and resource usage",
            target_types=["api", "service", "function"],
            syntax_summary="Target: (endpoint or function), latency_threshold_ms:, concurrency:",
            example_question="**Mode**: performance\n**Target**: http://localhost:8200/api/search\n  latency_threshold_ms: 200\n  concurrency: 10",
        ),
    )
    register(
        "simulate",
        run_simulate,
        RunnerInfo(
            mode="simulate",
            description="Simulation runner — sweeps a parameter across a range to find the failure boundary threshold",
            target_types=["simulation", "model", "business_logic"],
            syntax_summary="script:, stress_param:, stress_range:, stress_steps:, baseline_check:",
            example_question="**Mode**: simulate\n**Test**: script: simulate.py\n  stress_param: churn_rate\n  stress_range: [0.05, 0.50]\n  stress_steps: 10",
        ),
    )
    register(
        "benchmark",
        run_benchmark,
        RunnerInfo(
            mode="benchmark",
            description="Benchmark runner — latency, accuracy, and throughput sweeps against ML inference endpoints (Ollama, OpenAI-compat, HTTP)",
            target_types=["ml_endpoint", "api", "service"],
            syntax_summary="endpoint:, provider:, model:, latency_test: | accuracy_test: | throughput_test:",
            example_question=(
                "**Mode**: benchmark\n**Test**: endpoint: http://localhost:11434/api/generate\n"
                "  provider: ollama\n  model: qwen3:14b\n  latency_test:\n"
                "    prompt: Say hello in one word.\n    runs: 5\n    threshold_ms: 10000"
            ),
        ),
    )
    register(
        "contract",
        run_contract,
        RunnerInfo(
            mode="contract",
            description="Contract runner — static analysis of Solana/Anchor smart contracts: signer checks, invariant coverage, overflow patterns, reentrancy, seed canonicalization",
            target_types=["smart_contract", "codebase"],
            syntax_summary="path:, framework: anchor|raw_solana|generic, checks: [invariant_coverage|signer_checks|owner_checks|overflow_patterns|reentrancy_patterns|seed_canonicalization|pattern_search]",
            example_question=(
                "**Mode**: contract\n**Spec**:\n  path: programs/my-program/src/\n"
                "  framework: anchor\n  checks:\n    - type: signer_checks\n"
                "    - type: overflow_patterns\n  max_overflow_sites: 5"
            ),
        ),
    )
    register(
        "document",
        run_document,
        RunnerInfo(
            mode="document",
            description="Document runner — checks doc completeness and accuracy: endpoint/function coverage, example syntax, dead links, keyword presence, freshness",
            target_types=["document", "codebase", "api"],
            syntax_summary="code_path:, doc_path:, checks: [endpoint_coverage|function_coverage|example_syntax|dead_links|keyword_presence|freshness], min_coverage:",
            example_question=(
                "**Mode**: document\n**Spec**:\n  code_path: src/\n  doc_path: README.md\n"
                "  min_coverage: 0.8\n  checks:\n    - type: endpoint_coverage\n"
                "    - type: keyword_presence\n      keywords: [installation, usage]"
            ),
        ),
    )
    register(
        "baseline_check",
        run_baseline_check,
        RunnerInfo(
            mode="baseline_check",
            description="Baseline regression runner — compares a question's latest result against its saved known-good snapshot; FAILURE on verdict regression or metric threshold breach",
            target_types=["any"],
            syntax_summary="question_id:, current_result_file: (optional), fail_on_verdict_change:, fail_on_metric_regression: {metric: threshold_pct}",
            example_question=(
                "**Mode**: baseline_check\n**Spec**:\n  question_id: D1.1\n"
                "  fail_on_verdict_change: true\n  fail_on_metric_regression:\n"
                "    p95_ms: 50\n    pass_rate: 10"
            ),
        ),
    )

    from bl.runners.swarm import run_swarm

    register(
        "swarm",
        run_swarm,
        RunnerInfo(
            mode="swarm",
            description="Swarm meta-runner — runs multiple sub-runners in parallel and aggregates verdicts (worst/majority/any_failure)",
            target_types=["any"],
            syntax_summary="workers: [{id, mode, spec}], max_concurrency:, timeout_seconds:, aggregation: worst|majority|any_failure, weights:",
            example_question=(
                "**Mode**: swarm\n**Spec**:\n  workers:\n"
                "    - id: perf\n      mode: benchmark\n      spec: { ... }\n"
                "    - id: docs\n      mode: document\n      spec: { ... }\n"
                "  aggregation: worst\n  timeout_seconds: 120"
            ),
        ),
    )


_register_builtins()


def load_project_runners(project_root) -> list[str]:
    """
    Scan {project_root}/runners/*.py for custom runner modules.
    Each module must define a `RUNNER_MODE` string and a `run(question) -> dict` function.
    Optionally defines `RUNNER_INFO` as a RunnerInfo instance.
    Returns list of mode names successfully loaded.
    """
    import importlib.util
    import sys
    from pathlib import Path

    runners_dir = Path(project_root) / "runners"
    if not runners_dir.exists():
        return []

    loaded = []
    for py_file in sorted(runners_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                f"project_runner_{py_file.stem}", py_file
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mode = getattr(mod, "RUNNER_MODE", None)
            runner_fn = getattr(mod, "run", None)
            info = getattr(mod, "RUNNER_INFO", None)

            if mode and callable(runner_fn):
                register(mode, runner_fn, info)
                loaded.append(mode)
        except Exception as e:
            print(
                f"[runner-loader] Failed to load {py_file.name}: {e}", file=sys.stderr
            )

    return loaded


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
