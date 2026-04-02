from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.dependencies.path_security import verify_path_in_workspace
from shared.auth import verify_jwt

router = APIRouter(prefix="/api/files")

WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")

# auto_error=False so we can return 401 instead of 403 for missing credentials
_bearer = HTTPBearer(auto_error=False)


class FileEntry(BaseModel):
    name: str
    type: str  # "file" or "dir"
    size: int | None = None
    modified: float | None = None


class TreeResponse(BaseModel):
    name: str
    type: str
    size: int | None = None
    modified: float | None = None
    children: list[FileEntry] | None = None


def _get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return verify_jwt(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/tree", response_model=TreeResponse)
async def get_file_tree(
    path: str = Query(...),
    user: dict = Depends(_get_current_user),
) -> TreeResponse:
    try:
        resolved = verify_path_in_workspace(path, WORKSPACE_ROOT)
    except HTTPException:
        raise

    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="Path not found")

    if not os.path.isdir(resolved):
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries: list[FileEntry] = []
    try:
        for entry in os.scandir(resolved):
            if entry.name == ".git":
                continue
            entries.append(
                FileEntry(
                    name=entry.name,
                    type="dir" if entry.is_dir() else "file",
                    size=entry.stat().st_size if entry.is_file() else None,
                    modified=entry.stat().st_mtime,
                )
            )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    dir_stat = os.stat(resolved)
    return TreeResponse(
        name=os.path.basename(resolved) or resolved,
        type="dir",
        modified=dir_stat.st_mtime,
        children=entries,
    )


class FileOperation(BaseModel):
    action: str  # read, write, rename, delete, create_dir
    content: str | None = None
    new_name: str | None = None


@router.patch("/{path:path}")
async def file_operation(
    path: str,
    operation: FileOperation,
    user: dict = Depends(_get_current_user),
) -> dict:
    try:
        resolved = verify_path_in_workspace(path, WORKSPACE_ROOT)
    except HTTPException:
        raise

    if operation.action == "read":
        if not os.path.exists(resolved):
            raise HTTPException(status_code=404, detail="File not found")
        with open(resolved) as f:
            return {"content": f.read()}

    elif operation.action == "write":
        if operation.content is None:
            raise HTTPException(status_code=400, detail="content required for write")
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w") as f:
            f.write(operation.content)
        return {"status": "written"}

    elif operation.action == "rename":
        if not operation.new_name:
            raise HTTPException(status_code=400, detail="new_name required for rename")
        if not os.path.exists(resolved):
            raise HTTPException(status_code=404, detail="File not found")
        new_path = os.path.join(os.path.dirname(resolved), operation.new_name)
        new_resolved = verify_path_in_workspace(new_path, WORKSPACE_ROOT)
        os.rename(resolved, new_resolved)
        return {"status": "renamed"}

    elif operation.action == "delete":
        if not os.path.exists(resolved):
            raise HTTPException(status_code=404, detail="File not found")
        if os.path.isdir(resolved):
            shutil.rmtree(resolved)
        else:
            os.remove(resolved)
        return {"status": "deleted"}

    elif operation.action == "create_dir":
        os.makedirs(resolved, exist_ok=True)
        return {"status": "created"}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {operation.action}")


@router.get("/watch")
async def watch_files(
    path: str = Query(...),
    user: dict = Depends(_get_current_user),
):
    try:
        resolved = verify_path_in_workspace(path, WORKSPACE_ROOT)
    except HTTPException:
        raise

    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail="Path not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            from watchfiles import Change, awatch

            async for changes in awatch(resolved):
                for change_type, file_path in changes:
                    rel_path = os.path.relpath(file_path, resolved)
                    if rel_path.startswith(".git"):
                        continue

                    if change_type == Change.added:
                        event_type = "create"
                    elif change_type == Change.deleted:
                        event_type = "delete"
                    else:
                        event_type = "change"

                    data = json.dumps({"type": event_type, "path": rel_path})
                    yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
