"""safety_service — app factory, router registration, /health (claude.md §5)."""

from __future__ import annotations

from fastapi import FastAPI

from .api import check

SERVICE_NAME = "safety_service"


def create_app() -> FastAPI:
    app = FastAPI(title="Tunsay Safety Service", docs_url=None, redoc_url=None)
    app.include_router(check.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
