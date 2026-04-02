from __future__ import annotations

from arq.connections import RedisSettings

from backend.app.core.config import settings as app_settings


async def health_check_job(ctx: dict) -> dict:
    return {"status": "ok", "worker": "healthy"}


def _get_redis_settings() -> RedisSettings:
    return RedisSettings(host=app_settings.redis_host, port=app_settings.redis_port)


class WorkerSettings:
    functions = [health_check_job]
    job_timeout = 300
    max_jobs = 10
    redis_settings = _get_redis_settings()
