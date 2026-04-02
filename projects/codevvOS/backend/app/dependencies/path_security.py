from __future__ import annotations

import os
import urllib.parse

from fastapi import HTTPException


def verify_path_in_workspace(path: str, workspace_root: str) -> str:
    # Decode URL-encoded components
    path = urllib.parse.unquote(path)

    # Reject null bytes
    if "\x00" in path or chr(0) in path:
        raise HTTPException(status_code=400, detail="Invalid path: null bytes not allowed")

    # Resolve both paths (handles .., symlinks)
    try:
        resolved_path = os.path.realpath(os.path.abspath(path))
        resolved_root = os.path.realpath(os.path.abspath(workspace_root))
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {e}")

    # Ensure resolved path starts with workspace root
    if not resolved_path.startswith(resolved_root + os.sep) and resolved_path != resolved_root:
        raise HTTPException(
            status_code=400,
            detail="Path traversal detected: path escapes workspace",
        )

    return resolved_path
