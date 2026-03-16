"""
bl/recall_bridge.py — Optional Recall memory integration.

Stores BrickLayer findings to the Recall system after each question.
Retrieves relevant prior findings before each question.

Gracefully skips all operations if Recall is unreachable.
Recall API: http://192.168.50.19:8200
"""

import os

# Recall is optional — graceful fail if httpx not installed
try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

RECALL_BASE = os.environ.get("RECALL_BASE_URL", "http://192.168.50.19:8200")
RECALL_TIMEOUT = 5.0  # seconds — fail fast if Recall is unreachable


def _is_available() -> bool:
    """Quick health check. Returns False if Recall is unreachable."""
    if not _HTTPX_AVAILABLE:
        return False
    try:
        r = httpx.get(f"{RECALL_BASE}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def store_finding(question: dict, result: dict, project: str = "") -> bool:
    """
    Store a finding to Recall after a question completes.

    Returns True if stored, False if skipped/failed.
    """
    if not _HTTPX_AVAILABLE:
        return False

    qid = question.get("id", "unknown")
    verdict = result.get("verdict", "UNKNOWN")
    summary = result.get("summary", "")
    op_mode = question.get("operational_mode", question.get("mode", "unknown"))
    title = question.get("title", "")

    # Only store significant verdicts
    _STORE_VERDICTS = {
        "FAILURE",
        "WARNING",
        "DIAGNOSIS_COMPLETE",
        "FIXED",
        "FIX_FAILED",
        "PROMISING",
        "BLOCKED",
        "IMMINENT",
        "PROBABLE",
        "IMPROVEMENT",
        "REGRESSION",
        "NON_COMPLIANT",
        "PARTIAL",
        "ALERT",
        "DEGRADED",
    }
    if verdict not in _STORE_VERDICTS:
        return False

    content = f"[{qid}] {title}: {verdict}. {summary}"
    domain = f"{project}-bricklayer" if project else "bricklayer"

    payload = {
        "content": content,
        "domain": domain,
        "tags": [f"bl:mode:{op_mode}", f"bl:verdict:{verdict}", "bricklayer"],
        "importance": 0.8,
        "memory_type": "semantic",
    }

    try:
        r = httpx.post(
            f"{RECALL_BASE}/memories",
            json=payload,
            timeout=RECALL_TIMEOUT,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def search_before_question(question: dict, project: str = "") -> str:
    """
    Search Recall for findings relevant to this question.

    Returns a formatted string of relevant memories, or "" if none / unavailable.
    """
    if not _HTTPX_AVAILABLE:
        return ""

    query = f"{question.get('title', '')} {question.get('hypothesis', '')}".strip()
    if not query:
        return ""

    domain = f"{project}-bricklayer" if project else "bricklayer"
    op_mode = question.get("operational_mode", "")

    params = {
        "q": query,
        "domain": domain,
        "limit": 5,
    }
    if op_mode:
        params["tags"] = f"bl:mode:{op_mode}"

    try:
        r = httpx.get(
            f"{RECALL_BASE}/memories/search",
            params=params,
            timeout=RECALL_TIMEOUT,
        )
        if r.status_code != 200:
            return ""

        memories = r.json()
        if not memories:
            return ""

        lines = ["## Relevant Prior Findings (from Recall)\n"]
        for m in memories[:5]:
            content = m.get("content", "")
            score = m.get("score", 0.0)
            if content:
                lines.append(f"- [{score:.2f}] {content}")

        return "\n".join(lines) + "\n"
    except Exception:
        return ""
