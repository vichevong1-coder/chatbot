"""solver_service app factory: /health plus the solve router."""

from __future__ import annotations

from fastapi import FastAPI

from app.api import solve_router

SERVICE_NAME = "solver_service"


def create_app() -> FastAPI:
    app = FastAPI(title="Tunsay Solver Service", version="0.1.0")
    app.include_router(solve_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
