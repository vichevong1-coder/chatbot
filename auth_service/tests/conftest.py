"""Test fixtures: SQLite (aiosqlite) instead of Postgres, injected via create_app.

Only the ``users`` and ``schools`` tables are created — the full dal metadata carries
postgres JSONB columns SQLite cannot compile, so ``create_all`` is filtered to exactly
the two tables auth_service touches.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Make `import app.*` resolve to auth_service/app regardless of pytest's rootdir.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-0123456789")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "30")

from dal.models.base import Base  # noqa: E402
from dal.models.user import School, User  # noqa: E402

from app.main import create_app  # noqa: E402

DEMO_SCHOOL = {
    "code": "TUNSAY-G4-DEMO",
    "name": "Primary Learning Campus",
    "class_name": "Class 4A",
    "grade": 4,
}
OTHER_SCHOOL = {
    "code": "TUNSAY-G5-OTHER",
    "name": "Riverside Primary",
    "class_name": "Class 5B",
    "grade": 5,
}


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/auth_test.db")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=[School.__table__, User.__table__]
                )
            )
        async with factory() as session:
            session.add(School(**DEMO_SCHOOL))
            session.add(School(**OTHER_SCHOOL))
            await session.commit()

    asyncio.run(_setup())
    yield factory
    asyncio.run(engine.dispose())


@pytest.fixture()
def client(session_factory):
    app = create_app(session_factory=session_factory)
    with TestClient(app) as test_client:
        yield test_client
