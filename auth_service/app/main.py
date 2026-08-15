"""auth_service app factory.

Student identity only: school code + Khmer display name + optional 4-digit PIN.
No password, no email, no roles (.claude/contracts.md section 4).

``create_app`` takes an optional async session factory so tests can inject SQLite;
``None`` means "use dal.clients.postgres.get_session_factory() lazily at request time",
so importing this module never needs DATABASE_URL.
"""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api import login, me, register
from app.core.throttle import AttemptThrottle

SERVICE_NAME = "auth_service"


def create_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    throttle: AttemptThrottle | None = None,
) -> FastAPI:
    app = FastAPI(title=SERVICE_NAME)
    app.state.session_factory = session_factory
    app.state.throttle = throttle or AttemptThrottle()

    app.include_router(register.router)
    app.include_router(login.router)
    app.include_router(me.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    return app


app = create_app()
