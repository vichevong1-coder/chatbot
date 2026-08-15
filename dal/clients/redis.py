"""Async Redis client factory.

Same shape as :mod:`dal.clients.postgres`: a lazy, module-level cached client built from
``REDIS_URL`` (see ``.env.example``). ``from_url`` does not connect — the first command
does — so building the client is safe without a live Redis.
"""

from __future__ import annotations

import os

from redis.asyncio import Redis

_client: Redis | None = None


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        raise RuntimeError("REDIS_URL is not set (see .env.example)")
    return url


def get_redis() -> Redis:
    """Return the process-wide async Redis client, creating it lazily."""
    global _client
    if _client is None:
        _client = Redis.from_url(_redis_url(), decode_responses=True)
    return _client


async def close() -> None:
    """Close the cached client's connections and forget it."""
    global _client
    client, _client = _client, None
    if client is not None:
        await client.aclose()


def reset() -> None:
    """Forget the cached client without awaiting close (test helper)."""
    global _client
    _client = None
