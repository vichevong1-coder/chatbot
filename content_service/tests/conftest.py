"""content_service test fixtures.

Tests run against in-memory SQLite via aiosqlite — no Postgres needed. The one wrinkle:
``dal.models.Step`` uses the postgres JSONB type, which SQLite cannot create. The
standard trick is a compile hook that renders JSONB as plain JSON on the sqlite
dialect, registered below before any ``create_all`` runs.

The session factory is injected into ``create_app`` / the seeder — no dal client is
patched and ``DATABASE_URL`` is never consulted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

# Make `app` and `scripts` importable when pytest runs from the repo root.
SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from dal.models import Base  # noqa: E402

from app.main import create_app  # noqa: E402


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):  # noqa: ANN001, ANN003, ANN202
    """Render postgres JSONB columns as JSON when creating tables on SQLite."""
    return "JSON"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def session_factory():
    """A fresh in-memory database per test. StaticPool keeps every session on the one
    connection that holds the :memory: database."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def seeded_factory(session_factory):
    """The database after a real seed run: 6 valid problems loaded, science-g4-water
    rejected (the known corpus defect, .claude/contracts.md section 6)."""
    from scripts.seed_exercises import main as seed_main

    rc = await seed_main(session_factory=session_factory)
    assert rc == 1  # the defective file must fail ingest — see test_seed_loader
    return session_factory


@pytest.fixture
async def client(seeded_factory):
    """An httpx client over the app, wired to the seeded SQLite database."""
    app = create_app(session_factory=seeded_factory)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
