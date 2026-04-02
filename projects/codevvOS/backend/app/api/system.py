from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth import require_role

router = APIRouter(prefix="/api/system")

CGROUP_BASE = Path("/sys/fs/cgroup")


class SystemMetrics(BaseModel):
    memory_used_bytes: Optional[int] = None
    memory_limit_bytes: Optional[int] = None
    cpu_usage_usec: Optional[int] = None


def _read_cgroup_file(filename: str) -> Optional[int]:
    try:
        value = (CGROUP_BASE / filename).read_text().strip()
        if value == "max":
            return None
        return int(value)
    except (FileNotFoundError, ValueError, PermissionError):
        return None


def _read_cpu_usage() -> Optional[int]:
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
