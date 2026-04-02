from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.api.auth import limiter, router as auth_router
from backend.app.api.files import router as files_router
from backend.app.api.health import router as health_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.system import router as system_router

app = FastAPI(title="CodeVV OS Backend")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(system_router)
app.include_router(notifications_router)
app.include_router(files_router)
