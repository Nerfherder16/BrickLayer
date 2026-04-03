from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from shared.auth import require_role

router = APIRouter(prefix="/api/system")

CGROUP_BASE = Path("/sys/fs/cgroup")


class SystemMetrics(BaseModel):
    memory_used_bytes: int | None = None
    memory_limit_bytes: int | None = None
    cpu_usage_usec: int | None = None


def _read_cgroup_file(filename: str) -> int | None:
    try:
        value = (CGROUP_BASE / filename).read_text().strip()
        if value == "max":
            return None
        return int(value)
    except (FileNotFoundError, ValueError, PermissionError):
        return None


def _read_cpu_usage() -> int | None:
    try:
        cpu_stat = (CGROUP_BASE / "cpu.stat").read_text()
        for line in cpu_stat.splitlines():
            if line.startswith("usage_usec "):
                return int(line.split()[1])
    except (FileNotFoundError, ValueError, PermissionError):
        pass
    return None


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(user: dict = Depends(require_role("admin"))):
    return SystemMetrics(
        memory_used_bytes=_read_cgroup_file("memory.current"),
        memory_limit_bytes=_read_cgroup_file("memory.max"),
        cpu_usage_usec=_read_cpu_usage(),
    )
