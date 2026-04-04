"""JSX compiler service — transforms JSX to React.createElement via esbuild."""
from __future__ import annotations

import asyncio
import os
import tempfile


async def compile_jsx(jsx: str) -> tuple[str | None, str | None]:
    """Run esbuild to transform JSX to React.createElement calls.

    Returns (compiled_code, error_message).
    compiled_code is None on error; error_message is None on success.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jsx",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(jsx)
        tmp_path = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            "esbuild",
            "--bundle=false",
            "--jsx=transform",
            "--platform=browser",
            tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            return stdout.decode("utf-8"), None
        return None, stderr.decode("utf-8")
    finally:
        os.unlink(tmp_path)
