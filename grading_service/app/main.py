from __future__ import annotations

from fastapi import FastAPI
from app.api.grade import router as grade_router

SERVICE_NAME = "grading_service"

def create_app() -> FastAPI:
    app = FastAPI(title="Tunsay Grading Service", version="0.1.0")
    app.include_router(grade_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app

app = create_app()
