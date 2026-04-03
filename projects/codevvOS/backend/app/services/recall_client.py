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
            f"{RECALL_BASE_URL}/memory",
            json={
                "content": jsx,
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
    """Fetch all artifact memories from Recall, sorted by timestamp desc. Returns [] on error."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RECALL_BASE_URL}/memory",
                params={"type": "artifact"},
                timeout=5.0,
            )
            response.raise_for_status()
            items = response.json()
            return sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)
    except Exception as e:
        logging.warning(f"Recall unavailable: {e}")
        return []
