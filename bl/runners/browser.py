"""
bl/runners/browser.py — Headless browser runner using Playwright (C-08).

Executes browser-based UI checks specified in the question's Test field and
returns a verdict envelope based on page content, element presence, and load time.

Handles questions with mode: browser

Test field syntax (parsed from the question):
    url: {url}                      — required: page to load
    action: navigate                — just load and check (default)
    action: click {selector}        — click an element then check
    action: fill {selector} {value} — fill a form field
    action: screenshot              — take a screenshot, always HEALTHY
    expect_title: {substring}       — page title must contain this
    expect_text: {substring}        — page body text must contain this
    expect_element: {css_selector}  — element must exist in DOM
    expect_not_text: {substring}    — page body must NOT contain this
    latency_threshold_ms: {N}       — FAILURE if page load > N ms (default 5000)
    timeout: {N}                    — browser timeout in seconds (default 15)
    screenshot: true                — capture screenshot to .autopilot/browser-output/
    headless: true                  — headless mode (default true)
"""

import re
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

from bl.config import cfg

# ---------------------------------------------------------------------------
# Spec parser
# ---------------------------------------------------------------------------

_URL_SLUG_RE = re.compile(r"[^\w]+")


def _parse_browser_spec(test_field: str) -> dict:
    """Parse the Test field of a question into a browser test spec.

    Returns a dict with keys:
        url, action, action_selector, action_value,
        expect_title, expect_text, expect_not_text, expect_element,
        latency_threshold_ms, timeout, screenshot, headless
    """
    spec = {
        "url": None,
        "action": "navigate",
        "action_selector": None,
        "action_value": None,
        "expect_title": None,
        "expect_text": None,
        "expect_not_text": None,
        "expect_element": None,
        "latency_threshold_ms": 5000,
        "timeout": 15,
        "screenshot": False,
        "headless": True,
    }

    lines = test_field.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        low = stripped.lower()

        if low.startswith("url:"):
            spec["url"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("action:"):
            action_str = stripped.split(":", 1)[1].strip()
            parts = action_str.split(None, 2)
            if parts:
                spec["action"] = parts[0].lower()
                if len(parts) >= 2:
                    spec["action_selector"] = parts[1]
                if len(parts) >= 3:
                    spec["action_value"] = parts[2]
            continue

        if low.startswith("expect_title:"):
            spec["expect_title"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("expect_text:"):
            spec["expect_text"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("expect_not_text:"):
            spec["expect_not_text"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("expect_element:"):
            spec["expect_element"] = stripped.split(":", 1)[1].strip()
            continue

        if low.startswith("latency_threshold_ms:"):
            try:
                spec["latency_threshold_ms"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        if low.startswith("timeout:"):
            try:
                spec["timeout"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue

        if low.startswith("screenshot:"):
            val = stripped.split(":", 1)[1].strip().lower()
            spec["screenshot"] = val in ("true", "yes", "1")
            continue

        if low.startswith("headless:"):
            val = stripped.split(":", 1)[1].strip().lower()
            spec["headless"] = val not in ("false", "no", "0")
            continue

    return spec


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_browser(question: dict) -> dict:
    """Execute browser checks from Test field and return verdict envelope."""
    if not _PLAYWRIGHT_AVAILABLE:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "Playwright not installed — browser runner unavailable",
            "data": {"error": "playwright_not_installed"},
            "details": (
                "playwright is not installed. Install it with:\n"
                "  pip install playwright && playwright install chromium"
            ),
        }

    test_field = question.get("test", "") or question.get("Test", "")
    spec = _parse_browser_spec(test_field)

    url = spec["url"]
    if not url:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "browser runner: no url: directive found in Test field",
            "data": {"error": "missing_url"},
            "details": "Test field must include a 'url: http://...' line.",
        }

    action = spec["action"]
    latency_threshold = spec["latency_threshold_ms"]
    timeout_ms = spec["timeout"] * 1000

    checks_passed = []
    checks_failed = []
    screenshot_path = None
    status_code = None
    page_title = ""
    load_ms = 0

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=spec["headless"])
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(timeout_ms)

            # Navigate and measure load time
            start = time.monotonic()
            response = page.goto(url, wait_until="load", timeout=timeout_ms)
            load_ms = round((time.monotonic() - start) * 1000, 1)

            if response is not None:
                status_code = response.status

            page_title = page.title()

            # Execute action (after navigation)
            if action == "click" and spec["action_selector"]:
                page.click(spec["action_selector"])
            elif (
                action == "fill"
                and spec["action_selector"]
                and spec["action_value"] is not None
            ):
                page.fill(spec["action_selector"], spec["action_value"])
            elif action == "screenshot":
                # screenshot-only action: always HEALTHY, skip other checks
                if spec["screenshot"] or action == "screenshot":
                    screenshot_path = _save_screenshot(page, url)
                browser.close()
                return {
                    "verdict": "HEALTHY",
                    "summary": f"Browser screenshot: {url} — captured",
                    "data": {
                        "url": url,
                        "status": status_code,
                        "load_ms": load_ms,
                        "title": page_title,
                        "checks_passed": [],
                        "checks_failed": [],
                        "screenshot_path": screenshot_path,
                    },
                    "details": f"Screenshot-only action. Screenshot: {screenshot_path}",
                }

            # Run expect checks
            body_text = page.inner_text("body") if page.query_selector("body") else ""

            if spec["expect_title"] is not None:
                if spec["expect_title"] in page_title:
                    checks_passed.append(
                        f"expect_title: '{spec['expect_title']}' found in title"
                    )
                else:
                    checks_failed.append(
                        f"expect_title: '{spec['expect_title']}' not found in title '{page_title}'"
                    )

            if spec["expect_text"] is not None:
                if spec["expect_text"] in body_text:
                    checks_passed.append(f"expect_text: '{spec['expect_text']}' found")
                else:
                    checks_failed.append(
                        f"expect_text: '{spec['expect_text']}' not found in page body"
                    )

            if spec["expect_not_text"] is not None:
                if spec["expect_not_text"] not in body_text:
                    checks_passed.append(
                        f"expect_not_text: '{spec['expect_not_text']}' absent (correct)"
                    )
                else:
                    checks_failed.append(
                        f"expect_not_text: '{spec['expect_not_text']}' found but should be absent"
                    )

            if spec["expect_element"] is not None:
                element = page.query_selector(spec["expect_element"])
                if element is not None:
                    checks_passed.append(
                        f"expect_element: '{spec['expect_element']}' found in DOM"
                    )
                else:
                    checks_failed.append(
                        f"expect_element: '{spec['expect_element']}' not found in DOM"
                    )

            # Screenshot capture
            if spec["screenshot"]:
                screenshot_path = _save_screenshot(page, url)

            browser.close()

    except Exception as exc:
        error_msg = str(exc)
        # Distinguish network/timeout errors from other failures
        low_err = error_msg.lower()
        if "timeout" in low_err or "timed out" in low_err:
            verdict_str = "INCONCLUSIVE"
            summary = f"Browser {url} — timeout after {spec['timeout']}s"
        elif (
            "net::" in low_err
            or "connection refused" in low_err
            or "name not resolved" in low_err
            or "failed to fetch" in low_err
        ):
            verdict_str = "INCONCLUSIVE"
            summary = f"Browser {url} — network error: {error_msg}"
        else:
            verdict_str = "INCONCLUSIVE"
            summary = f"Browser {url} — browser error: {error_msg}"

        return {
            "verdict": verdict_str,
            "summary": summary,
            "data": {"url": url, "error": error_msg},
            "details": f"Browser launch or navigation error:\n{error_msg}",
        }

    # Determine verdict
    verdict = "HEALTHY"
    failure_reasons = []

    if checks_failed:
        verdict = "FAILURE"
        failure_reasons.extend(checks_failed)

    if load_ms > latency_threshold:
        verdict = "FAILURE"
        failure_reasons.append(f"latency {load_ms}ms > threshold {latency_threshold}ms")
    elif verdict == "HEALTHY" and load_ms > latency_threshold * 0.7:
        verdict = "WARNING"
        failure_reasons.append(
            f"latency {load_ms}ms approaching threshold {latency_threshold}ms (>70%)"
        )

    summary = f"Browser {url} → {status_code} in {load_ms}ms"
    if failure_reasons:
        summary += " | " + "; ".join(failure_reasons)

    detail_lines = [
        f"URL: {url}",
        f"Status: {status_code}",
        f"Load time: {load_ms}ms (threshold: {latency_threshold}ms)",
        f"Title: {page_title}",
        f"Checks passed ({len(checks_passed)}): {', '.join(checks_passed) or 'none'}",
        f"Checks failed ({len(checks_failed)}): {', '.join(checks_failed) or 'none'}",
    ]
    if screenshot_path:
        detail_lines.append(f"Screenshot: {screenshot_path}")

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "url": url,
            "status": status_code,
            "load_ms": load_ms,
            "title": page_title,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "screenshot_path": screenshot_path,
        },
        "details": "\n".join(detail_lines),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_screenshot(page, url: str) -> str:
    """Save a screenshot of the page to .autopilot/browser-output/ and return the path."""
    output_dir = Path(cfg.project_root) / ".autopilot" / "browser-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    url_slug = _URL_SLUG_RE.sub("_", url)[:60].strip("_")
    filename = f"{timestamp}_{url_slug}.png"
    screenshot_path = str(output_dir / filename)

    page.screenshot(path=screenshot_path, full_page=True)
    return screenshot_path
