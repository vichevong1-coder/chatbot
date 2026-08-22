"""auth_service app factory.

Student identity only: school code + Khmer display name + optional 4-digit PIN.
No password, no email, no roles (.claude/contracts.md section 4).

``create_app`` takes an optional async session factory so tests can inject SQLite;
``None`` means "use dal.clients.postgres.get_session_factory() lazily at request time",
so importing this module never needs DATABASE_URL.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dal.clients.postgres import get_engine, get_session_factory
from dal.models.base import Base
from dal.models.user import School, User

from app.api import login, me, register
from app.core.throttle import AttemptThrottle

SERVICE_NAME = "auth_service"

DEFAULT_SCHOOLS = [
    {"code": "TUNSAY-G4-DEMO", "name": "Primary Learning Campus", "class_name": "Class 4A", "grade": 4},
    {"code": "WEG-TK", "name": "Westline Toul Kork", "class_name": "Class 4A", "grade": 4},
    {"code": "WEG-SR", "name": "Westline Siem Reap", "class_name": "Class 4B", "grade": 4},
    {"code": "TEST-01", "name": "Test School", "class_name": "Class 4T", "grade": 4},
]


async def _auto_seed_schools() -> None:
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=[School.__table__, User.__table__], checkfirst=True
                )
            )
        factory = get_session_factory()
        async with factory() as session:
            for data in DEFAULT_SCHOOLS:
                existing = await session.get(School, data["code"])
                if existing is None:
                    session.add(School(**data))
            await session.commit()
    except Exception as exc:
        # Best-effort seeding on startup; never crash if DB is starting up
        pass


def create_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    throttle: AttemptThrottle | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if session_factory is None:
            await _auto_seed_schools()
        yield

    app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)
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
