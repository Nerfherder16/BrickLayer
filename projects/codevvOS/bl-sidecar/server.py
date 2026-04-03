import asyncio
import signal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="BrickLayer Sidecar", version="1.0.0")

ALLOWED_COMMANDS = {"echo", "bl", "python", "ls", "pwd"}

_active_state: dict = {"process": None, "command": None}


class RunRequest(BaseModel):
    command: str
    args: list[str] = []


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    proc = _active_state["process"]
    cmd = _active_state["command"]
    return {"active": proc is not None, "command": cmd}


async def _run_generator(command: str, args: list[str]):
    process = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    _active_state["process"] = process
    _active_state["command"] = command
    try:
        async for line in process.stdout:
            yield {"data": line.decode().rstrip()}
        await process.wait()
    finally:
        _active_state["process"] = None
        _active_state["command"] = None


@app.post("/run")
async def run_command(body: RunRequest):
    if body.command not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=400, detail="Command not allowed")
    return EventSourceResponse(_run_generator(body.command, body.args))


@app.post("/interrupt")
async def interrupt():
    proc = _active_state["process"]
    if proc is None:
        raise HTTPException(status_code=409, detail="No active process")
    proc.send_signal(signal.SIGINT)
    return {"status": "interrupted"}
