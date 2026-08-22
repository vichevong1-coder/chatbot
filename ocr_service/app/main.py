"""FastAPI application for ocr_service."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.extract import router as extract_router
from app.core.math_ocr import MathOcrEngine

SERVICE_NAME = "ocr_service"


def create_app(ocr_engine: MathOcrEngine | None = None) -> FastAPI:
    """Application factory with dependency injection seam for testing."""
    app = FastAPI(title=SERVICE_NAME)
    app.state.ocr_engine = ocr_engine or MathOcrEngine()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    app.include_router(extract_router)
    return app


app = create_app()
