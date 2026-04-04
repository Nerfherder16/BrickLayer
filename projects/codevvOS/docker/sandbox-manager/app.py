from __future__ import annotations

import os

import aiodocker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Sandbox Manager")


class ExecRequest(BaseModel):
    container_id: str
    command: list[str]
    workdir: str = "/workspace"


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/sandbox/exec")
async def sandbox_exec(body: ExecRequest):
    # TIME_BOMB: Uses aiodocker (async), NOT docker-py (sync, blocks event loop).
    # Docker socket access is via docker-socket-proxy, not direct mount.
    try:
        # DOCKER_HOST is set by docker-socket-proxy
        docker_host = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
        async with aiodocker.Docker(url=docker_host) as docker:
            container = await docker.containers.get(body.container_id)
            exec_id = await container.exec(
                cmd=body.command,
                workdir=body.workdir,
            )
            return {"exec_id": exec_id._id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
