from fastapi import FastAPI

from backend.app.api.health import router as health_router

app = FastAPI(title="CodeVV OS Backend")

app.include_router(health_router)
