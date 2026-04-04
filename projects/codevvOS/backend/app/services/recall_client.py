"""Recall memory system client for artifact persistence."""

from __future__ import annotations

import logging
import os

import httpx

RECALL_BASE_URL = os.getenv("RECALL_BASE_URL", "http://100.70.195.84:8200")


async def persist_artifact(
    artifact_id: str,
    title: str,
    jsx: str,
    compiled: str | None,
) -> str:
    """Store artifact to Recall. Returns the memory ID. Raises httpx.HTTPError on failure."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RECALL_BASE_URL}/memory/store",
            json={
                "content": jsx,
                "domain": "codevv",
                "source": "codevv-artifact",
                "memory_type": "semantic",
                "tags": ["artifact", f"artifact_id:{artifact_id}", title[:50]],
                "metadata": {
                    "type": "artifact",
                    "artifact_id": artifact_id,
                    "title": title,
                    "compiled": compiled,
                },
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["id"]


async def get_artifact_history() -> list[dict]:
    """Fetch artifact memories from Recall via search, sorted by timestamp desc. Returns [] on error."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RECALL_BASE_URL}/search/browse",
                json={"query": "artifact", "domain_hint": "codevv", "limit": 50},
                timeout=5.0,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("results", data) if isinstance(data, dict) else data
            return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as e:
        logging.warning(f"Recall unavailable: {e}")
        return []
