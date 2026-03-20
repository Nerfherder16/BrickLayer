"""
bl/runners/benchmark.py — ML inference endpoint benchmark runner.

Runs latency, throughput, and accuracy sweeps against Ollama,
OpenAI-compatible APIs, or any HTTP inference endpoint to find
failure/degradation boundaries.

Handles questions with mode: benchmark

Spec format (under the 'spec' key in the question dict, or parsed from
the 'test' field as YAML-like text):

    endpoint: "http://localhost:11434/api/generate"
    provider: "ollama"          # "ollama" | "openai" | "http"
    model: "qwen3:14b"

    # Pick one test type:

    latency_test:
      prompt: "Say hello in one word."
      runs: 5
      threshold_ms: 10000       # FAILURE if p95 > this
      warning_ms: 5000          # WARNING if p95 > this

    accuracy_test:
      prompts:
        - input: "What is 2+2?"
          expected_contains: "4"
        - input: "Capital of France?"
          expected_contains: "Paris"
      pass_threshold: 0.8       # FAILURE if pass_rate < this

    throughput_test:
      prompt: "Count to 5."
      concurrent: 3
      duration_seconds: 30
      min_rps: 0.5              # FAILURE if achieved RPS < this

    # Optional:
    timeout: 30
    api_key: null
    extra_headers: {}
"""

import statistics
import threading
import time
from typing import Any

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

# ---------------------------------------------------------------------------
# Spec extraction
# ---------------------------------------------------------------------------


def _extract_spec(question: dict) -> dict | None:
    """Return the benchmark spec dict from the question, or None if missing/malformed.

    Accepts either:
    - question["spec"]  — already a dict (pre-parsed by caller)
    - question["test"] / question["Test"] — YAML-like text to parse
    """
    spec = question.get("spec")
    if isinstance(spec, dict):
        return spec

    test_field = question.get("test", "") or question.get("Test", "")
    if test_field:
        return _parse_spec_text(test_field)

    return None


def _parse_spec_text(text: str) -> dict:
    """Parse a YAML-like benchmark spec from the Test field.

    Handles top-level keys and one level of nesting (indented key: value pairs
    and list items prefixed with '- ').  Does not require pyyaml.
    """
    spec: dict[str, Any] = {}
    current_section: str | None = None
    current_list_item: dict | None = None
    list_target: list | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        # List item under a nested section (e.g. prompts entries)
        if stripped.startswith("- ") and current_section and indent >= 4:
            # Flush any prior list item
            if current_list_item is not None and list_target is not None:
                list_target.append(current_list_item)
            current_list_item = {}
            # Inline key: value on the same line as '-'
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                if current_list_item is not None:
                    current_list_item[k.strip()] = _coerce(v.strip())
            continue

        # Key: value inside a list item (deeper indent)
        if current_list_item is not None and indent >= 6 and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_list_item[k.strip()] = _coerce(v.strip())
            continue

        # Flush pending list item when indent drops
        if current_list_item is not None and indent < 6:
            if list_target is not None:
                list_target.append(current_list_item)
            current_list_item = None
            list_target = None

        # Nested key: value under a section (indent 2-5)
        if indent >= 2 and current_section and ":" in stripped:
            k, _, v = stripped.partition(":")
            key = k.strip()
            val_str = v.strip()
            section_dict = spec.get(current_section)
            if not isinstance(section_dict, dict):
                spec[current_section] = {}
                section_dict = spec[current_section]
            if not val_str:
                # Start of a nested list (e.g. "prompts:")
                section_dict[key] = []
                list_target = section_dict[key]
            else:
                section_dict[key] = _coerce(val_str)
            continue

        # Top-level key: value (indent 0-1)
        if ":" in stripped and indent < 2:
            k, _, v = stripped.partition(":")
            key = k.strip()
            val_str = v.strip()
            if not val_str:
                # Section header (e.g. "latency_test:")
                spec[key] = {}
                current_section = key
            else:
                spec[key] = _coerce(val_str)
                current_section = None
            continue

    # Flush trailing list item
    if current_list_item is not None and list_target is not None:
        list_target.append(current_list_item)

    return spec


def _coerce(raw: str) -> Any:
    """Coerce a string value to int, float, bool, None, or keep as str."""
    if raw.lower() in ("null", "none", "~"):
        return None
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    # Strip surrounding quotes
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _build_client(spec: dict) -> "httpx.Client":
    api_key = spec.get("api_key")
    extra_headers = spec.get("extra_headers") or {}
    headers: dict[str, str] = dict(extra_headers)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    timeout = float(spec.get("timeout", 30))
    return httpx.Client(headers=headers, timeout=timeout)


def _make_request(
    client: "httpx.Client",
    endpoint: str,
    provider: str,
    model: str,
    prompt: str,
) -> tuple[str, float]:
    """Send a single inference request and return (response_text, elapsed_ms).

    Raises httpx.HTTPError or httpx.TimeoutException on failure.
    """
    start = time.monotonic()

    if provider == "ollama":
        payload = {"model": model, "prompt": prompt, "stream": False}
        resp = client.post(endpoint, json=payload)
        resp.raise_for_status()
        body = resp.json()
        text = body.get("response", "")

    elif provider == "openai":
        # endpoint is base URL; append /chat/completions
        url = endpoint.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        body = resp.json()
        text = body["choices"][0]["message"]["content"]

    else:
        # Generic HTTP: POST JSON body, expect text in response
        payload = {"model": model, "prompt": prompt}
        resp = client.post(endpoint, json=payload)
        resp.raise_for_status()
        try:
            body = resp.json()
            text = (
                body.get("response")
                or body.get("text")
                or body.get("content")
                or str(body)
            )
        except Exception:
            text = resp.text

    elapsed_ms = (time.monotonic() - start) * 1000.0
    return text, elapsed_ms


def _percentile(values: list[float], p: float) -> float:
    """Compute the p-th percentile of values (0-100). Requires at least 1 value."""
    if len(values) == 1:
        return values[0]
    sorted_vals = sorted(values)
    idx = (p / 100.0) * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


# ---------------------------------------------------------------------------
# Test implementations
# ---------------------------------------------------------------------------


def _run_latency_test(client: "httpx.Client", spec: dict, lt: dict) -> dict:
    """Run sequential latency test and return verdict envelope."""
    endpoint = spec["endpoint"]
    provider = spec.get("provider", "ollama")
    model = spec.get("model", "")
    prompt = lt.get("prompt", "Hello.")
    runs = int(lt.get("runs", 5))
    threshold_ms = float(lt.get("threshold_ms", 10000))
    warning_ms = float(lt.get("warning_ms", threshold_ms * 0.5))

    latencies: list[float] = []
    errors: list[str] = []

    for i in range(runs):
        try:
            _, elapsed = _make_request(client, endpoint, provider, model, prompt)
            latencies.append(elapsed)
        except Exception as exc:
            errors.append(f"run {i + 1}: {exc}")

    if not latencies:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"latency_test: all {runs} runs failed — {errors[0] if errors else 'unknown error'}",
            "data": {"test_type": "latency", "runs": runs, "errors": errors},
            "details": (
                f"Endpoint: {endpoint}\n"
                f"Model: {model}\n"
                f"All {runs} requests failed:\n" + "\n".join(f"  {e}" for e in errors)
            ),
        }

    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)

    if p95 > threshold_ms:
        verdict = "FAILURE"
        reason = f"p95 {p95:.0f}ms > failure threshold {threshold_ms:.0f}ms"
    elif p95 > warning_ms:
        verdict = "WARNING"
        reason = f"p95 {p95:.0f}ms > warning threshold {warning_ms:.0f}ms"
    else:
        verdict = "HEALTHY"
        reason = f"p95 {p95:.0f}ms within thresholds"

    summary = (
        f"latency_test {model} — p50={p50:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms"
        f" ({runs - len(errors)}/{runs} ok) | {reason}"
    )
    detail_lines = [
        f"Endpoint: {endpoint}",
        f"Provider: {provider}",
        f"Model: {model}",
        f"Runs: {runs} ({len(errors)} errors)",
        f"Latencies (ms): {[round(v, 1) for v in latencies]}",
        f"p50: {p50:.1f}ms",
        f"p95: {p95:.1f}ms",
        f"p99: {p99:.1f}ms",
        f"Warning threshold: {warning_ms:.0f}ms",
        f"Failure threshold: {threshold_ms:.0f}ms",
        f"Verdict reason: {reason}",
    ]
    if errors:
        detail_lines.append("Errors: " + "; ".join(errors))

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "test_type": "latency",
            "p50_ms": round(p50, 1),
            "p95_ms": round(p95, 1),
            "p99_ms": round(p99, 1),
            "runs_ok": runs - len(errors),
            "runs_total": runs,
            "errors": errors,
        },
        "details": "\n".join(detail_lines),
    }


def _run_accuracy_test(client: "httpx.Client", spec: dict, at: dict) -> dict:
    """Run accuracy test against a list of prompt/expected pairs."""
    endpoint = spec["endpoint"]
    provider = spec.get("provider", "ollama")
    model = spec.get("model", "")
    prompts = at.get("prompts") or []
    pass_threshold = float(at.get("pass_threshold", 0.8))

    if not prompts:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "accuracy_test: no prompts defined in spec",
            "data": {"test_type": "accuracy", "error": "no_prompts"},
            "details": "The accuracy_test.prompts list is empty or missing.",
        }

    results: list[dict] = []
    passed = 0

    for entry in prompts:
        prompt_text = entry.get("input") or entry.get("prompt", "")
        expected = entry.get("expected_contains", "")
        try:
            response_text, elapsed = _make_request(
                client, endpoint, provider, model, prompt_text
            )
            ok = expected.lower() in response_text.lower() if expected else True
            if ok:
                passed += 1
            results.append(
                {
                    "input": prompt_text,
                    "expected_contains": expected,
                    "response_preview": response_text[:120],
                    "elapsed_ms": round(elapsed, 1),
                    "pass": ok,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "input": prompt_text,
                    "expected_contains": expected,
                    "error": str(exc),
                    "pass": False,
                }
            )

    total = len(prompts)
    pass_rate = passed / total if total > 0 else 0.0

    if pass_rate < pass_threshold:
        verdict = "FAILURE"
        reason = f"pass_rate {pass_rate:.0%} < threshold {pass_threshold:.0%}"
    else:
        verdict = "HEALTHY"
        reason = f"pass_rate {pass_rate:.0%} >= threshold {pass_threshold:.0%}"

    failed_cases = [r for r in results if not r.get("pass")]
    summary = (
        f"accuracy_test {model} — {passed}/{total} passed ({pass_rate:.0%}) | {reason}"
    )
    detail_lines = [
        f"Endpoint: {endpoint}",
        f"Provider: {provider}",
        f"Model: {model}",
        f"Total prompts: {total}",
        f"Passed: {passed}",
        f"Pass rate: {pass_rate:.1%}",
        f"Pass threshold: {pass_threshold:.1%}",
        "",
        "Results:",
    ]
    for r in results:
        status = "PASS" if r.get("pass") else "FAIL"
        if "error" in r:
            detail_lines.append(f"  [{status}] {r['input']!r} → ERROR: {r['error']}")
        else:
            detail_lines.append(
                f"  [{status}] {r['input']!r} → expected {r['expected_contains']!r}"
                f" in {r.get('response_preview', '')!r}"
            )

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "test_type": "accuracy",
            "pass_rate": round(pass_rate, 4),
            "passed": passed,
            "total": total,
            "failed_cases": failed_cases,
        },
        "details": "\n".join(detail_lines),
    }


def _run_throughput_test(client: "httpx.Client", spec: dict, tt: dict) -> dict:
    """Run concurrent throughput test over a fixed duration."""
    endpoint = spec["endpoint"]
    provider = spec.get("provider", "ollama")
    model = spec.get("model", "")
    prompt = tt.get("prompt", "Hello.")
    concurrent = int(tt.get("concurrent", 3))
    duration_seconds = float(tt.get("duration_seconds", 30))
    min_rps = float(tt.get("min_rps", 0.5))

    completed_lock = threading.Lock()
    completed: list[float] = []  # elapsed_ms per successful request
    errors: list[str] = []
    stop_event = threading.Event()

    def worker() -> None:
        # Re-create a client per thread; httpx.Client is not thread-safe for sharing
        thread_client = _build_client(spec)
        try:
            while not stop_event.is_set():
                try:
                    _, elapsed = _make_request(
                        thread_client, endpoint, provider, model, prompt
                    )
                    with completed_lock:
                        completed.append(elapsed)
                except Exception as exc:
                    with completed_lock:
                        errors.append(str(exc))
        finally:
            thread_client.close()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(concurrent)]
    wall_start = time.monotonic()
    for t in threads:
        t.start()

    time.sleep(duration_seconds)
    stop_event.set()

    for t in threads:
        t.join(timeout=float(spec.get("timeout", 30)) + 2)

    wall_elapsed = time.monotonic() - wall_start
    total_ok = len(completed)
    achieved_rps = total_ok / wall_elapsed if wall_elapsed > 0 else 0.0

    if total_ok == 0:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": (
                f"throughput_test: 0 successful requests in {wall_elapsed:.1f}s"
                f" — {errors[0] if errors else 'unknown error'}"
            ),
            "data": {
                "test_type": "throughput",
                "rps": 0.0,
                "concurrent": concurrent,
                "duration_seconds": duration_seconds,
                "errors": errors[:10],
            },
            "details": (
                f"Endpoint: {endpoint}\nModel: {model}\n"
                f"No requests completed in {wall_elapsed:.1f}s.\n"
                "Errors:\n" + "\n".join(f"  {e}" for e in errors[:10])
            ),
        }

    avg_latency = statistics.mean(completed)
    p95_latency = _percentile(completed, 95)

    if achieved_rps < min_rps:
        verdict = "FAILURE"
        reason = f"achieved {achieved_rps:.2f} RPS < min_rps {min_rps}"
    else:
        verdict = "HEALTHY"
        reason = f"achieved {achieved_rps:.2f} RPS >= min_rps {min_rps}"

    summary = (
        f"throughput_test {model} — {achieved_rps:.2f} RPS"
        f" ({total_ok} reqs / {wall_elapsed:.1f}s, {concurrent} workers)"
        f" | {reason}"
    )
    detail_lines = [
        f"Endpoint: {endpoint}",
        f"Provider: {provider}",
        f"Model: {model}",
        f"Concurrent workers: {concurrent}",
        f"Test duration: {wall_elapsed:.1f}s (target: {duration_seconds}s)",
        f"Requests completed: {total_ok}",
        f"Request errors: {len(errors)}",
        f"Achieved RPS: {achieved_rps:.3f}",
        f"Min RPS threshold: {min_rps}",
        f"Avg latency: {avg_latency:.0f}ms",
        f"p95 latency: {p95_latency:.0f}ms",
        f"Verdict reason: {reason}",
    ]
    if errors:
        detail_lines.append(f"Sample errors: {'; '.join(errors[:5])}")

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "test_type": "throughput",
            "rps": round(achieved_rps, 3),
            "requests_ok": total_ok,
            "request_errors": len(errors),
            "duration_actual_s": round(wall_elapsed, 2),
            "concurrent": concurrent,
            "avg_latency_ms": round(avg_latency, 1),
            "p95_ms": round(p95_latency, 1),
        },
        "details": "\n".join(detail_lines),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_benchmark(question: dict) -> dict:
    """Execute an ML endpoint benchmark and return a verdict envelope.

    Dispatches to latency_test, accuracy_test, or throughput_test depending
    on which key is present in the spec (first match wins).
    """
    if not _HTTPX_AVAILABLE:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "httpx not installed — benchmark runner unavailable",
            "data": {"error": "httpx_not_installed"},
            "details": (
                "httpx is required for the benchmark runner.\n"
                "Install it with:  pip install httpx"
            ),
        }

    spec = _extract_spec(question)

    if not spec:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "benchmark runner: no spec found in question",
            "data": {"error": "missing_spec"},
            "details": (
                "The question must supply a 'spec' dict or a 'test' field "
                "with benchmark directives (endpoint:, provider:, model:, and one test type)."
            ),
        }

    endpoint = spec.get("endpoint")
    if not endpoint:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "benchmark runner: 'endpoint' is required in spec",
            "data": {"error": "missing_endpoint", "spec_keys": list(spec.keys())},
            "details": (
                "The spec must include an 'endpoint' key with the inference URL.\n"
                "Example: endpoint: http://localhost:11434/api/generate"
            ),
        }

    model = spec.get("model", "")
    provider = spec.get("provider", "ollama")

    try:
        client = _build_client(spec)
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"benchmark runner: failed to build HTTP client — {exc}",
            "data": {"error": str(exc)},
            "details": f"Could not initialise httpx.Client: {exc}",
        }

    try:
        # Dispatch to the first test type found in spec
        if "latency_test" in spec and isinstance(spec["latency_test"], dict):
            result = _run_latency_test(client, spec, spec["latency_test"])

        elif "accuracy_test" in spec and isinstance(spec["accuracy_test"], dict):
            result = _run_accuracy_test(client, spec, spec["accuracy_test"])

        elif "throughput_test" in spec and isinstance(spec["throughput_test"], dict):
            result = _run_throughput_test(client, spec, spec["throughput_test"])

        else:
            result = {
                "verdict": "INCONCLUSIVE",
                "summary": "benchmark runner: no test type found in spec",
                "data": {
                    "error": "missing_test_type",
                    "spec_keys": list(spec.keys()),
                    "expected_one_of": [
                        "latency_test",
                        "accuracy_test",
                        "throughput_test",
                    ],
                },
                "details": (
                    "The spec must include exactly one of: latency_test, accuracy_test, "
                    "throughput_test.\nSpec keys found: " + str(list(spec.keys()))
                ),
            }
    except Exception as exc:
        result = {
            "verdict": "INCONCLUSIVE",
            "summary": f"benchmark runner: unexpected error — {exc}",
            "data": {"error": str(exc), "endpoint": endpoint, "model": model},
            "details": (
                f"An unexpected error occurred during benchmark execution:\n{exc}\n\n"
                f"Endpoint: {endpoint}\nProvider: {provider}\nModel: {model}"
            ),
        }
    finally:
        client.close()

    # Attach context to data for downstream analysis
    result.setdefault("data", {})
    result["data"].setdefault("endpoint", endpoint)
    result["data"].setdefault("provider", provider)
    result["data"].setdefault("model", model)

    return result
