"""
bl/runners/performance.py — Async HTTP load-test runner.

Runs structured latency/concurrency sweeps against a live API target
and returns a BrickLayer verdict envelope.
"""

import asyncio
import time

import httpx

from bl.config import (
    CONSOLIDATE_ROUTE,
    HEALTH_ROUTE,
    SEARCH_ROUTE,
    STORE_ROUTE,
    auth_headers,
    cfg,
)

# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


async def _single_request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    payload: dict | None = None,
) -> dict:
    start = time.monotonic()
    try:
        if method == "GET":
            resp = await client.get(path, timeout=cfg.request_timeout)
        else:
            resp = await client.post(path, json=payload, timeout=cfg.request_timeout)
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
    idx = min(int(len(sorted_v) * p / 100), len(sorted_v) - 1)
    return sorted_v[idx]


async def _run_concurrent_stage(
    concurrent: int,
    duration_s: float,
    method: str,
    path: str,
    payload: dict | None,
) -> dict:
    results = []
    deadline = time.monotonic() + duration_s

    async def worker():
        async with httpx.AsyncClient(
            base_url=cfg.base_url, headers=auth_headers()
        ) as client:
            while time.monotonic() < deadline:
                results.append(await _single_request(client, method, path, payload))

    await asyncio.gather(
        *[asyncio.create_task(worker()) for _ in range(concurrent)],
        return_exceptions=True,
    )

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
    rate_per_sec: float, duration_s: float, stage_num: int
) -> dict:
    results = []
    interval = 1.0 / rate_per_sec
    deadline = time.monotonic() + duration_s

    async with httpx.AsyncClient(
        base_url=cfg.base_url, headers=auth_headers()
    ) as client:
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


# ---------------------------------------------------------------------------
# Question runners
# ---------------------------------------------------------------------------


async def run_performance_q1_1() -> dict:
    """Q1.1 — Search latency sweep 5→10→20→40 concurrent users, 30s each."""
    stages = [5, 10, 20, 40]
    stage_results = []
    early_stop = None

    for c in stages:
        stage = await _run_concurrent_stage(c, 30, "POST", SEARCH_ROUTE, SEARCH_PAYLOAD)
        stage_results.append(stage)
        if stage["p99_ms"] > 2000 or stage["error_rate_pct"] > 5:
            early_stop = c
            break

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

    summary = " | ".join(
        f"c={s['concurrent']}: p99={s['p99_ms']}ms" for s in stage_results
    )
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
        stage = await _run_store_rate_stage(rate, 20, i)
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

    summary = " | ".join(
        f"{s['rate_per_sec']}/s: mean={s['mean_ms']}ms" for s in stage_results
    )

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
        async with httpx.AsyncClient(
            base_url=cfg.base_url, headers=auth_headers()
        ) as client:
            while time.monotonic() < deadline:
                r = await _single_request(client, "POST", SEARCH_ROUTE, SEARCH_PAYLOAD)
                r["t"] = round(time.monotonic() - start, 1)
                search_results.append(r)

    async def health_poller():
        async with httpx.AsyncClient(
            base_url=cfg.base_url, headers=auth_headers()
        ) as client:
            while time.monotonic() < deadline:
                r = await _single_request(client, "GET", HEALTH_ROUTE, None)
                r["t"] = round(time.monotonic() - start, 1)
                health_timeline.append(r)
                await asyncio.sleep(5)

    workers = [asyncio.create_task(search_worker()) for _ in range(30)]
    workers.append(asyncio.create_task(health_poller()))
    await asyncio.gather(*workers, return_exceptions=True)

    first_health_fail = next(
        (r["t"] for r in health_timeline if not r["ok"] or r["status"] != 200), None
    )
    first_search_error_t = None
    t_now = 0.0
    while t_now < 60.0:
        window = [r for r in search_results if t_now <= r["t"] < t_now + 5.0]
        if window and sum(1 for r in window if not r["ok"]) / len(window) * 100 > 1.0:
            first_search_error_t = t_now
            break
        t_now += 5.0

    if first_health_fail is None and first_search_error_t is not None:
        verdict = "FAILURE"
        summary = f"Health stayed green while search errors appeared at t={first_search_error_t}s — health is a false negative"
    elif first_health_fail is not None and first_search_error_t is not None:
        lag = first_health_fail - first_search_error_t
        verdict = "WARNING" if lag > 30 else "HEALTHY"
        summary = f"Health lagged search errors by {lag:.0f}s (health fail at t={first_health_fail}s, search errors at t={first_search_error_t}s)"
    elif first_health_fail is not None:
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
    baseline = await _run_concurrent_stage(5, 30, "POST", SEARCH_ROUTE, SEARCH_PAYLOAD)
    stress = await _run_concurrent_stage(40, 60, "POST", SEARCH_ROUTE, SEARCH_PAYLOAD)

    verdict = "HEALTHY"
    if stress["p99_ms"] > 3000:
        verdict = "FAILURE"
    elif stress["p99_ms"] > 1500:
        verdict = "WARNING"

    return {
        "verdict": verdict,
        "summary": f"5 users: p99={baseline['p99_ms']}ms | 40 users: p99={stress['p99_ms']}ms err={stress['error_rate_pct']}%",
        "data": {"baseline_5": baseline, "stress_40": stress},
        "details": f"Baseline p99={baseline['p99_ms']}ms vs stress p99={stress['p99_ms']}ms",
    }


async def run_performance_q1_5() -> dict:
    """Q1.5 — Concurrent /ops/consolidate calls: N=1,2,5,10."""
    levels = [1, 2, 5, 10]
    stage_results = []

    async def fire_consolidate_n(n: int) -> dict:
        async with httpx.AsyncClient(
            base_url=cfg.base_url, headers=auth_headers()
        ) as client:
            tasks = [
                asyncio.create_task(
                    _single_request(client, "POST", CONSOLIDATE_ROUTE, {})
                )
                for _ in range(n)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        real = [r for r in results if isinstance(r, dict)]
        statuses = [r["status"] for r in real]
        return {
            "n": n,
            "statuses": statuses,
            "errors": sum(1 for r in real if not r["ok"]),
            "timeouts": sum(1 for r in real if r.get("error") == "timeout"),
            "status_200": statuses.count(200),
            "status_409": statuses.count(409),
            "status_429": statuses.count(429),
            "status_5xx": sum(1 for s in statuses if s >= 500),
        }

    for n in levels:
        stage_results.append(await fire_consolidate_n(n))

    verdict = "HEALTHY"
    issues = []
    for s in stage_results:
        if s["status_5xx"] > 0 and s["n"] >= 2:
            verdict = "FAILURE"
            issues.append(f"n={s['n']}: {s['status_5xx']} 500 errors")
        elif s["timeouts"] > 0 and s["n"] >= 5:
            verdict = "FAILURE"
            issues.append(f"n={s['n']}: {s['timeouts']} timeouts")

    summary = " | ".join(
        f"n={s['n']}: 200={s['status_200']} 409={s['status_409']} 5xx={s['status_5xx']}"
        for s in stage_results
    )

    return {
        "verdict": verdict,
        "summary": summary,
        "data": {"stages": stage_results},
        "details": f"Issues: {issues}" if issues else "No critical errors observed",
    }


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_RUNNERS = {
    "Q1.1": run_performance_q1_1,
    "Q1.2": run_performance_q1_2,
    "Q1.3": run_performance_q1_3,
    "Q1.4": run_performance_q1_4,
    "Q1.5": run_performance_q1_5,
}


async def run_performance(question: dict) -> dict:
    qid = question["id"]
    runner = _RUNNERS.get(qid)
    if runner is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"No performance runner implemented for {qid}",
            "data": {},
            "details": "Add a runner to _RUNNERS dict in bl/runners/performance.py",
        }

    try:
        async with httpx.AsyncClient(
            base_url=cfg.base_url, headers=auth_headers()
        ) as client:
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
            "summary": f"API unreachable at {cfg.base_url}: {exc}",
            "data": {},
            "details": str(exc),
        }

    try:
        return await runner()
    except Exception as exc:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Runner failed: {exc}",
            "data": {},
            "details": str(exc),
        }
