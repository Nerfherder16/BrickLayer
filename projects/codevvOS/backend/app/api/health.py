from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


async def _check_postgres() -> bool:
    try:
        from backend.app.db.session import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    try:
        from backend.app.core.config import settings
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


@router.get("/health")
async def health_check():
    pg_ok = await _check_postgres()
    redis_ok = await _check_redis()

    status = "healthy" if (pg_ok and redis_ok) else "degraded"
    code = 200 if (pg_ok and redis_ok) else 503

    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "postgres": pg_ok,
            "redis": redis_ok,
        },
    )
