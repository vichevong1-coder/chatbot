"""Session transcript storage.

``SessionStore`` is the interface the chat route depends on; ``RedisSessionStore``
is the production implementation over ``dal.clients.redis``; ``InMemorySessionStore``
backs the tests (no Redis, no network). postgres_store / summarizer / cache stay
empty stubs until Phase 2 (plan.md).

Transcripts are lists of dal ChatMessage dicts stored as JSON under
``session:{session_id}`` with a ~24h sliding TTL — homework sessions do not need
to outlive the school day, and children's chat text must not accumulate forever
(claude.md §5).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from dal.clients.redis import get_redis

SESSION_TTL_SECONDS = 24 * 60 * 60  # ~24h


def _key(session_id: str) -> str:
    return f"session:{session_id}"


class SessionStore(ABC):
    """What the chat route needs from a transcript store."""

    @abstractmethod
    async def get(self, session_id: str) -> list[dict[str, Any]]:
        """Return the transcript (possibly empty), oldest first."""

    @abstractmethod
    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        """Append messages to the transcript and refresh the TTL."""

    @abstractmethod
    async def touch(self, session_id: str) -> None:
        """Refresh the ~24h TTL without writing."""


class RedisSessionStore(SessionStore):
    """JSON transcript under ``session:{id}``; client comes lazily from dal."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    async def get(self, session_id: str) -> list[dict[str, Any]]:
        raw = await get_redis().get(_key(session_id))
        if not raw:
            return []
        return json.loads(raw)

    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        transcript = await self.get(session_id)
        transcript.extend(messages)
        await get_redis().set(
            _key(session_id),
            json.dumps(transcript, ensure_ascii=False),
            ex=self._ttl,
        )

    async def touch(self, session_id: str) -> None:
        await get_redis().expire(_key(session_id), self._ttl)


class InMemorySessionStore(SessionStore):
    """Test double: same interface, a plain dict, no TTL enforcement."""

    def __init__(self) -> None:
        self.sessions: dict[str, list[dict[str, Any]]] = {}
        self.touched: list[str] = []

    async def get(self, session_id: str) -> list[dict[str, Any]]:
        return list(self.sessions.get(session_id, []))

    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        self.sessions.setdefault(session_id, []).extend(messages)

    async def touch(self, session_id: str) -> None:
        self.touched.append(session_id)
