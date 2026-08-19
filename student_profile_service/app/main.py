"""student_profile_service app factory."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.profile import router as profile_router

SERVICE_NAME = "student_profile_service"


def create_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    app = FastAPI(title="Tunsay Student Profile Service", version="0.1.0")
    app.state.session_factory = session_factory

    app.include_router(profile_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
