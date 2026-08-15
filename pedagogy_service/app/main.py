"""pedagogy_service app factory: /health plus the explain router.

The ONLY service that talks to Gemini (via dal.llm_client.LlmClient). GEMINI_API_KEY
and GEMINI_MODEL are consumed inside LlmClient — nothing here duplicates them.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api import explain_router

SERVICE_NAME = "pedagogy_service"


def create_app() -> FastAPI:
    app = FastAPI(title="Tunsay Pedagogy Service", version="0.1.0")
    app.include_router(explain_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
