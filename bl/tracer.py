"""
bl/tracer.py — C-23: Per-step introspection tracer.

Wraps run_question() to capture a structured trace for every question execution:
  {thought, tool_call, result_summary, latency_ms, confidence, error_type, timestamp}

Traces are written to:
  1. {project}/traces.jsonl  — local append-only log (always)
  2. Recall (bricklayer-trace domain) — if Recall is reachable and BRICKLAYER_TRACE_RECALL=1

Enable Recall tracing via environment variable:
  export BRICKLAYER_TRACE_RECALL=1
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


def _append_trace(trace: dict) -> None:
    """Append a trace record to {project}/traces.jsonl."""
    try:
        from bl.config import cfg

        traces_path: Path = cfg.project_root / "traces.jsonl"
        with traces_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(trace, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[tracer] local write failed: {exc}", file=sys.stderr)


def _store_trace_recall(trace: dict) -> None:
    """Store trace to Recall under bricklayer-trace domain (opt-in)."""
    if os.environ.get("BRICKLAYER_TRACE_RECALL") != "1":
        return
    try:
        from bl.recall_bridge import RECALL_BASE, RECALL_TIMEOUT

        import httpx  # noqa: F401 — only imported when recall available

        qid = trace.get("tool_call", "unknown")
        content = (
            f"[trace:{qid}] {trace.get('thought', '')[:120]} → "
            f"{trace.get('result_summary', '')} "
            f"({trace.get('latency_ms', 0):.0f}ms, {trace.get('confidence', 'uncertain')})"
        )
        payload = {
            "content": content,
            "domain": "bricklayer-trace",
            "tags": [
                "bricklayer",
                "bl:trace",
                f"bl:verdict:{trace.get('verdict', 'UNKNOWN')}",
            ],
            "importance": 0.3,
            "memory_type": "episodic",
        }
        httpx.post(f"{RECALL_BASE}/memories", json=payload, timeout=RECALL_TIMEOUT)
    except Exception:
        pass  # Recall trace is best-effort — never block campaign


def traced(fn: Callable[[dict], dict]) -> Callable[[dict], dict]:
    """
    Decorator that wraps a run_question-style callable with introspection tracing.

    Usage:
        runner = traced(run_question)
        result = runner(question)
    """

    def wrapper(question: dict) -> dict:
        start = time.monotonic()
        result: dict = {}
        try:
            result = fn(question)
        except Exception as exc:
            result = {
                "verdict": "INCONCLUSIVE",
                "summary": f"Runner raised exception: {exc}",
                "data": {},
                "details": str(exc),
                "failure_type": "tool_failure",
                "confidence": "uncertain",
            }
            raise
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "thought": question.get("title", question.get("id", "")),
                "tool_call": f"{question.get('mode', 'unknown')}:{question.get('agent', question.get('id', ''))}",
                "verdict": result.get("verdict", "UNKNOWN"),
                "result_summary": result.get("summary", "")[:200],
                "latency_ms": round(elapsed_ms, 1),
                "confidence": result.get("confidence", "uncertain"),
                "error_type": result.get("failure_type"),
                "question_id": question.get("id"),
                "domain": question.get("domain"),
            }
            _append_trace(trace)
            _store_trace_recall(trace)

        return result

    return wrapper


def load_traces(project_root: Path | str | None = None) -> list[dict]:
    """
    Load all traces from {project_root}/traces.jsonl.
    Returns list of trace dicts, oldest first.
    """
    if project_root is None:
        from bl.config import cfg

        project_root = cfg.project_root

    traces_path = Path(project_root) / "traces.jsonl"
    if not traces_path.exists():
        return []

    traces = []
    for line in traces_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return traces
