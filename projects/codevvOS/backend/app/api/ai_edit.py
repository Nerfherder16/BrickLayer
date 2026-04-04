"""Inline edit endpoint — POST /api/ai/inline-edit."""
from __future__ import annotations

import time
from collections.abc import AsyncIterator

from backend.app.services.llm_service import stream_inline_edit
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Rate limiting — 5 requests per 60-second window, keyed by session_id
# ---------------------------------------------------------------------------

_RATE_LIMIT = 5
_RATE_WINDOW = 60.0

# Maps session_id -> list of request timestamps (float, epoch seconds)
_rate_store: dict[str, list[float]] = {}


def _check_rate_limit(session_id: str) -> None:
    """Raise 429 if session has exceeded 5 requests in the last 60 seconds."""
    now = time.monotonic()
    window_start = now - _RATE_WINDOW
    timestamps = _rate_store.get(session_id, [])
    # Prune expired timestamps
    timestamps = [t for t in timestamps if t > window_start]
    if len(timestamps) >= _RATE_LIMIT:
        _rate_store[session_id] = timestamps
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    timestamps.append(now)
    _rate_store[session_id] = timestamps


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class InlineEditRequest(BaseModel):
    prompt: str
    document: str
    language: str


# ---------------------------------------------------------------------------
# SSE generator
# ---------------------------------------------------------------------------


async def _sse_stream(prompt: str, document: str, language: str) -> AsyncIterator[str]:
    async for chunk in stream_inline_edit(prompt, document, language):
        yield f"data: {chunk}\n\n"
    yield "event: done\ndata: \n\n"


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

_MAX_DOCUMENT_BYTES = 100 * 1024  # 100 KB


@router.post("/inline-edit")
async def inline_edit(body: InlineEditRequest, request: Request) -> StreamingResponse:
    """Stream an inline-edited document via SSE. Rate limited to 5 req/min per session."""
    session_id = request.headers.get("X-Session-Id", "default")
    _check_rate_limit(session_id)

    if len(body.document.encode()) > _MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds 100 KB limit")

    return StreamingResponse(
        _sse_stream(body.prompt, body.document, body.language),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
