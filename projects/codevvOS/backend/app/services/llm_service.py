"""Ollama LLM integration for inline document editing."""
from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://100.70.195.84:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


async def stream_inline_edit(
    prompt: str, document: str, language: str
) -> AsyncIterator[str]:
    """Stream edited document text from Ollama generate API."""
    system_prompt = (
        f"You are a code editor. The user will give you a {language} document "
        "and an edit instruction. Return only the edited document, no explanation."
    )
    full_prompt = f"Instruction: {prompt}\n\nDocument:\n{document}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "system": system_prompt,
                "prompt": full_prompt,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = chunk.get("response", "")
                if text:
                    yield text
