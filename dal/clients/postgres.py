"""Async Postgres engine/session factory.

A thin, lazy factory around SQLAlchemy's async engine — no business logic lives here.
Configuration comes from ``DATABASE_URL`` (see ``.env.example``). The URL in the env file
uses the plain ``postgresql://`` scheme; the async driver is psycopg 3, so the scheme is
rewritten to ``postgresql+psycopg://`` before the engine is created.

The engine and sessionmaker are cached at module level so every caller in a process
shares one connection pool. ``reset()`` / ``dispose()`` exist for tests and for clean
shutdown; nothing here opens a network connection until a session is actually used.
"""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see .env.example)")
    # The compose/env convention is the bare scheme; SQLAlchemy needs the async driver.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, creating it lazily."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide ``async_sessionmaker`` bound to :func:`get_engine`."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def dispose() -> None:
    """Close the pooled connections and forget the cached engine/factory."""
    global _engine, _session_factory
    engine, _engine, _session_factory = _engine, None, None
    if engine is not None:
        await engine.dispose()


def reset() -> None:
    """Forget the cached engine/factory without awaiting disposal (test helper).

    Prefer :func:`dispose` when an event loop is available — this variant is for
    synchronous test teardown where no connection was ever opened.
    """
    global _engine, _session_factory
    _engine = None
    _session_factory = None
