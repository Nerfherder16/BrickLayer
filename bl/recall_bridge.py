"""
BrickLayer <-> Recall bridge.
Queries the Recall 1.x API for memories relevant to a campaign,
surfacing prior findings from analogous projects.

Uses stdlib only (urllib) — no httpx/requests dependency.
All network calls are fire-and-forget: timeouts are hard-capped at
RECALL_TIMEOUT seconds and every exception is swallowed so a Recall
outage never blocks a running campaign.
"""

import json
import os
import pathlib
import urllib.request
import urllib.error
from typing import Any

RECALL_HOST = os.environ.get("RECALL_HOST", "http://100.70.195.84:8200")
RECALL_API_KEY = os.environ.get("RECALL_API_KEY", "recall-admin-key-change-me")
RECALL_TIMEOUT = 3  # seconds — never block a campaign

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if RECALL_API_KEY:
        h["X-API-Key"] = RECALL_API_KEY
    return h


def _write_recall_degraded(degraded: bool) -> None:
    """
    Write a sentinel file so Trowel and other callers can detect Recall health
    without making a live query. Written to .mas/ alongside other masonry state.

    degraded=True  → Recall was unreachable on last attempt
    degraded=False → Recall responded successfully
    """
    try:
        sentinel = (
            pathlib.Path(os.environ.get("BL_ROOT", ".")) / ".mas" / "recall_degraded"
        )
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        if degraded:
            sentinel.write_text("1", encoding="utf-8")
        else:
            # Clear sentinel on successful call
            if sentinel.exists():
                sentinel.unlink()
    except Exception:
        pass  # never block on sentinel writes


def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST JSON to Recall. Returns parsed JSON body or None on any error."""
    url = f"{RECALL_HOST}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=RECALL_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            _write_recall_degraded(False)
            return result
    except Exception:
        _write_recall_degraded(True)
        return None


def _extract_memories(raw: Any) -> list[dict]:
    """Normalise whatever shape Recall returns into a flat list of memory dicts."""
    if not raw:
        return []
    # Recall may return {"memories": [...]} or a bare list
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("memories", "results", "data", "items"):
            if isinstance(raw.get(key), list):
                return raw[key]
    return []


def _clean(mem: dict) -> dict:
    """Return only the fields callers care about."""
    return {
        "content": mem.get("content", ""),
        "importance": mem.get("importance", 0.0),
        "tags": mem.get("tags", []),
        "created_at": mem.get("created_at", ""),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search_prior_findings(
    query: str,
    domain: str = "autoresearch",
    limit: int = 5,
) -> list[dict]:
    """
    Query Recall for memories matching `query` in the given domain.
    Returns list of {content, importance, tags, created_at} dicts.
    Returns [] on any error (timeout, unreachable, etc.)
    """
    if not query:
        return []
    raw = _post(
        "/memory/search",
        {"query": query, "domain": domain, "limit": limit},
    )
    return [_clean(m) for m in _extract_memories(raw)]


def get_project_history(
    project_name: str,
    limit: int = 10,
) -> list[dict]:
    """
    Retrieve session summaries and key findings for a specific project.
    Searches Recall with query=project_name, filtered to the autoresearch domain.
    """
    if not project_name:
        return []
    raw = _post(
        "/memory/search",
        {"query": project_name, "domain": "autoresearch", "limit": limit},
    )
    return [_clean(m) for m in _extract_memories(raw)]


def store_finding(
    question_id: str,
    verdict: str,
    summary: str,
    project: str,
    tags: list[str] | None = None,
    domain: str | None = None,
    importance: float = 0.7,
) -> bool:
    """
    Store a BL finding to Recall for cross-project recall.
    Returns True if stored successfully, False otherwise.
    """
    if not summary:
        return False

    effective_domain = domain or f"{project}-bricklayer"
    content = f"[{project}/{question_id}] {verdict}: {summary}"
    all_tags = [
        "bricklayer",
        f"project:{project}",
        f"verdict:{verdict}",
        f"qid:{question_id}",
    ]
    if tags:
        all_tags.extend(tags)

    result = _post(
        "/memory/store",
        {
            "content": content,
            "domain": effective_domain,
            "importance": importance,
            "tags": all_tags,
        },
    )
    # Any non-None response is a success
    return result is not None


def get_analogous_failures(
    system_type: str,
    limit: int = 5,
) -> list[dict]:
    """
    Find failure patterns from other projects that match this system type.
    system_type: e.g. "fastapi", "solana", "react", "docker"
    Searches across all domains for FAILURE verdicts mentioning system_type.
    """
    if not system_type:
        return []
    # Search broadly — omit domain filter to scan all projects
    raw = _post(
        "/memory/search",
        {
            "query": f"FAILURE {system_type}",
            "limit": limit,
        },
    )
    memories = _extract_memories(raw)
    # Filter to entries that actually mention a failure verdict
    failures = [
        m
        for m in memories
        if "FAILURE" in m.get("content", "").upper()
        or any(
            "failure" in str(t).lower() or "verdict:failure" in str(t).lower()
            for t in m.get("tags", [])
        )
    ]
    return [_clean(m) for m in failures]


def get_campaign_context(
    project: str,
    wave: int = 1,
    limit: int = 8,
) -> list[dict]:
    """
    Query Recall for cross-campaign context relevant to this project and wave.

    Surfaces prior findings, known failure modes, and synthesis notes from
    earlier waves or related projects — giving Trowel useful background before
    dispatching the first question of a new wave.

    Returns [] on any error so a Recall outage never blocks a campaign.
    """
    if not project:
        return []

    query = f"campaign context project:{project} wave:{wave} findings synthesis"
    raw = _post(
        "/memory/search",
        {
            "query": query,
            "domain": f"{project}-bricklayer",
            "limit": limit,
            "tags": ["bricklayer", f"project:{project}"],
        },
    )
    memories = _extract_memories(raw)

    # Also search without domain restriction to find cross-project analogues
    if len(memories) < limit // 2:
        cross_raw = _post(
            "/memory/search",
            {
                "query": f"bricklayer synthesis failure {project}",
                "limit": limit - len(memories),
            },
        )
        memories.extend(_extract_memories(cross_raw))

    return [_clean(m) for m in memories]


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Recall host: {RECALL_HOST}")
    print("Searching for: 'benchmark runner failure'")
    results = search_prior_findings("benchmark runner failure")
    if results:
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] importance={r['importance']:.2f}  tags={r['tags']}")
            print(f"    {r['content'][:120]}")
    else:
        print("No results (Recall unreachable or no matching memories).")
