"""
bl/local_inference.py — Lightweight local model inference via Ollama.

Routes scoring, classification, and hypothesis generation to the local
Ollama instance (192.168.50.62) instead of the Claude API. Falls back
to the existing heuristic if Ollama is unreachable or times out.
"""

import httpx

from bl.config import cfg

_TIMEOUT = 30.0  # seconds — local LAN call, should be fast

_SYSTEM_PROMPT = (
    "You are a precise classifier for BrickLayer, an autonomous research campaign system. "
    "BrickLayer runs structured question campaigns against production systems (APIs, codebases, databases). "
    "Each result has a verdict (HEALTHY/WARNING/FAILURE/INCONCLUSIVE), a summary, and evidence details. "
    "Verdict meanings: HEALTHY=condition confirmed safe, FAILURE=condition confirmed broken, "
    "WARNING=risk identified but not confirmed, INCONCLUSIVE=could not determine. "
    "Respond only with the exact value requested. No explanation, no preamble."
)


def _ollama_generate(prompt: str, system: str = _SYSTEM_PROMPT) -> str | None:
    """
    Call Ollama /api/generate synchronously. Returns stripped response text,
    or None if the call fails or times out.
    """
    try:
        resp = httpx.post(
            f"{cfg.local_ollama_url}/api/generate",
            json={
                "model": cfg.local_model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 32},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception:
        return None


def classify_failure_type_local(result: dict, mode: str) -> str | None:
    """
    Use local model to classify failure type.
    Returns one of: syntax|logic|hallucination|tool_failure|timeout|unknown
    or None if HEALTHY/WARNING (no failure).
    """
    verdict = result.get("verdict", "")
    if verdict not in ("FAILURE", "INCONCLUSIVE"):
        return None

    summary = result.get("summary", "")[:300]
    details = result.get("details", "")[:300]

    prompt = (
        f"Classify why this research campaign result failed.\n"
        f"Mode: {mode} | Verdict: {verdict}\n"
        f"Summary: {summary}\n"
        f"Details: {details}\n\n"
        "Failure type definitions:\n"
        "  syntax       — Python/code syntax error, parse error, IndentationError\n"
        "  logic        — correct execution but wrong result; test assertion failed\n"
        "  hallucination — agent claimed something without evidence; 'assumed', 'unclear', 'no data'\n"
        "  tool_failure — connection refused, import error, subprocess failed, HTTP error, exit code\n"
        "  timeout      — timed out, ReadTimeout, time limit exceeded\n"
        "  unknown      — cannot determine cause from available information\n\n"
        "Examples:\n"
        "  'ModuleNotFoundError: No module named httpx' → tool_failure\n"
        "  'AssertionError: expected 200 got 404' → logic\n"
        "  'agent assumed the cache was populated' → hallucination\n"
        "  'ReadTimeoutError after 30s' → timeout\n\n"
        "Reply with exactly one word from: syntax, logic, hallucination, tool_failure, timeout, unknown\n\n"
        "Your answer:"
    )

    raw = _ollama_generate(prompt)
    if raw:
        word = raw.lower().split()[0] if raw.split() else ""
        if word in (
            "syntax",
            "logic",
            "hallucination",
            "tool_failure",
            "timeout",
            "unknown",
        ):
            return word
    return None


def classify_confidence_local(result: dict) -> str | None:
    """
    Use local model to classify confidence level.
    Returns one of: high|medium|low|uncertain
    """
    verdict = result.get("verdict", "")
    summary = result.get("summary", "")[:300]
    details = result.get("details", "")[:300]

    prompt = (
        f"Rate the confidence of this research campaign finding.\n"
        f"Verdict: {verdict}\n"
        f"Summary: {summary}\n"
        f"Details: {details}\n\n"
        "Confidence level definitions:\n"
        "  high      — concrete evidence: specific line numbers, file paths, test counts, measured values\n"
        "  medium    — some evidence: issue identified but not fully confirmed; WARNING with specific details\n"
        "  low       — weak evidence: WARNING with vague description; few concrete signals\n"
        "  uncertain — no usable evidence: INCONCLUSIVE verdict, agent could not verify, speculation only\n\n"
        "Examples:\n"
        "  HEALTHY, '23 passed 0 failed', details have test names → high\n"
        "  WARNING, 'embed_batch() swallows failure at line 224', details mention line number → medium\n"
        "  WARNING, 'possible race condition in cache', details are vague → low\n"
        "  INCONCLUSIVE, 'requires agent analysis', no concrete details → uncertain\n\n"
        "Reply with exactly one word from: high, medium, low, uncertain\n\n"
        "Your answer:"
    )

    raw = _ollama_generate(prompt)
    if raw:
        word = raw.lower().split()[0] if raw.split() else ""
        if word in ("high", "medium", "low", "uncertain"):
            return word
    return None


def score_result_local(result: dict) -> float | None:
    """
    Use local model to score result quality 0.0-1.0.
    Falls back to None if unavailable (caller uses formula fallback).
    """
    verdict = result.get("verdict", "")
    summary = result.get("summary", "")[:300]
    details = result.get("details", "")[:300]

    prompt = (
        f"Score the quality of this research finding from 0.0 to 1.0.\n"
        f"Verdict: {verdict}\n"
        f"Summary: {summary}\n"
        f"Details: {details}\n\n"
        "Consider: evidence quality, verdict clarity, whether the result is actionable.\n"
        "Reply with only a decimal number between 0.0 and 1.0.\n\n"
        "Your score:"
    )

    raw = _ollama_generate(prompt)
    if raw:
        try:
            score = float(raw.split()[0])
            if 0.0 <= score <= 1.0:
                return round(score, 2)
        except (ValueError, IndexError):
            pass
    return None


def is_available() -> bool:
    """Quick health check — returns True if Ollama is reachable."""
    try:
        resp = httpx.get(f"{cfg.local_ollama_url}/api/tags", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False
