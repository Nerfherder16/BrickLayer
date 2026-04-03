from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx

BRICKLAYER_URL = "http://bricklayer:8300"
TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)


def _get_secret() -> str:
    p = Path("/run/secrets/bl_internal_secret")
    if p.exists():
        return p.read_text().strip()
    return os.environ.get("BL_INTERNAL_SECRET", "dev-bl-secret")


async def spawn_agent(name: str, prompt: str, cwd: str = ".") -> dict[str, Any]:
    headers = {"X-BL-Internal-Secret": _get_secret()}
    payload = {"name": name, "prompt": prompt, "cwd": cwd}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{BRICKLAYER_URL}/agent/spawn", json=payload, headers=headers
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        return {"error": "bricklayer_unavailable", "detail": "Cannot connect to bricklayer service"}
    except Exception as e:
        return {"error": "bricklayer_error", "detail": str(e)}


async def get_agent_status(agent_id: str) -> dict[str, Any]:
    headers = {"X-BL-Internal-Secret": _get_secret()}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{BRICKLAYER_URL}/agent/{agent_id}/status", headers=headers
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        return {"error": "bricklayer_unavailable", "detail": "Cannot connect to bricklayer service"}
    except Exception as e:
        return {"error": "bricklayer_error", "detail": str(e)}


async def stream_agent(agent_id: str) -> AsyncGenerator[str, None]:
    headers = {"X-BL-Internal-Secret": _get_secret()}
    stream_timeout = httpx.Timeout(connect=5.0, read=300.0, write=10.0, pool=5.0)
    try:
        async with httpx.AsyncClient(timeout=stream_timeout) as client:
            async with client.stream(
                "GET", f"{BRICKLAYER_URL}/agent/{agent_id}/stream", headers=headers
            ) as resp:
                async for line in resp.aiter_lines():
                    yield line
    except httpx.ConnectError:
        yield '{"error": "bricklayer_unavailable"}'
