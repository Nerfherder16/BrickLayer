"""Artifact endpoints — compile (JSX→JS) and persist/retrieve via Recall."""
from __future__ import annotations

from backend.app.services import recall_client
from backend.app.services.jsx_compiler import compile_jsx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

ALLOWED_DEPS: frozenset[str] = frozenset({"react", "react-dom", "recharts", "lucide-react"})

_MAX_JSX_BYTES = 50 * 1024  # 50 KB


class CompileRequest(BaseModel):
    jsx: str
    dependencies: list[str] = []


class CompileResponse(BaseModel):
    compiled: str | None
    error: str | None


@router.post("/compile", response_model=CompileResponse)
async def compile_artifact(body: CompileRequest) -> CompileResponse:
    """Transform JSX to React.createElement via esbuild."""
    if not body.jsx or not body.jsx.strip():
        raise HTTPException(status_code=400, detail="jsx must not be empty")

    if len(body.jsx.encode()) > _MAX_JSX_BYTES:
        raise HTTPException(status_code=413, detail="jsx exceeds 50 KB limit")

    for dep in body.dependencies:
        if dep not in ALLOWED_DEPS:
            raise HTTPException(
                status_code=400,
                detail=f"dependency '{dep}' is not in the allowlist",
            )

    compiled, error = await compile_jsx(body.jsx)
    return CompileResponse(compiled=compiled, error=error)


class PersistRequest(BaseModel):
    artifact_id: str
    title: str
    jsx: str
    compiled: str | None = None


@router.post("/persist")
async def persist_artifact(body: PersistRequest) -> dict:
    """Store artifact to Recall memory system. Returns the Recall memory ID."""
    memory_id = await recall_client.persist_artifact(
        body.artifact_id,
        body.title,
        body.jsx,
        body.compiled,
    )
    return {"id": memory_id}


@router.get("/history")
async def get_history() -> list:
    """Fetch artifact history from Recall, sorted by timestamp desc. Returns [] on Recall failure."""
    return await recall_client.get_artifact_history()
