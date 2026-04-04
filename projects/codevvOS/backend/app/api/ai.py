"""AI endpoints with per-user rate limiting."""
from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from shared.auth import bearer_scheme, verify_jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

RATE_LIMIT_AI = "30/minute"


def _get_user_key(request: Request) -> str:
    """Extract user_id from JWT for per-user rate limiting, fall back to IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = verify_jwt(auth[7:])
            return f"user:{payload.get('user_id', '')}"
        except Exception:  # noqa: S110 — intentional silent fallback to IP key
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_key)
router = APIRouter(prefix="/api/ai")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


async def _stream_ollama(base_url: str, model: str, messages: list[dict]) -> AsyncIterator[str]:
    """Yield SSE lines from an Ollama streaming chat response."""
    try:
        async with httpx.AsyncClient() as client:
            with client.stream(
                "POST",
                f"{base_url}/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield f"data: {json.dumps({'token': content})}\n\n"
    except httpx.ConnectError:
        yield f"data: {json.dumps({'error': 'AI service unavailable'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"
        return
    yield "data: [DONE]\n\n"


@router.get("/status")
@limiter.limit(RATE_LIMIT_AI)
async def ai_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Return AI service availability. Rate limited to 30 requests/minute per user."""
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return {"status": "available"}


@router.post("/chat")
@limiter.limit(RATE_LIMIT_AI)
async def ai_chat(
    request: Request,
    body: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> StreamingResponse:
    """Stream Ollama chat responses as SSE. Rate limited to 30 requests/minute per user."""
    try:
        verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    base_url = os.environ.get("OLLAMA_BASE_URL")
    if not base_url:
        raise HTTPException(status_code=503, detail="AI service not configured")

    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    messages = [
        *[{"role": m.role, "content": m.content} for m in body.history],
        {"role": "user", "content": body.message},
    ]

    return StreamingResponse(
        _stream_ollama(base_url, model, messages),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
