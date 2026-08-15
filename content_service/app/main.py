"""content_service app factory: /health, the public problems router, and the
internal-only admin router (reachable only on the compose network — see
app/api/admin.py and .claude/contracts.md section 4)."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api import admin_router, problems_router
from app.infrastructure.repository import ProblemRepository

SERVICE_NAME = "content_service"


def create_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    """``session_factory`` is injectable for tests; the default lazily binds to
    ``DATABASE_URL`` via dal.clients.postgres on first use."""
    app = FastAPI(title="Tunsay Content Service", version="0.1.0")
    app.state.repository = ProblemRepository(session_factory)
    app.include_router(problems_router)
    app.include_router(admin_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
