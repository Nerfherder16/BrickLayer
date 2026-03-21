"""Layer 2 — Semantic/Embedding routing.

Uses local Ollama embeddings to match requests to agents by description
similarity. Caches agent embeddings to avoid repeated Ollama calls within
a session.

Returns RoutingDecision with confidence=cosine_similarity on a match above
threshold, or None to fall through to Layer 3.
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any

import httpx

from masonry.src.schemas.payloads import AgentRegistryEntry, RoutingDecision

# Module-level cache: corpus_key -> embedding vector
_embedding_cache: dict[str, list[float]] = {}

# Ollama URL is configurable via environment variable
_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.50.62:11434")
_DEFAULT_OLLAMA_URL = _OLLAMA_URL  # kept for backward-compat references
_DEFAULT_MODEL = "qwen3-embedding:0.6b"
_DEFAULT_THRESHOLD = 0.70
_TIMEOUT = 15.0  # longer for batch requests


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Returns 0.0 if either vector is the zero vector.
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_embedding(
    client: Any,
    text: str,
    model: str,
    ollama_url: str,
) -> list[float] | None:
    """Fetch an embedding from Ollama. Returns None on any error."""
    try:
        response = client.post(
            f"{ollama_url}/api/embed",
            json={"model": model, "input": text},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])
        if embeddings:
            return embeddings[0]
        return None
    except (httpx.TimeoutException, httpx.HTTPError, Exception) as exc:
        print(f"[semantic] Ollama error: {exc}", file=sys.stderr)
        return None


def _agent_corpus_key(agent: AgentRegistryEntry) -> str:
    """Build the corpus string for an agent and use it as cache key."""
    return agent.description + " " + ", ".join(agent.capabilities)


def route_semantic(
    request_text: str,
    registry: list[AgentRegistryEntry],
    ollama_url: str = _OLLAMA_URL,
    model: str = _DEFAULT_MODEL,
    threshold: float = _DEFAULT_THRESHOLD,
) -> RoutingDecision | None:
    """Attempt semantic routing via Ollama embeddings.

    Returns RoutingDecision on a high-confidence match, or None to fall through.
    """
    if not registry:
        return None

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            # Batch-fetch all uncached agent embeddings in a single Ollama call
            uncached = [
                a for a in registry
                if _agent_corpus_key(a) not in _embedding_cache
            ]
            if uncached:
                texts = [_agent_corpus_key(a) for a in uncached]
                try:
                    resp = client.post(
                        f"{ollama_url}/api/embed",
                        json={"model": model, "input": texts},
                        timeout=_TIMEOUT,
                    )
                    resp.raise_for_status()
                    batch_embs = resp.json().get("embeddings", [])
                    for agent, emb in zip(uncached, batch_embs):
                        _embedding_cache[_agent_corpus_key(agent)] = emb
                except Exception as exc:
                    print(f"[semantic] Ollama batch error: {exc}", file=sys.stderr)
                    return None

            # Get request embedding (single call)
            request_emb = _get_embedding(client, request_text, model, ollama_url)
            if request_emb is None:
                return None

            # Build agent embedding list from cache
            agent_embs: list[tuple[AgentRegistryEntry, list[float]]] = [
                (a, _embedding_cache[_agent_corpus_key(a)])
                for a in registry
                if _agent_corpus_key(a) in _embedding_cache
            ]

    except Exception as exc:
        print(f"[semantic] Unexpected error: {exc}", file=sys.stderr)
        return None

    if not agent_embs:
        return None

    # Compute similarities
    scored = [
        (agent, _cosine_similarity(request_emb, emb))
        for agent, emb in agent_embs
    ]
    best_agent, best_score = max(scored, key=lambda x: x[1])

    if best_score < threshold:
        return None

    return RoutingDecision(
        target_agent=best_agent.name,
        layer="semantic",
        confidence=best_score,
        reason=f"Semantic match: {best_score:.2f}"[:100],
    )
