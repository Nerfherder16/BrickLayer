from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.system import router as system_router

app = FastAPI(title="CodeVV OS Backend")

app.include_router(health_router)
app.include_router(system_router)
app.include_router(notifications_router)
