"""
bl/runners/http.py — Simple HTTP request runner (C-07).

Executes one or more HTTP requests specified in the question's Test field
and returns a verdict envelope based on status code, response body, and latency.

Handles questions with mode: http

Test field syntax (parsed from the question):
    GET {url}                         — basic reachability
    POST {url} {json_body}            — POST with JSON body
    expect_status: {code}             — expected HTTP status (default 200)
    expect_body: {substring}          — response body must contain this
    latency_threshold_ms: {N}         — FAILURE if response > N ms
    auth: bearer                      — include AUTH_HEADERS from config
"""

import json
import re
import time

import httpx

from bl.config import auth_headers, cfg

# ---------------------------------------------------------------------------
# Spec parser
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+")
_METHOD_RE = re.compile(r"^\s*(GET|POST|PUT|DELETE|PATCH)\s+", re.IGNORECASE)


def _parse_http_spec(test_field: str) -> dict:
    """Parse the Test field of a question into an HTTP request spec.

    Returns a dict with keys:
        method, url, body, expect_status, expect_body, latency_ms, use_auth
    """
    spec = {
        "method": "GET",
        "url": None,
        "body": None,
        "expect_status": 200,
        "expect_body": None,
        "latency_ms": 2000,
        "use_auth": False,
    }

    lines = test_field.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        low = stripped.lower()

        # Directive lines
        if low.startswith("expect_status:"):
            try:
                spec["expect_status"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        if low.startswith("expect_body:"):
            spec["expect_body"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("latency_threshold_ms:"):
            try:
                spec["latency_ms"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        if low.startswith("auth:") and "bearer" in low:
            spec["use_auth"] = True
            continue

        # Method + URL line
        url_match = _URL_RE.search(stripped)
        if url_match and spec["url"] is None:
            spec["url"] = url_match.group(0).rstrip("/.,;")
            method_match = _METHOD_RE.match(stripped)
            if method_match:
                spec["method"] = method_match.group(1).upper()

            # Body: remainder of line after URL
            remainder = stripped[url_match.end() :].strip()
            if remainder:
                spec["body"] = remainder

    # Fallback URL
    if spec["url"] is None:
        spec["url"] = cfg.base_url.rstrip("/") + "/health"

    return spec


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_http(question: dict) -> dict:
    """Execute HTTP request(s) from Test field and return verdict envelope."""
    test_field = question.get("test", "") or question.get("Test", "")
    spec = _parse_http_spec(test_field)

    method = spec["method"]
    url = spec["url"]
    expect_status = spec["expect_status"]
    latency_threshold = spec["latency_ms"]
    expect_body = spec["expect_body"]

    headers = {"Content-Type": "application/json"}
    if spec["use_auth"]:
        headers.update(auth_headers())

    body = None
    if spec["body"]:
        try:
            body = json.loads(spec["body"])
        except json.JSONDecodeError:
            body = spec["body"]

    # Execute request
    status_code = 0
    response_body = ""
    elapsed_ms = 0

    try:
        start = time.monotonic()
        with httpx.Client(timeout=cfg.request_timeout) as client:
            if method == "GET":
                resp = client.get(url, headers=headers)
            elif method == "POST":
                resp = client.post(
                    url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    content=body.encode() if isinstance(body, str) else None,
                )
            elif method == "PUT":
                resp = client.put(
                    url, headers=headers, json=body if isinstance(body, dict) else None
                )
            elif method == "DELETE":
                resp = client.delete(url, headers=headers)
            else:
                resp = client.get(url, headers=headers)

        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        status_code = resp.status_code
        response_body = resp.text

    except httpx.ConnectError as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"HTTP {method} {url} — connection error: {exc}",
            "data": {"method": method, "url": url, "error": str(exc)},
            "details": f"Connection error reaching {url}: {exc}",
        }
    except httpx.TimeoutException as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"HTTP {method} {url} — timeout after {cfg.request_timeout}s",
            "data": {"method": method, "url": url, "error": "timeout"},
            "details": f"Request timed out after {cfg.request_timeout}s: {exc}",
        }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"HTTP {method} {url} — unexpected error: {exc}",
            "data": {"method": method, "url": url, "error": str(exc)},
            "details": f"Unexpected error: {exc}",
        }

    # Determine verdict
    verdict = "HEALTHY"
    failure_reasons = []

    if status_code != expect_status:
        verdict = "FAILURE"
        failure_reasons.append(f"status {status_code} != expected {expect_status}")

    if elapsed_ms > latency_threshold:
        verdict = "FAILURE"
        failure_reasons.append(
            f"latency {elapsed_ms}ms > threshold {latency_threshold}ms"
        )
    elif verdict == "HEALTHY" and elapsed_ms > latency_threshold * 0.7:
        verdict = "WARNING"
        failure_reasons.append(
            f"latency {elapsed_ms}ms approaching threshold {latency_threshold}ms (>70%)"
        )

    if expect_body is not None and expect_body not in response_body:
        verdict = "FAILURE"
        failure_reasons.append(f"expected body substring '{expect_body}' not found")

    summary = f"HTTP {method} {url} → {status_code} in {elapsed_ms}ms"
    if failure_reasons:
        summary += " | " + "; ".join(failure_reasons)

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "method": method,
            "url": url,
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "latency_threshold_ms": latency_threshold,
            "body_preview": response_body[:200],
        },
        "details": (
            f"Status: {status_code} (expected {expect_status})\n"
            f"Latency: {elapsed_ms}ms (threshold: {latency_threshold}ms)\n"
            f"Body: {response_body[:300]}"
        ),
    }
