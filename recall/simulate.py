"""
simulate.py — Recall stress-test runner.

Reads the current question from questions.md (first PENDING question, or --question arg),
dispatches based on Mode field, runs the test, writes a finding, and updates results.tsv.

Usage:
    python simulate.py                      # run next PENDING question
    python simulate.py --question Q1.1      # run specific question
    python simulate.py --list               # list all questions and statuses

Modes:
    performance  — httpx async load test against http://192.168.50.19:8200
    correctness  — pytest subprocess against C:/Users/trg16/Dev/Recall/tests/
    quality      — read source files and emit for agent analysis

Output: JSON to stdout + finding written to findings/Q{N}.{M}.md + results.tsv updated
"""

import argparse
import asyncio
import io
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    import httpx
except ImportError:
    print(
        json.dumps(
            {
                "question_id": "SETUP",
                "mode": "setup",
                "verdict": "INCONCLUSIVE",
                "summary": "httpx not installed. Run: pip install httpx",
                "data": {},
                "details": "Missing dependency: httpx",
            }
        )
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config (defaults — overridden by init_project when --project is given)
# ---------------------------------------------------------------------------

BASE_URL = "http://192.168.50.19:8200"
API_KEY = "recall-admin-key-change-me"
AUTH_HEADERS: dict = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
REQUEST_TIMEOUT = 10.0  # seconds per request

# API routes
SEARCH_ROUTE = "/search/query"
STORE_ROUTE = "/memory/store"
HEALTH_ROUTE = "/health"
CONSOLIDATE_ROUTE = "/admin/consolidate"

# Paths — reassigned by init_project() when --project is given
RECALL_SRC = Path("C:/Users/trg16/Dev/Recall")
AUTOSEARCH_ROOT = Path(__file__).parent.parent  # autosearch/
PROJECT_ROOT = Path(__file__).parent  # recall/ (legacy default)
FINDINGS_DIR: Path = PROJECT_ROOT / "findings"
RESULTS_TSV: Path = PROJECT_ROOT / "results.tsv"
QUESTIONS_MD: Path = PROJECT_ROOT / "questions.md"
INTROSPECT_LOG: Path = PROJECT_ROOT / "introspect.jsonl"
AGENTS_DIR = AUTOSEARCH_ROOT / "agents"

# mkdir deferred to init_project to support path overrides

# ---------------------------------------------------------------------------
# Project loader
# ---------------------------------------------------------------------------


def init_project(project_name: str | None) -> None:
    """Load project config from project.json and update module-level path constants."""
    global BASE_URL, API_KEY, AUTH_HEADERS, RECALL_SRC
    global FINDINGS_DIR, RESULTS_TSV, QUESTIONS_MD, INTROSPECT_LOG

    if project_name:
        # Search: projects/{name}/ first, then sibling {name}/ (legacy layout)
        candidates = [
            AUTOSEARCH_ROOT / "projects" / project_name,
            AUTOSEARCH_ROOT / project_name,
        ]
        project_dir: Path | None = None
        for candidate in candidates:
            if (candidate / "project.json").exists():
                project_dir = candidate
                break

        if project_dir is None:
            print(f"Error: project '{project_name}' not found.", file=sys.stderr)
            for c in candidates:
                print(f"  Checked: {c / 'project.json'}", file=sys.stderr)
            print("\nRun: python onboard.py  to create a new project.", file=sys.stderr)
            sys.exit(1)

        cfg = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
        RECALL_SRC = Path(cfg["target_git"])
        BASE_URL = cfg.get("target_live_url", BASE_URL)
        API_KEY = cfg.get("api_key", API_KEY)
        AUTH_HEADERS = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        FINDINGS_DIR = project_dir / "findings"
        RESULTS_TSV = project_dir / "results.tsv"
        QUESTIONS_MD = project_dir / "questions.md"
        INTROSPECT_LOG = project_dir / "introspect.jsonl"
    else:
        # Legacy: use the directory simulate.py lives in
        project_dir = Path(__file__).parent
        FINDINGS_DIR = project_dir / "findings"
        RESULTS_TSV = project_dir / "results.tsv"
        QUESTIONS_MD = project_dir / "questions.md"
        INTROSPECT_LOG = project_dir / "introspect.jsonl"

    FINDINGS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Question parsing
# ---------------------------------------------------------------------------


def parse_questions() -> list[dict]:
    """Parse questions.md and return list of question dicts."""
    text = QUESTIONS_MD.read_text(encoding="utf-8")
    questions = []

    # Match question blocks: ## Q{N}.{M} [MODE] Title
    block_pattern = re.compile(
        r"^## (Q\d+\.\d+) \[(\w+)\] (.+?)$",
        re.MULTILINE,
    )
    field_pattern = re.compile(
        r"^\*\*(Mode|Target|Hypothesis|Test|Verdict threshold|Agent|Finding|Source)\*\*:\s*(.+?)(?=\n\*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    # Split into blocks
    matches = list(block_pattern.finditer(text))
    for i, m in enumerate(matches):
        qid = m.group(1)
        mode_raw = m.group(2).lower()
        title = m.group(3).strip()

        # Extract block body (up to next ## Q block or end)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        # Parse fields
        fields = {}
        for fm in field_pattern.finditer(body):
            fields[fm.group(1).lower().replace(" ", "_")] = fm.group(2).strip()

        # Determine status from results.tsv
        status = get_question_status(qid)

        questions.append(
            {
                "id": qid,
                "mode": mode_raw,
                "title": title,
                "status": status,
                "target": fields.get("target", ""),
                "hypothesis": fields.get("hypothesis", ""),
                "test": fields.get("test", ""),
                "verdict_threshold": fields.get("verdict_threshold", ""),
                "agent_name": fields.get("agent", "").strip(),
                "finding": fields.get("finding", "").strip(),
                "source": fields.get("source", "").strip(),
            }
        )

    return questions


def get_question_status(qid: str) -> str:
    """Read current verdict from results.tsv."""
    if not RESULTS_TSV.exists():
        return "PENDING"
    for line in RESULTS_TSV.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if parts and parts[0] == qid:
            verdict = parts[1].strip() if len(parts) > 1 else "PENDING"
            return verdict
    return "PENDING"


def get_next_pending(questions: list[dict]) -> dict | None:
    """Return first PENDING question."""
    for q in questions:
        if q["status"] == "PENDING":
            return q
    return None


def get_question_by_id(questions: list[dict], qid: str) -> dict | None:
    for q in questions:
        if q["id"] == qid:
            return q
    return None


# ---------------------------------------------------------------------------
# Performance mode
# ---------------------------------------------------------------------------

# Payloads for realistic API calls
SEARCH_PAYLOAD = {
    "query": "memory system performance test concurrent load stress",
    "domain": "autoresearch",
    "limit": 10,
}

STORE_PAYLOAD_TEMPLATE = {
    "content": "Autoresearch load test memory entry {i} — stress testing Recall API under concurrent load",
    "domain": "autoresearch",
    "tags": ["autoresearch", "load-test"],
    "importance": 0.5,
}


async def _single_request(
    client: "httpx.AsyncClient",
    method: str,
    path: str,
    payload: dict | None = None,
) -> dict:
    """Fire one request, return timing + status dict."""
    start = time.monotonic()
    try:
        if method == "GET":
            resp = await client.get(path, timeout=REQUEST_TIMEOUT)
        else:
            resp = await client.post(path, json=payload, timeout=REQUEST_TIMEOUT)
        elapsed = time.monotonic() - start
        return {
            "ok": resp.status_code < 500,
            "status": resp.status_code,
            "latency_ms": round(elapsed * 1000, 1),
            "error": None,
        }
    except httpx.TimeoutException:
        elapsed = time.monotonic() - start
        return {
            "ok": False,
            "status": 0,
            "latency_ms": round(elapsed * 1000, 1),
            "error": "timeout",
        }
    except Exception as exc:
        elapsed = time.monotonic() - start
        return {
            "ok": False,
            "status": 0,
            "latency_ms": round(elapsed * 1000, 1),
            "error": str(exc),
        }


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(len(sorted_v) * p / 100)
    idx = min(idx, len(sorted_v) - 1)
    return sorted_v[idx]


async def _run_concurrent_stage(
    concurrent: int,
    duration_s: float,
    method: str,
    path: str,
    payload: dict | None,
) -> dict:
    """Run `concurrent` workers for `duration_s` seconds, return stats."""
    results = []
    deadline = time.monotonic() + duration_s

    async def worker():
        async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
            while time.monotonic() < deadline:
                r = await _single_request(client, method, path, payload)
                results.append(r)

    workers = [asyncio.create_task(worker()) for _ in range(concurrent)]
    await asyncio.gather(*workers, return_exceptions=True)

    latencies = [r["latency_ms"] for r in results if r["ok"]]
    errors = [r for r in results if not r["ok"]]
    total = len(results)

    return {
        "concurrent": concurrent,
        "total_requests": total,
        "errors": len(errors),
        "error_rate_pct": round(len(errors) / total * 100, 1) if total else 0,
        "p50_ms": round(_percentile(latencies, 50), 1),
        "p95_ms": round(_percentile(latencies, 95), 1),
        "p99_ms": round(_percentile(latencies, 99), 1),
        "mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
    }


async def _run_store_rate_stage(
    rate_per_sec: float,
    duration_s: float,
    stage_num: int,
) -> dict:
    """Send stores at a fixed rate for duration_s seconds."""
    results = []
    interval = 1.0 / rate_per_sec
    deadline = time.monotonic() + duration_s

    async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
        i = 0
        while time.monotonic() < deadline:
            payload = dict(STORE_PAYLOAD_TEMPLATE)
            payload["content"] = STORE_PAYLOAD_TEMPLATE["content"].format(
                i=f"{stage_num}-{i}"
            )
            r = await _single_request(client, "POST", STORE_ROUTE, payload)
            results.append(r)
            i += 1
            await asyncio.sleep(max(0, interval - r["latency_ms"] / 1000))

    latencies = [r["latency_ms"] for r in results if r["ok"]]
    errors = [r for r in results if not r["ok"]]
    total = len(results)

    return {
        "rate_per_sec": rate_per_sec,
        "total_requests": total,
        "errors": len(errors),
        "error_rate_pct": round(len(errors) / total * 100, 1) if total else 0,
        "mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "p95_ms": round(_percentile(latencies, 95), 1),
    }


async def run_performance_q1_1() -> dict:
    """Q1.1 — Search latency sweep 5→10→20→40 concurrent users, 30s each."""
    stages = [5, 10, 20, 40]
    stage_results = []
    early_stop = None

    for c in stages:
        stage = await _run_concurrent_stage(
            concurrent=c,
            duration_s=30,
            method="POST",
            path=SEARCH_ROUTE,
            payload=SEARCH_PAYLOAD,
        )
        stage_results.append(stage)
        if stage["p99_ms"] > 2000 or stage["error_rate_pct"] > 5:
            early_stop = c
            break

    # Determine verdict
    verdict = "HEALTHY"
    failure_detail = []
    for s in stage_results:
        if s["p99_ms"] > 2000 or s["error_rate_pct"] > 5:
            verdict = "FAILURE"
            failure_detail.append(
                f"c={s['concurrent']}: p99={s['p99_ms']}ms err={s['error_rate_pct']}%"
            )
        elif s["p99_ms"] > 1000 or s["error_rate_pct"] > 1:
            if verdict == "HEALTHY":
                verdict = "WARNING"
            failure_detail.append(
                f"c={s['concurrent']}: p99={s['p99_ms']}ms err={s['error_rate_pct']}%"
            )

    summary_parts = [f"c={s['concurrent']}: p99={s['p99_ms']}ms" for s in stage_results]
    summary = " | ".join(summary_parts)
    if early_stop:
        summary += f" [stopped early at c={early_stop}]"

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {"stages": stage_results, "early_stop_at": early_stop},
        "details": f"Failure conditions: {failure_detail}"
        if failure_detail
        else "All stages within thresholds",
    }


async def run_performance_q1_2() -> dict:
    """Q1.2 — Store rate ramp 1/s→5/s→10/s→20/s, 20s each."""
    rates = [1.0, 5.0, 10.0, 20.0]
    stage_results = []
    early_stop = None

    for i, rate in enumerate(rates):
        stage = await _run_store_rate_stage(rate, duration_s=20, stage_num=i)
        stage_results.append(stage)
        if stage["mean_ms"] > 5000 or stage["error_rate_pct"] > 10:
            early_stop = rate
            break

    verdict = "HEALTHY"
    failure_detail = []
    for s in stage_results:
        if s["mean_ms"] > 5000 or s["error_rate_pct"] > 10:
            verdict = "FAILURE"
            failure_detail.append(
                f"rate={s['rate_per_sec']}/s: mean={s['mean_ms']}ms err={s['error_rate_pct']}%"
            )
        elif s["mean_ms"] > 2000 or s["error_rate_pct"] > 5:
            if verdict == "HEALTHY":
                verdict = "WARNING"
            failure_detail.append(
                f"rate={s['rate_per_sec']}/s: mean={s['mean_ms']}ms err={s['error_rate_pct']}%"
            )

    summary_parts = [
        f"{s['rate_per_sec']}/s: mean={s['mean_ms']}ms" for s in stage_results
    ]
    summary = " | ".join(summary_parts)

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {"stages": stage_results, "early_stop_at": early_stop},
        "details": f"Failure conditions: {failure_detail}"
        if failure_detail
        else "All rates within thresholds",
    }


async def run_performance_q1_3() -> dict:
    """Q1.3 — /health lead/lag vs search errors under 30 concurrent users, 60s."""
    health_timeline = []
    search_results = []
    start = time.monotonic()
    deadline = start + 60.0

    async def search_worker():
        async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
            while time.monotonic() < deadline:
                r = await _single_request(client, "POST", SEARCH_ROUTE, SEARCH_PAYLOAD)
                r["t"] = round(time.monotonic() - start, 1)
                search_results.append(r)

    async def health_poller():
        async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
            while time.monotonic() < deadline:
                r = await _single_request(client, "GET", HEALTH_ROUTE, None)
                r["t"] = round(time.monotonic() - start, 1)
                health_timeline.append(r)
                await asyncio.sleep(5)

    workers = [asyncio.create_task(search_worker()) for _ in range(30)]
    workers.append(asyncio.create_task(health_poller()))
    await asyncio.gather(*workers, return_exceptions=True)

    # Find first health failure time
    first_health_fail = next(
        (r["t"] for r in health_timeline if not r["ok"] or r["status"] != 200),
        None,
    )

    # Find first time search error rate exceeded 1% in a 5s window
    first_search_error_t = None
    window_size = 5.0
    t_now = 0.0
    while t_now < 60.0:
        window = [r for r in search_results if t_now <= r["t"] < t_now + window_size]
        if window:
            err_rate = sum(1 for r in window if not r["ok"]) / len(window) * 100
            if err_rate > 1.0:
                first_search_error_t = t_now
                break
        t_now += window_size

    # Verdict
    if first_health_fail is None and first_search_error_t is not None:
        verdict = "FAILURE"
        summary = f"Health stayed green while search errors appeared at t={first_search_error_t}s — health is a false negative"
    elif first_health_fail is not None and first_search_error_t is not None:
        lag = first_health_fail - first_search_error_t
        if lag > 30:
            verdict = "WARNING"
            summary = f"Health lagged search errors by {lag:.0f}s (health fail at t={first_health_fail}s, search errors at t={first_search_error_t}s)"
        else:
            verdict = "HEALTHY"
            summary = f"Health degraded at t={first_health_fail}s, search errors at t={first_search_error_t}s (lag={lag:.0f}s)"
    elif first_health_fail is not None and first_search_error_t is None:
        verdict = "HEALTHY"
        summary = f"Health degraded at t={first_health_fail}s before any user-visible search errors"
    else:
        verdict = "HEALTHY"
        summary = "No health failures and no search errors under 30 concurrent users"

    total_search = len(search_results)
    err_search = sum(1 for r in search_results if not r["ok"])

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "health_polls": len(health_timeline),
            "health_failures": sum(1 for r in health_timeline if not r["ok"]),
            "first_health_fail_t": first_health_fail,
            "first_search_error_t": first_search_error_t,
            "total_search_requests": total_search,
            "search_errors": err_search,
            "search_error_rate_pct": round(err_search / total_search * 100, 1)
            if total_search
            else 0,
        },
        "details": f"Health timeline: {health_timeline[:5]}... Search sample: {search_results[:3]}...",
    }


async def run_performance_q1_4() -> dict:
    """Q1.4 — Search latency at 40 concurrent users vs 5 concurrent baseline, 60s."""
    baseline = await _run_concurrent_stage(
        concurrent=5,
        duration_s=30,
        method="POST",
        path=SEARCH_ROUTE,
        payload=SEARCH_PAYLOAD,
    )
    stress = await _run_concurrent_stage(
        concurrent=40,
        duration_s=60,
        method="POST",
        path=SEARCH_ROUTE,
        payload=SEARCH_PAYLOAD,
    )

    verdict = "HEALTHY"
    if stress["p99_ms"] > 3000:
        verdict = "FAILURE"
    elif stress["p99_ms"] > 1500:
        verdict = "WARNING"

    summary = (
        f"5 users: p99={baseline['p99_ms']}ms | "
        f"40 users: p99={stress['p99_ms']}ms err={stress['error_rate_pct']}%"
    )

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {"baseline_5": baseline, "stress_40": stress},
        "details": f"Baseline p99={baseline['p99_ms']}ms vs stress p99={stress['p99_ms']}ms",
    }


async def run_performance_q1_5() -> dict:
    """Q1.5 — Concurrent /ops/consolidate calls: N=1,2,5,10."""
    levels = [1, 2, 5, 10]
    stage_results = []

    async def fire_consolidate_n(n: int) -> dict:
        async def one(client):
            return await _single_request(client, "POST", CONSOLIDATE_ROUTE, {})

        async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
            tasks = [asyncio.create_task(one(client)) for _ in range(n)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        real = [r for r in results if isinstance(r, dict)]
        statuses = [r["status"] for r in real]
        errors = [r for r in real if not r["ok"]]
        timeouts = [r for r in real if r.get("error") == "timeout"]

        return {
            "n": n,
            "statuses": statuses,
            "errors": len(errors),
            "timeouts": len(timeouts),
            "status_200": statuses.count(200),
            "status_409": statuses.count(409),
            "status_429": statuses.count(429),
            "status_5xx": sum(1 for s in statuses if s >= 500),
        }

    for n in levels:
        stage = await fire_consolidate_n(n)
        stage_results.append(stage)

    # Verdict
    verdict = "HEALTHY"
    issues = []
    for s in stage_results:
        if s["status_5xx"] > 0 and s["n"] >= 2:
            verdict = "FAILURE"
            issues.append(f"n={s['n']}: {s['status_5xx']} 500 errors")
        elif s["timeouts"] > 0 and s["n"] >= 5:
            verdict = "FAILURE"
            issues.append(f"n={s['n']}: {s['timeouts']} timeouts")

    summary_parts = [
        f"n={s['n']}: 200={s['status_200']} 409={s['status_409']} 5xx={s['status_5xx']}"
        for s in stage_results
    ]
    summary = " | ".join(summary_parts)

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {"stages": stage_results},
        "details": f"Issues: {issues}" if issues else "No critical errors observed",
    }


PERFORMANCE_RUNNERS = {
    "Q1.1": run_performance_q1_1,
    "Q1.2": run_performance_q1_2,
    "Q1.3": run_performance_q1_3,
    "Q1.4": run_performance_q1_4,
    "Q1.5": run_performance_q1_5,
}


async def run_performance(question: dict) -> dict:
    qid = question["id"]
    runner = PERFORMANCE_RUNNERS.get(qid)
    if runner is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"No performance runner implemented for {qid}",
            "data": {},
            "details": "Add a runner to PERFORMANCE_RUNNERS dict",
        }

    # Check API is reachable first
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, headers=AUTH_HEADERS) as client:
            resp = await client.get(HEALTH_ROUTE, timeout=5.0)
        if resp.status_code >= 500:
            return {
                "verdict": "INCONCLUSIVE",
                "summary": f"API returned {resp.status_code} on /health — system may be down",
                "data": {"health_status": resp.status_code},
                "details": resp.text[:500],
            }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"API unreachable at {BASE_URL}: {exc}",
            "data": {},
            "details": str(exc),
        }

    try:
        result = await runner()
        return result
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Runner failed: {exc}",
            "data": {},
            "details": str(exc),
        }


# ---------------------------------------------------------------------------
# Correctness mode
# ---------------------------------------------------------------------------


def run_correctness(question: dict) -> dict:
    """Run pytest for correctness questions. Parse output for verdict."""
    test_spec = question.get("test", "")

    # Extract pytest command from the Test field
    # Look for `pytest ...` patterns
    pytest_matches = re.findall(r"pytest\s+(C:[^\s`]+(?:\s+C:[^\s`]+)*)", test_spec)

    if not pytest_matches:
        # Try to find paths and build a command
        path_matches = re.findall(r"C:/Users/trg16/Dev/Recall/[^\s`\n]+", test_spec)
        if path_matches:
            paths = " ".join(path_matches)
            pytest_cmd = f"pytest {paths} -v --tb=short -q"
        else:
            return {
                "verdict": "INCONCLUSIVE",
                "summary": "Could not extract pytest path from question Test field",
                "data": {},
                "details": f"Test field: {test_spec}",
            }
    else:
        paths = pytest_matches[0]
        # Check for -k filter in the test spec
        k_match = re.search(r'-k\s+"([^"]+)"', test_spec)
        k_filter = f' -k "{k_match.group(1)}"' if k_match else ""
        pytest_cmd = f"pytest {paths} -v --tb=short -q{k_filter}"

    # On Windows, use python -m pytest to ensure correct interpreter
    cmd = f"python -m {pytest_cmd}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(RECALL_SRC),
        )
        stdout = result.stdout
        stderr = result.stderr
        combined = stdout + ("\n" + stderr if stderr else "")

        # Parse pytest summary line: "X passed", "X failed", "X error"
        passed = 0
        failed = 0
        errors = 0

        passed_m = re.search(r"(\d+) passed", combined)
        failed_m = re.search(r"(\d+) failed", combined)
        error_m = re.search(r"(\d+) error", combined)
        if passed_m:
            passed = int(passed_m.group(1))
        if failed_m:
            failed = int(failed_m.group(1))
        if error_m:
            errors = int(error_m.group(1))

        # Detect "no tests ran" or "file not found"
        no_tests = (
            "no tests ran" in combined.lower()
            or "collected 0 items" in combined
            or "ERROR" in combined
            and "not found" in combined.lower()
        )

        if no_tests and passed == 0 and failed == 0:
            # Retry once with corrected path check
            alt_paths = _find_test_paths(question)
            if alt_paths and alt_paths != paths:
                retry_cmd = f"python -m pytest {alt_paths} -v --tb=short -q"
                retry_result = subprocess.run(
                    retry_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(RECALL_SRC),
                )
                retry_out = retry_result.stdout + retry_result.stderr
                passed_m = re.search(r"(\d+) passed", retry_out)
                failed_m = re.search(r"(\d+) failed", retry_out)
                if passed_m:
                    passed = int(passed_m.group(1))
                if failed_m:
                    failed = int(failed_m.group(1))
                combined = f"[RETRY with {alt_paths}]\n" + retry_out
                no_tests = passed == 0 and failed == 0

        if no_tests:
            verdict = "INCONCLUSIVE"
            summary = "No tests found for paths in question. Check test paths."
        elif failed > 0 or errors > 0:
            verdict = "FAILURE"
            summary = f"{passed} passed, {failed} failed, {errors} errors"
        else:
            verdict = "HEALTHY"
            summary = f"{passed} passed, {failed} failed"

        return {
            "verdict": verdict,
            "summary": summary,
            "data": {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "returncode": result.returncode,
            },
            "details": combined[:4000],
        }

    except subprocess.TimeoutExpired:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "pytest timed out after 300s",
            "data": {},
            "details": "Subprocess timeout",
        }
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"pytest subprocess error: {exc}",
            "data": {},
            "details": str(exc),
        }


def _find_test_paths(question: dict) -> str | None:
    """Try to find the test file path by scanning the Recall test directories."""
    test_dirs = [
        RECALL_SRC / "tests" / "integration",
        RECALL_SRC / "tests" / "core",
        RECALL_SRC / "tests" / "ml",
    ]
    # Extract filenames from Test field
    filenames = re.findall(r"test_\w+\.py", question.get("test", ""))
    found = []
    for fname in filenames:
        for d in test_dirs:
            candidate = d / fname
            if candidate.exists():
                found.append(str(candidate))
    return " ".join(found) if found else None


# ---------------------------------------------------------------------------
# Agent mode
# ---------------------------------------------------------------------------


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- ... ---) from a markdown file."""
    if not text.startswith("---"):
        return text
    try:
        end = text.index("---", 3)
        return text[end + 3 :].strip()
    except ValueError:
        return text


def _run_scout_for_project() -> None:
    """Invoke the Scout agent to regenerate questions.md."""
    import os as _os
    import shutil as _shutil

    scout_path = AGENTS_DIR / "scout.md"
    if not scout_path.exists():
        print(json.dumps({"error": "scout.md not found in agents/"}))
        return

    raw = scout_path.read_text(encoding="utf-8")
    body = _strip_frontmatter(raw)

    # Load project config
    cfg_path = FINDINGS_DIR.parent / "project.json"
    cfg = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    docs_dir = FINDINGS_DIR.parent / "docs"
    docs_content = ""
    if docs_dir.exists():
        for doc in sorted(docs_dir.iterdir()):
            if doc.is_file():
                try:
                    docs_content += f"\n\n### {doc.name}\n{doc.read_text(encoding='utf-8', errors='ignore')[:3000]}"
                except Exception:
                    pass

    prompt = f"""{body}

---

## Your Assignment

**Project**: {cfg.get("display_name", "Unknown")}
**Target git**: {RECALL_SRC}
**Stack**: {", ".join(cfg.get("stack", [])) or "unknown"}
**Live service**: {cfg.get("target_live_url", "none")}
**Docs folder**: {docs_dir}
{f"**Supporting docs content**:{docs_content}" if docs_content else "**Docs folder**: empty — scan the codebase only"}

Scan the target codebase now and output the complete questions.md content."""

    claude_bin = _shutil.which("claude") or "claude"
    child_env = {k: v for k, v in _os.environ.items() if k != "CLAUDECODE"}

    print("Running Scout — scanning codebase to generate questions...", flush=True)
    try:
        proc = subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"error": str(e)}))
        return

    output = proc.stdout.strip()
    idx = output.find("# BrickLayer Campaign Questions")
    if idx == -1:
        print(json.dumps({"error": "Scout output not recognized", "raw": output[:500]}))
        return

    questions_md = output[idx:]
    QUESTIONS_MD.write_text(questions_md, encoding="utf-8")
    count = questions_md.count("## Q")
    print(
        json.dumps(
            {"status": "ok", "questions_written": count, "path": str(QUESTIONS_MD)}
        )
    )


def _verdict_from_agent_output(agent_name: str, output: dict) -> str:
    """Map agent JSON output contract to a BrickLayer verdict."""
    if not output:
        return "INCONCLUSIVE"

    if agent_name == "security-hardener":
        # HEALTHY: fixed risks (committed or clearly reported as fixed + tests pass)
        if output.get("risks_fixed", 0) > 0 or output.get("changes_committed", 0) > 0:
            return "HEALTHY"
        if output.get("risks_reported", 0) > 0:
            return "WARNING"

    elif agent_name == "test-writer":
        before = output.get("coverage_before", 0.0)
        after = output.get("coverage_after", 0.0)
        written = output.get("tests_written", 0)
        if written > 0 and after > before:
            return "HEALTHY"
        if written > 0:
            return "WARNING"

    elif agent_name == "type-strictener":
        before = output.get("errors_before", 0)
        after = output.get("errors_after", 0)
        committed = output.get("changes_committed", 0)
        if committed > 0 and after < before:
            return "HEALTHY"
        if committed > 0:
            return "WARNING"
        # Agent may have diagnosed a non-mypy finding and self-reported HEALTHY
        if output.get("mitigation_required") is False:
            return "HEALTHY"
        # Agent found issues but reported them all as architectural debt (can't fix)
        if output.get("architectural_debt") and not committed:
            return "WARNING"

    elif agent_name == "perf-optimizer":
        pct = output.get("improvement_pct", 0.0)
        committed = output.get("changes_committed", 0)
        if committed > 0 and pct >= 20:
            return "HEALTHY"
        if committed > 0 and pct >= 5:
            return "WARNING"

    else:
        # Generic: any committed change is progress
        if output.get("changes_committed", 0) > 0:
            return "HEALTHY"

    # Last resort: trust the agent's own verdict field if present
    self_verdict = output.get("verdict", "").upper()
    if self_verdict in ("HEALTHY", "WARNING", "FAILURE", "INCONCLUSIVE"):
        return self_verdict

    return "INCONCLUSIVE"


def _parse_text_output(agent_name: str, text: str) -> dict:
    """
    Fallback parser when the agent produces plain text instead of a JSON block.
    Extracts key metrics using regex patterns matched to each agent type.
    """
    out: dict = {}

    # Detect commits — "commit `abc1234`" or "committed abc1234"
    commit_matches = re.findall(
        r"commit[ted]*\s+[`']?([0-9a-f]{7,})[`']?", text, re.IGNORECASE
    )
    if commit_matches:
        out["changes_committed"] = len(commit_matches)

    if agent_name == "security-hardener":
        # Match both "3 risks fixed" and "18 silent exception swallows fixed"
        for pattern in [
            r"(\d+)\s+risks?\s+fixed",
            r"(\d+)\s+\w[\w\s]+\s+fixed",  # "N <anything> fixed"
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m and not out.get("risks_fixed"):
                out["risks_fixed"] = int(m.group(1))
        m = re.search(r"(\d+)\s+risks?\s+(?:found|identified)", text, re.IGNORECASE)
        if m:
            out["risks_found"] = int(m.group(1))
        m = re.search(
            r"(\d+)\s+(?:new\s+)?(?:security\s+)?tests?\s+written", text, re.IGNORECASE
        )
        if m:
            out["tests_written"] = int(m.group(1))
        m = re.search(r"(\d+)\s+risks?\s+reported", text, re.IGNORECASE)
        if m:
            out["risks_reported"] = int(m.group(1))

    elif agent_name == "test-writer":
        m = re.search(r"(\d+)\s+tests?\s+written", text, re.IGNORECASE)
        if m:
            out["tests_written"] = int(m.group(1))
        m = re.search(
            r"coverage[:\s]+(\d+(?:\.\d+)?)%\s*[→\-]+\s*(\d+(?:\.\d+)?)%", text
        )
        if m:
            out["coverage_before"] = float(m.group(1)) / 100
            out["coverage_after"] = float(m.group(2)) / 100

    elif agent_name == "type-strictener":
        m = re.search(r"(\d+)\s+errors?\s+[→\-]+\s*(\d+)", text)
        if m:
            out["errors_before"] = int(m.group(1))
            out["errors_after"] = int(m.group(2))

    elif agent_name == "perf-optimizer":
        m = re.search(r"p99[:\s]+(\d+(?:\.\d+)?)ms\s*[→\-]+\s*(\d+(?:\.\d+)?)ms", text)
        if m:
            out["p99_before"] = float(m.group(1))
            out["p99_after"] = float(m.group(2))
            if out["p99_before"] > 0:
                out["improvement_pct"] = round(
                    (out["p99_before"] - out["p99_after"]) / out["p99_before"] * 100, 1
                )

    return out


def _summary_from_agent_output(agent_name: str, output: dict) -> str:
    """Build a concise summary from agent output contract."""
    if not output:
        return f"{agent_name}: no structured output produced"

    if agent_name == "security-hardener":
        return (
            f"risks_found={output.get('risks_found', '?')} "
            f"fixed={output.get('risks_fixed', '?')} "
            f"committed={output.get('changes_committed', '?')} "
            f"tests_written={output.get('tests_written', '?')}"
        )
    if agent_name == "test-writer":
        before = output.get("coverage_before", 0.0)
        after = output.get("coverage_after", 0.0)
        return (
            f"coverage {before * 100:.0f}% → {after * 100:.0f}% "
            f"({output.get('tests_written', '?')} tests written)"
        )
    if agent_name == "type-strictener":
        return (
            f"mypy errors {output.get('errors_before', '?')} → "
            f"{output.get('errors_after', '?')} "
            f"({output.get('changes_committed', '?')} changes committed)"
        )
    if agent_name == "perf-optimizer":
        return (
            f"p99 {output.get('p99_before', '?')}ms → {output.get('p99_after', '?')}ms "
            f"({output.get('improvement_pct', 0.0):.1f}% improvement)"
        )
    return f"{agent_name}: {json.dumps(output)[:200]}"


def run_agent(question: dict) -> dict:
    """
    Invoke a specialist agent against a BrickLayer finding via Claude CLI.

    The agent's system prompt is read from agents/{agent_name}.md.
    The finding context is injected from findings/{finding_id}.md.
    The agent runs non-interactively via `claude -p` and its JSON output
    contract is parsed from the response to produce the verdict envelope.
    """
    agent_name = question.get("agent_name", "").strip()
    finding_id = question.get("finding", "").strip()
    source_file = question.get("source", "").strip()

    if not agent_name:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "No agent specified — add **Agent**: <name> to question",
            "data": {},
            "details": f"Available: {[f.stem for f in AGENTS_DIR.glob('*.md') if f.stem != 'SCHEMA']}",
        }

    agent_path = AGENTS_DIR / f"{agent_name}.md"
    if not agent_path.exists():
        available = [f.stem for f in AGENTS_DIR.glob("*.md") if f.stem != "SCHEMA"]
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Agent file not found: {agent_name}.md",
            "data": {"available_agents": available},
            "details": f"Expected at: {agent_path}",
        }

    # Read agent prompt, strip YAML frontmatter
    agent_prompt = _strip_frontmatter(agent_path.read_text(encoding="utf-8"))

    # Load finding context
    finding_context = "(no finding specified)"
    if finding_id:
        finding_path = FINDINGS_DIR / f"{finding_id}.md"
        if finding_path.exists():
            finding_context = finding_path.read_text(encoding="utf-8", errors="replace")
        else:
            finding_context = (
                f"(Finding {finding_id} not found — run that question first)"
            )

    source_line = (
        f"\n**Source file**: `{RECALL_SRC / source_file}`" if source_file else ""
    )

    full_prompt = f"""{agent_prompt}

---

## Your Assignment

**Project root**: `{RECALL_SRC}`{source_line}
**Test directory**: `{RECALL_SRC / "tests"}`

**Finding to address**:

{finding_context}

Begin your agent loop now. Output your JSON result contract in a ```json ... ``` block when complete."""

    # Resolve claude CLI — npm shims on Windows need full path
    import os  # noqa: PLC0415
    import shutil  # noqa: PLC0415

    claude_bin = shutil.which("claude") or "claude"

    # Strip CLAUDECODE env var — Claude Code refuses to launch nested sessions
    child_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        # Pass prompt via stdin (-p -) to avoid Windows CMD 8191-char limit
        proc = subprocess.run(
            [
                claude_bin,
                "-p",
                "-",
                "--output-format",
                "json",
                "--allowedTools",
                "Read,Write,Edit,Bash,Glob,Grep",
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
            cwd=str(RECALL_SRC),
            env=child_env,
        )
        raw = proc.stdout

        # Unwrap --output-format json envelope if present
        agent_text = raw
        try:
            wrapper = json.loads(raw)
            if isinstance(wrapper, dict):
                agent_text = wrapper.get("result", raw)
        except json.JSONDecodeError:
            pass

        # Extract agent JSON output contract from fenced code block
        agent_output: dict = {}
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", agent_text, re.DOTALL)
        if json_match:
            try:
                agent_output = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: parse metrics from plain text when agent skips JSON block
        if not agent_output and agent_text:
            agent_output = _parse_text_output(agent_name, agent_text)

        verdict = _verdict_from_agent_output(agent_name, agent_output)
        summary = _summary_from_agent_output(agent_name, agent_output)

        return {
            "verdict": verdict,
            "summary": summary,
            "data": agent_output,
            "details": agent_text[:4000],
        }

    except subprocess.TimeoutExpired:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"{agent_name} timed out after 600s",
            "data": {},
            "details": "Agent loop exceeded time limit — check for infinite loops or missing iteration bounds",
        }
    except FileNotFoundError:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "claude CLI not found — ensure Claude Code is installed and on PATH",
            "data": {},
            "details": "Install: https://claude.ai/download",
        }


# ---------------------------------------------------------------------------
# Quality mode
# ---------------------------------------------------------------------------


def run_quality(question: dict) -> dict:
    """Read source files specified in the Target field and emit contents."""
    target = question.get("target", "")

    # Extract file paths from target
    # Patterns: "src/core/retrieval.py", "src/api/routes/", "src/core/embeddings.py + tests/core/test_embeddings_cache.py"
    src_files = []

    # Split on ' + ' to handle multi-path targets like "src/core/ + src/workers/"
    target_segments = [s.strip() for s in target.split("+")]

    for segment in target_segments:
        segment = segment.strip()

        # Named .py file: src/core/retrieval.py or tests/core/test_foo.py
        file_matches = re.findall(r"(?:src|tests)/[\w/]+\.py", segment)
        for fpath in file_matches:
            full = RECALL_SRC / fpath
            src_files.append(full)

        # Bare directory: src/, src/core/, src/workers/, tests/
        dir_matches = re.findall(r"(?:src|tests)(?:/[\w/]*)?/?(?=\s|$)", segment)
        for dpath in dir_matches:
            if file_matches:
                continue  # already handled as specific file
            dpath = dpath.strip().rstrip("/")
            full_dir = RECALL_SRC / dpath
            if full_dir.is_dir():
                src_files.extend(sorted(full_dir.rglob("*.py")))

    # Handle legacy "src/api/routes/ (all .py files)" pattern
    if "src/api/routes/" in target and not src_files:
        routes_dir = RECALL_SRC / "src" / "api" / "routes"
        if routes_dir.exists():
            src_files.extend(sorted(routes_dir.glob("*.py")))

    # Deduplicate preserving order
    seen = set()
    unique_files = []
    for f in src_files:
        if str(f) not in seen:
            seen.add(str(f))
            unique_files.append(f)

    if not unique_files:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"No source files found from target: {target}",
            "data": {"target": target},
            "details": "Check target field in questions.md — paths must match actual Recall source layout",
        }

    output_parts = []
    missing = []
    total_lines = 0

    for fpath in unique_files:
        if not fpath.exists():
            missing.append(str(fpath))
            output_parts.append(f"\n=== MISSING: {fpath} ===\n")
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            lines = content.splitlines()
            total_lines += len(lines)
            output_parts.append(f"\n=== {fpath} ({len(lines)} lines) ===\n{content}\n")
        except Exception as exc:
            output_parts.append(f"\n=== ERROR reading {fpath}: {exc} ===\n")

    full_output = "".join(output_parts)

    # Pattern-based verdict — applied when we can derive a verdict from code analysis
    verdict, summary = _analyze_quality_patterns(
        question, unique_files, full_output, missing, total_lines
    )

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {
            "files_read": [str(f) for f in unique_files if f.exists()],
            "files_missing": missing,
            "total_lines": total_lines,
        },
        "details": full_output,
    }


def _analyze_quality_patterns(
    question: dict, files: list, content: str, missing: list, total_lines: int
) -> tuple[str, str]:
    """
    Apply pattern-based analysis to quality question file content.
    Returns (verdict, summary). Falls back to INCONCLUSIVE when no pattern matches.
    """
    hypothesis = question.get("hypothesis", "").lower()

    # --- Logger mismatch detection ---
    # Triggered by: "structlog" + "stdlib" or "logging.getlogger" in hypothesis
    if "structlog" in hypothesis and (
        "stdlib" in hypothesis
        or "logging.getlogger" in hypothesis
        or "mismatch" in hypothesis
    ):
        failures = []
        warnings = []
        for fpath in files:
            if not fpath.exists():
                continue
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            has_stdlib = bool(re.search(r"^import logging\b", src, re.MULTILINE))
            has_structlog = bool(re.search(r"import structlog", src))
            # Look for stdlib logger called with kwargs: logger.warning("x", key=val)
            stdlib_kwarg_calls = re.findall(
                r"(?:logging\.\w+|logger\.\w+)\([^)]*,\s*\w+=",
                src,
            )
            # Check if logger var is stdlib (getLogger) or structlog (get_logger)
            uses_stdlib_logger = bool(re.search(r"logging\.getLogger\(\)", src))
            if has_stdlib and has_structlog:
                if stdlib_kwarg_calls and uses_stdlib_logger:
                    failures.append(
                        f"{fpath.name}: stdlib logger called with kwargs — TypeError in except blocks"
                    )
                else:
                    warnings.append(
                        f"{fpath.name}: mixed imports (stdlib + structlog) but no kwarg-passing found"
                    )
        if failures:
            return "FAILURE", f"Logger mismatch: {'; '.join(failures)}"
        if warnings:
            return "WARNING", f"Mixed logger imports: {'; '.join(warnings)}"
        return (
            "HEALTHY",
            f"Checked {len(files)} files — all consistently use structlog; no stdlib/structlog mixing detected",
        )

    # --- Unguarded mutable module-level state ---
    if "mutable" in hypothesis and ("lock" in hypothesis or "async" in hypothesis):
        failures = []
        warnings = []
        for fpath in files:
            if not fpath.exists():
                continue
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # Find module-level dict/list assignments
            module_dicts = re.findall(
                r"^(\w+)\s*(?::\s*\S+)?\s*=\s*(?:\{\}|\[\]|dict\(\)|list\(\))",
                src,
                re.MULTILINE,
            )
            # Check each for nearby asyncio.Lock
            for var in module_dicts:
                lock_nearby = bool(
                    re.search(rf"{var}_lock|_{var}_lock|asyncio\.Lock", src)
                )
                # Check if it's written from an async def
                written_in_async = bool(
                    re.search(rf"async def[^{{]+\n(?:.*\n){{0,30}}.*{var}\s*[=\[]", src)
                )
                if written_in_async and not lock_nearby:
                    failures.append(
                        f"{fpath.name}: `{var}` written from async path without asyncio.Lock"
                    )
                elif not lock_nearby and module_dicts:
                    warnings.append(f"{fpath.name}: `{var}` has no apparent lock guard")
        if failures:
            return (
                "FAILURE",
                f"Unguarded async-written state: {'; '.join(failures[:3])}",
            )
        if warnings:
            return (
                "WARNING",
                f"Potentially unguarded module-level state: {'; '.join(warnings[:3])}",
            )
        return (
            "HEALTHY",
            f"Checked {len(files)} files — no unguarded async-written module-level state detected",
        )

    # --- datetime.utcnow() deprecation ---
    if "utcnow" in hypothesis:
        hits = re.findall(r"datetime\.utcnow\(\)", content)
        file_hits = [
            str(f.name)
            for f in files
            if f.exists()
            and "datetime.utcnow()" in f.read_text(encoding="utf-8", errors="replace")
        ]
        if hits:
            return (
                "FAILURE",
                f"Found {len(hits)} datetime.utcnow() calls in {len(file_hits)} files: {', '.join(file_hits[:5])}",
            )
        return "HEALTHY", f"No datetime.utcnow() calls found in {len(files)} files"

    # --- N+1 query pattern detection ---
    if "n+1" in hypothesis or "loop" in hypothesis and "db" in hypothesis:
        loop_db_pattern = re.findall(
            r"for\s+\w+\s+in\s+\w+[^:]+:\s*\n(?:.*\n){0,5}.*(?:session\.|qdrant\.|redis\.)",
            content,
        )
        if loop_db_pattern:
            return (
                "FAILURE",
                f"Potential N+1 pattern: DB call inside result loop ({len(loop_db_pattern)} instances)",
            )
        return "HEALTHY", "No N+1 DB-inside-loop patterns detected"

    # --- Fallback ---
    if missing:
        return (
            "INCONCLUSIVE",
            f"Read {len(files) - len(missing)}/{len(files)} files ({total_lines} lines). Missing: {', '.join(missing)}",
        )
    return (
        "INCONCLUSIVE",
        f"Read {len(files)} source files ({total_lines} lines) — requires agent analysis for verdict",
    )


# ---------------------------------------------------------------------------
# Finding writer
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Failure taxonomy
# ---------------------------------------------------------------------------

# Failure type taxonomy: syntax | logic | hallucination | tool_failure | timeout | unknown
_FAILURE_TYPES = frozenset(
    ("syntax", "logic", "hallucination", "tool_failure", "timeout", "unknown")
)


def classify_failure_type(result: dict, mode: str) -> str | None:
    """
    Classify why a question failed. Returns one of:
      syntax | logic | hallucination | tool_failure | timeout | unknown
    Returns None when verdict is HEALTHY or WARNING — no failure to classify.
    """
    verdict = result.get("verdict", "")
    if verdict in ("HEALTHY", "WARNING"):
        return None

    details = (result.get("details", "") or "").lower()
    summary = (result.get("summary", "") or "").lower()
    combined = details + " " + summary

    # Timeout — most specific, check first
    if any(
        s in combined
        for s in (
            "timeout",
            "timed out",
            "readtimeout",
            "connecttimeout",
            "time limit exceeded",
        )
    ):
        return "timeout"

    # Tool failure — infrastructure/runner errors, not logic errors
    if any(
        s in combined
        for s in (
            "connection refused",
            "connection error",
            "importerror",
            "modulenotfounderror",
            "no module named",
            "oserror",
            "permissionerror",
            "filenotfounderror",
            "subprocess failed",
            "process exited",
            "exit code",
            "returncode",
            "could not connect",
            "httpstatuserror",
            "network error",
        )
    ):
        return "tool_failure"

    # Syntax errors
    if any(
        s in combined
        for s in (
            "syntaxerror",
            "indentationerror",
            "parse error",
            "syntax error",
            "invalid syntax",
        )
    ):
        return "syntax"

    # Correctness mode failures are logic by default (assertion failures, test failures)
    if mode == "correctness":
        return "logic"

    # Performance mode: metric didn't meet threshold → logic
    if mode == "performance":
        return "logic"

    # Agent/quality/static mode with no concrete evidence → hallucination
    if mode in ("agent", "quality", "static"):
        if any(
            s in combined
            for s in (
                "no evidence",
                "cannot verify",
                "no concrete",
                "assumed",
                "unclear",
                "speculative",
                "no data",
                "not found in",
                "could not find evidence",
            )
        ):
            return "hallucination"

    return "unknown"


# ---------------------------------------------------------------------------
# Confidence signaling
# ---------------------------------------------------------------------------

# Confidence levels: high | medium | low | uncertain
# Routing actions the orchestrator uses to decide next step
CONFIDENCE_ROUTING: dict[str, str] = {
    "high": "accept",  # proceed directly — evidence is solid
    "medium": "validate",  # log a note, proceed with caution
    "low": "escalate",  # flag for human review before acting on verdict
    "uncertain": "re-run",  # re-run or try a different approach
}


def classify_confidence(result: dict, mode: str) -> str:
    """
    Estimate how much trust to place in this verdict.
    Returns: high | medium | low | uncertain
    """
    verdict = result.get("verdict", "")
    data = result.get("data", {}) or {}
    details = (result.get("details", "") or "").lower()

    # INCONCLUSIVE always uncertain — we don't know what happened
    if verdict == "INCONCLUSIVE":
        return "uncertain"

    # --- Performance mode ---
    if mode == "performance":
        stages = data.get("stages", [])
        if not stages:
            return "uncertain"
        early_stop = data.get("early_stop_at")
        if early_stop:
            return "low"  # stopped early, incomplete picture
        return "high" if len(stages) >= 3 else "medium"

    # --- Correctness mode ---
    if mode == "correctness":
        passed = data.get("passed", 0) or 0
        failed = data.get("failed", 0) or 0
        total = passed + failed
        if total == 0:
            return "uncertain"
        if total >= 10:
            return "high"
        if total >= 3:
            return "medium"
        return "low"

    # --- Agent / quality / static mode ---
    if mode in ("agent", "quality", "static"):
        # Signals of concrete evidence in the details or data
        concrete_signals = (
            "line ",
            "line:",
            ".py:",
            ".rs:",
            ".ts:",
            ".kt:",
            "function ",
            "def ",
            "file:",
            "/src/",
            "test_",
            "error:",
            "warning:",
            "assert",
            "found ",
        )
        evidence_count = sum(1 for s in concrete_signals if s in details)
        if evidence_count >= 4:
            return "high"
        if evidence_count >= 2:
            return "medium"
        if evidence_count >= 1:
            return "low"
        # Check if data dict has real content
        if data and data != {}:
            return "medium"
        return "uncertain"

    # --- Generic fallback by verdict ---
    if verdict == "FAILURE":
        return "high" if details.strip() else "low"
    if verdict == "WARNING":
        return "medium"
    if verdict == "HEALTHY":
        return "high" if details.strip() else "medium"

    return "uncertain"


# ---------------------------------------------------------------------------
# Introspection decorator
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Eval / scoring harness
# ---------------------------------------------------------------------------

# Score = evidence_quality * 0.4 + verdict_clarity * 0.4 + execution_success * 0.2
# Range: 0.0 (useless) → 1.0 (perfect)
# Written to results.tsv and included in introspect trace.

_VERDICT_CLARITY: dict[str, float] = {
    "HEALTHY": 1.0,
    "FAILURE": 1.0,
    "WARNING": 0.7,
    "INCONCLUSIVE": 0.0,
}

_CONFIDENCE_EVIDENCE: dict[str, float] = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.3,
    "uncertain": 0.0,
}

_FAILURE_EXECUTION: dict[str, float] = {
    # These failure types mean the question ran and produced signal
    None: 1.0,
    "logic": 0.9,
    "syntax": 0.8,
    "hallucination": 0.4,
    "unknown": 0.5,
    "timeout": 0.3,
    "tool_failure": 0.0,
}


def score_result(result: dict) -> float:
    """
    Score a verdict envelope on a 0.0-1.0 scale.
    evidence_quality * 0.4 + verdict_clarity * 0.4 + execution_success * 0.2
    """
    verdict = result.get("verdict", "INCONCLUSIVE")
    confidence = result.get("confidence", "uncertain")
    failure_type = result.get("failure_type")

    evidence_quality = _CONFIDENCE_EVIDENCE.get(confidence, 0.0)
    verdict_clarity = _VERDICT_CLARITY.get(verdict, 0.0)
    execution_success = _FAILURE_EXECUTION.get(failure_type, 0.5)

    score = (
        (evidence_quality * 0.4) + (verdict_clarity * 0.4) + (execution_success * 0.2)
    )
    return round(score, 3)


import functools  # noqa: E402 — placed here so linter sees usage alongside _write_introspect_trace


def _write_introspect_trace(trace: dict) -> None:
    """
    Append a structured trace record to introspect.jsonl.
    Fire-and-forget POST to Recall if BASE_URL is configured.
    Never raises — introspection must not break the campaign.
    """
    line = json.dumps(trace, ensure_ascii=False)
    try:
        with INTROSPECT_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        print(f"[introspect] local write failed: {exc}", file=sys.stderr)

    # Fire-and-forget POST to Recall — skip if BASE_URL is unset or "none"
    if not BASE_URL or BASE_URL.lower() in ("none", ""):
        return
    try:
        import httpx as _httpx  # noqa: PLC0415

        payload = {
            "content": (
                f"BrickLayer trace: {trace.get('agent', '?')} | "
                f"{trace.get('tool_call', '?')} | "
                f"verdict={trace.get('tool_result', '?')} | "
                f"confidence={trace.get('confidence', '?')} | "
                f"latency={trace.get('latency_ms', '?')}ms"
            ),
            "domain": "bricklayer",
            "tags": [
                "trace",
                f"phase:{trace.get('phase', 'campaign')}",
                f"agent:{trace.get('agent', 'unknown')}",
                f"tool:{trace.get('tool_call', 'unknown')}",
                f"confidence:{trace.get('confidence', 'uncertain')}",
                f"error_type:{trace.get('error_type', 'none')}",
            ],
            "importance": 0.6,
        }
        _httpx.post(
            f"{BASE_URL}{STORE_ROUTE}",
            json=payload,
            headers=AUTH_HEADERS,
            timeout=2.0,
        )
    except Exception:
        pass  # Recall unavailable — local log is the source of truth


def introspect_step(fn):
    """
    Decorator that captures timing and writes a structured trace for every
    question run. Apply to _run_and_record.
    """

    @functools.wraps(fn)
    def wrapper(question: dict) -> dict:
        start = time.monotonic()
        result = fn(question)
        latency_ms = int((time.monotonic() - start) * 1000)

        trace = {
            "agent": question.get("agent_name") or "bricklayer",
            "phase": "campaign",
            "thought": question.get("hypothesis") or question.get("title", ""),
            "tool_call": question.get("mode", "unknown"),
            "tool_result": f"{result.get('verdict', '?')}: {result.get('summary', '')[:120]}",
            "tokens_used": None,  # not available from subprocess runners
            "latency_ms": latency_ms,
            "confidence": result.get("confidence", "uncertain"),
            "error_type": result.get("failure_type"),
            "question_id": result.get("question_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _write_introspect_trace(trace)
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Finding writer
# ---------------------------------------------------------------------------


def write_finding(question: dict, result: dict) -> Path:
    """Write findings/{qid}.md in BrickLayer finding format."""
    qid = question["id"]
    finding_path = FINDINGS_DIR / f"{qid}.md"

    verdict = result["verdict"]
    severity_map = {
        "FAILURE": "High",
        "WARNING": "Medium",
        "HEALTHY": "Info",
        "INCONCLUSIVE": "Low",
    }
    severity = severity_map.get(verdict, "Low")

    failure_type = result.get("failure_type")
    confidence = result.get("confidence", "uncertain")
    failure_type_line = f"\n**Failure Type**: {failure_type}" if failure_type else ""
    routing_action = CONFIDENCE_ROUTING.get(confidence, "re-run")

    content = f"""# Finding: {qid} — {question["title"]}

**Question**: {question["hypothesis"]}
**Verdict**: {verdict}
**Severity**: {severity}{failure_type_line}
**Confidence**: {confidence} → {routing_action}
**Mode**: {question["mode"]}
**Target**: {question["target"]}

## Summary

{result["summary"]}

## Evidence

{result["details"][:3000]}

## Raw Data

```json
{json.dumps(result["data"], indent=2)[:2000]}
```

## Verdict Threshold

{question["verdict_threshold"]}

## Mitigation Recommendation

[To be filled by agent analysis]

## Open Follow-up Questions

[Add follow-up questions here if verdict is FAILURE or WARNING]
"""

    finding_path.write_text(content, encoding="utf-8")
    return finding_path


def update_results_tsv(
    qid: str,
    verdict: str,
    summary: str,
    failure_type: str | None = None,
    confidence: str | None = None,
    score: float | None = None,
) -> None:
    """Update results.tsv with the verdict for this question."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not RESULTS_TSV.exists():
        RESULTS_TSV.write_text(
            "question_id\tverdict\tfailure_type\tconfidence\tscore\tsummary\ttimestamp\n",
            encoding="utf-8",
        )

    lines = RESULTS_TSV.read_text(encoding="utf-8", errors="replace").splitlines()
    updated = False
    new_lines = []
    ft = failure_type or ""
    conf = confidence or "uncertain"
    sc = f"{score:.3f}" if score is not None else ""

    for line in lines:
        parts = line.split("\t")
        if parts and parts[0] == qid:
            safe_summary = summary.replace("\t", " ")[:120]
            new_lines.append(
                f"{qid}\t{verdict}\t{ft}\t{conf}\t{sc}\t{safe_summary}\t{timestamp}"
            )
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        safe_summary = summary.replace("\t", " ")[:120]
        new_lines.append(
            f"{qid}\t{verdict}\t{ft}\t{conf}\t{sc}\t{safe_summary}\t{timestamp}"
        )

    RESULTS_TSV.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def run_question(question: dict) -> dict:
    """Dispatch to correct mode runner."""
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


@introspect_step
def _run_and_record(question: dict) -> dict:
    """Run a single question, write finding, update results.tsv, print JSON."""
    print(
        f"Running {question['id']} [{question['mode']}]: {question['title']}",
        file=sys.stderr,
    )
    result = run_question(question)
    result["failure_type"] = classify_failure_type(result, question["mode"])
    result["confidence"] = classify_confidence(result, question["mode"])
    result["score"] = score_result(result)
    finding_path = write_finding(question, result)
    update_results_tsv(
        question["id"],
        result["verdict"],
        result["summary"],
        result["failure_type"],
        result["confidence"],
        result["score"],
    )
    print(json.dumps(result, indent=2))
    print(f"\nFinding written to: {finding_path}", file=sys.stderr)
    print(f"Verdict: {result['verdict']}", file=sys.stderr)
    routing = CONFIDENCE_ROUTING.get(result["confidence"], "re-run")
    print(f"Confidence: {result['confidence']} → {routing}", file=sys.stderr)
    print(f"Score: {result['score']:.3f}", file=sys.stderr)
    if result["failure_type"]:
        print(f"Failure type: {result['failure_type']}", file=sys.stderr)
    return result


def _print_handoff_reminder() -> None:
    """Print end-of-run cross-project handoff check."""
    handoffs_dir = AUTOSEARCH_ROOT / "handoffs"
    print("\n" + "=" * 60, file=sys.stderr)
    print("END-OF-RUN HANDOFF CHECK", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("Did this campaign find changes needed in another project?", file=sys.stderr)
    print(
        "  YES → Create autosearch/handoffs/handoff-{project}-{date}.md",
        file=sys.stderr,
    )
    print("  NO  → Session complete.", file=sys.stderr)
    existing = (
        sorted(handoffs_dir.glob("handoff-*.md")) if handoffs_dir.exists() else []
    )
    if existing:
        print(f"\nOpen handoffs ({len(existing)}):", file=sys.stderr)
        for h in existing:
            print(f"  {h.name}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


def _run_retrospective() -> None:
    """Run the retrospective agent to improve BrickLayer from session learnings."""
    import os as _os
    import shutil as _shutil

    retro_path = AGENTS_DIR / "retrospective.md"
    if not retro_path.exists():
        print("retrospective.md not found in agents/")
        return

    # Read agent prompt, strip frontmatter
    raw = retro_path.read_text(encoding="utf-8")
    body = _strip_frontmatter(raw)

    # Read results.tsv
    results_content = "(no results yet)"
    if RESULTS_TSV.exists():
        results_content = RESULTS_TSV.read_text(encoding="utf-8")

    # Load project config
    cfg_path = FINDINGS_DIR.parent / "project.json"
    cfg = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    project_display = cfg.get("display_name", "Unknown")

    # Print reflection questions and collect answers
    questions = [
        "1. Verdict accuracy: Which verdicts were INCONCLUSIVE, wrong, or needed manual correction? Why?",
        "2. Agent output: Did any agent report DONE without a green test run? What broke?",
        "3. Question quality: Any vacuous results (0 assertions)? Questions too narrow or too broad?",
        "4. Coverage gaps: Any failure modes found with no agent to fix them?",
        "5. Parallelization: Which questions had no dependencies and could have run simultaneously?",
        "6. Fix quality: Any committed fix later found speculative or wrong?",
        "7. Highest-value finding this session?",
        "8. Biggest time sink with least value?",
    ]

    print("\n" + "=" * 60)
    print(f"BrickLayer Retrospective — {project_display}")
    print("=" * 60)
    print("Answer each question. Press Enter twice to move to the next.\n")

    answers = []
    for q in questions:
        print(f"\n{q}")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        answers.append("\n".join(lines).strip())

    reflection_text = "\n\n".join(
        f"**{questions[i]}**\n{answers[i]}" for i in range(len(questions))
    )

    # Build prompt
    import datetime as _datetime

    prompt = f"""{body}

---

## Your Assignment

**Project**: {project_display}
**Autosearch root**: {AUTOSEARCH_ROOT}
**Session date**: {_datetime.datetime.now().strftime("%Y-%m-%d")}

**Results TSV**:
{results_content}

**User Reflection**:
{reflection_text}

Review the session artifacts and reflection answers. Apply concrete improvements to BrickLayer. Commit to the autosearch repo if git is available. Output your Retrospective Report when done."""

    claude_bin = _shutil.which("claude") or "claude"
    child_env = {k: v for k, v in _os.environ.items() if k != "CLAUDECODE"}

    print("\n" + "=" * 60)
    print("Running Retrospective agent...")
    print("=" * 60 + "\n")

    try:
        subprocess.run(
            [claude_bin, "-p", "-", "--dangerously-skip-permissions"],
            input=prompt,
            capture_output=False,  # stream output live to terminal
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=600,
        )
    except FileNotFoundError:
        print("claude CLI not found — cannot run retrospective agent.")
    except subprocess.TimeoutExpired:
        print("Retrospective agent timed out after 10 minutes.")


def main():
    parser = argparse.ArgumentParser(description="BrickLayer autoresearch runner")
    parser.add_argument("--project", "-p", help="Project name (e.g. recall, adbp)")
    parser.add_argument("--question", "-q", help="Question ID to run (e.g. Q1.1)")
    parser.add_argument(
        "--campaign",
        "-c",
        action="store_true",
        help="Run all PENDING questions in sequence",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all questions")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse questions only, don't run"
    )
    parser.add_argument(
        "--scout",
        "-s",
        action="store_true",
        help="Run Scout to regenerate questions.md for the project",
    )
    parser.add_argument(
        "--retro",
        "-r",
        action="store_true",
        help="Run end-of-session retrospective to improve BrickLayer",
    )
    args = parser.parse_args()

    init_project(args.project)

    _DEFAULT_KEY = "recall-admin-key-change-me"
    if BASE_URL not in ("none", "None", "") and API_KEY == _DEFAULT_KEY:
        print(
            "Warning: using default API key — set api_key in project.json before targeting a live service.",
            file=sys.stderr,
        )

    if args.scout:
        _run_scout_for_project()
        return

    if args.retro:
        _run_retrospective()
        return

    questions = parse_questions()

    if args.list:
        print(f"{'ID':<8} {'STATUS':<15} {'MODE':<15} {'TITLE'}")
        print("-" * 80)
        for q in questions:
            print(f"{q['id']:<8} {q['status']:<15} {q['mode']:<15} {q['title']}")
        return

    if args.campaign:
        pending = [q for q in questions if q["status"] == "PENDING"]
        if not pending:
            print("No PENDING questions remain.", file=sys.stderr)
            _print_handoff_reminder()
            return
        print(f"\nCampaign: {len(pending)} PENDING questions to run", file=sys.stderr)
        for i, question in enumerate(pending, 1):
            print(
                f"\n[{i}/{len(pending)}] {question['id']} — {question['title']}",
                file=sys.stderr,
            )
            _run_and_record(question)
        print("\nCampaign complete.", file=sys.stderr)
        _print_handoff_reminder()
        return

    if args.question:
        question = get_question_by_id(questions, args.question)
        if not question:
            print(
                json.dumps(
                    {
                        "error": f"Question {args.question} not found",
                        "available": [q["id"] for q in questions],
                    }
                )
            )
            sys.exit(1)
    else:
        question = get_next_pending(questions)
        if not question:
            print(
                json.dumps(
                    {
                        "verdict": "INCONCLUSIVE",
                        "summary": "No PENDING questions remain",
                        "data": {},
                        "details": "All questions answered. Generate new ones with forge.",
                    }
                )
            )
            return

    if args.dry_run:
        print(json.dumps(question, indent=2))
        return

    _run_and_record(question)
    _print_handoff_reminder()


if __name__ == "__main__":
    main()
