from backend.app.api import ai_edit
from backend.app.api import artifacts
from backend.app.api import graph
from backend.app.api.ai import router as ai_router
from backend.app.api.auth import api_router as auth_api_router
from backend.app.api.auth import limiter
from backend.app.api.auth import router as auth_router
from backend.app.api.claude_settings import router as claude_settings_router
from backend.app.api.files import router as files_router
from backend.app.api.health import router as health_router
from backend.app.api.layout import router as layout_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.settings import router as settings_router
from backend.app.api.system import router as system_router
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="CodeVV OS Backend")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(auth_api_router)
app.include_router(ai_router)
app.include_router(claude_settings_router)
app.include_router(system_router)
app.include_router(notifications_router)
app.include_router(files_router)
app.include_router(settings_router)
app.include_router(layout_router)
app.include_router(ai_edit.router, prefix="/api/ai")
app.include_router(artifacts.router, prefix="/api/artifacts")
app.include_router(graph.router, prefix="/api/graph")
