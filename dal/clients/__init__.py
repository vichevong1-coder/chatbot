"""Outbound infrastructure clients shared by every Tunsay service.

Each submodule is a lazy factory over one backing service:

- :mod:`dal.clients.postgres` — async SQLAlchemy engine + sessionmaker (``DATABASE_URL``)
- :mod:`dal.clients.redis` — ``redis.asyncio`` client (``REDIS_URL``)

The Gemini wrapper lives one level up, in :mod:`dal.llm_client`.
"""

from dal.clients.postgres import get_engine, get_session_factory
from dal.clients.redis import get_redis

__all__ = ["get_engine", "get_session_factory", "get_redis"]
