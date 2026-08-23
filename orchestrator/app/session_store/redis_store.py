"""Session transcript storage.

``SessionStore`` is the interface the chat route depends on; ``RedisSessionStore``
is the production implementation over ``dal.clients.redis``; ``InMemorySessionStore``
backs the tests (no Redis, no network).

Key namespace layout (one Redis data-structure per concern, all share the same
24 h sliding TTL refreshed on every write):

  chat_sessions:{sid}          Hash   — session metadata
  chat_messages:{sid}          List   — one JSON entry per turn
  session_contexts:{sid}       Hash   — live working memory
  intent_routes:{sid}          List   — last 100 intent detections
  service_calls:{sid}          List   — last 100 downstream call logs
  conversation_summaries:{sid} String — latest deterministic summary
  chat_feedback:{sid}          Hash   — rating + comment
  chat_attachments:{sid}       List   — uploaded file references
  failed_requests:{sid}        List   — last 100 error events
  model_usage_logs:{sid}       List   — last 100 LLM token records
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from dal.clients.redis import get_redis

SESSION_TTL_SECONDS = 24 * 60 * 60  # ~24 h
_LIST_CAP = 100  # max entries kept for capped lists


# Key helpers

def _k(namespace: str, session_id: str) -> str:
    return f"{namespace}:{session_id}"


def _all_keys(session_id: str) -> list[str]:
    """Every key that belongs to this session — used for TTL refresh."""
    namespaces = [
        "chat_sessions",
        "chat_messages",
        "session_contexts",
        "intent_routes",
        "service_calls",
        "conversation_summaries",
        "chat_feedback",
        "chat_attachments",
        "failed_requests",
        "model_usage_logs",
    ]
    return [_k(ns, session_id) for ns in namespaces]


# Abstract base

class SessionStore(ABC):
    """What the chat route and graph nodes need from a session store."""

    # -- existing transcript API (unchanged) --------------------------------

    @abstractmethod
    async def get(self, session_id: str) -> list[dict[str, Any]]:
        """Return the chat transcript (oldest first)."""

    @abstractmethod
    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        """Append messages and refresh the TTL."""

    @abstractmethod
    async def touch(self, session_id: str) -> None:
        """Refresh the 24 h TTL across ALL namespaces without writing data."""

    # -- session metadata ---------------------------------------------------

    @abstractmethod
    async def init_session(
        self,
        session_id: str,
        student_id: str,
        grade: int,
        language: str,
    ) -> None:
        """Create/reset the session metadata hash. Safe to call multiple times."""

    @abstractmethod
    async def get_session_meta(self, session_id: str) -> dict[str, Any] | None:
        """Return session metadata dict, or None if session does not exist."""

    # -- context (working memory) ------------------------------------------

    @abstractmethod
    async def set_context(self, session_id: str, **fields: Any) -> None:
        """Merge fields into the session_contexts hash."""

    @abstractmethod
    async def get_context(self, session_id: str) -> dict[str, Any]:
        """Return the full context hash (empty dict if not set)."""

    # -- intent routes ------------------------------------------------------

    @abstractmethod
    async def log_intent(
        self,
        session_id: str,
        intent: str,
        routed_to: str,
        confidence: float | None = None,
    ) -> None:
        """Append an intent detection record (capped at 100)."""

    # -- service calls -------------------------------------------------------

    @abstractmethod
    async def log_service_call(
        self,
        session_id: str,
        service_name: str,
        latency_ms: float,
        status: str,
    ) -> None:
        """Append a downstream service call record (capped at 100)."""

    # -- conversation summary -----------------------------------------------

    @abstractmethod
    async def set_summary(self, session_id: str, summary_text: str) -> None:
        """Store the latest conversation summary string."""

    @abstractmethod
    async def get_summary(self, session_id: str) -> str | None:
        """Return the stored summary, or None."""

    # -- feedback -----------------------------------------------------------

    @abstractmethod
    async def set_feedback(
        self, session_id: str, rating: int, comment: str = ""
    ) -> None:
        """Store student feedback (overwrites previous)."""

    # -- attachments --------------------------------------------------------

    @abstractmethod
    async def log_attachment(
        self, session_id: str, file_key: str, file_type: str
    ) -> None:
        """Append an uploaded-file reference."""

    # -- failed requests ----------------------------------------------------

    @abstractmethod
    async def log_failure(
        self,
        session_id: str,
        error_type: str,
        message: str,
        node: str = "",
    ) -> None:
        """Append a fallback/error event (capped at 100)."""

    # -- model usage --------------------------------------------------------

    @abstractmethod
    async def log_model_usage(
        self,
        session_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Append an LLM token usage record (capped at 100)."""


# Redis implementation

class RedisSessionStore(SessionStore):
    """Production store: 10 Redis namespaces, all share a 24 h sliding TTL."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    # -- internal helpers ---------------------------------------------------

    async def _refresh_ttl(self, session_id: str) -> None:
        r = get_redis()
        async with r.pipeline(transaction=False) as pipe:
            for key in _all_keys(session_id):
                pipe.expire(key, self._ttl)
            await pipe.execute()

    async def _rpush_capped(
        self, session_id: str, namespace: str, entry: dict[str, Any]
    ) -> None:
        key = _k(namespace, session_id)
        r = get_redis()
        async with r.pipeline(transaction=True) as pipe:
            pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
            pipe.ltrim(key, -_LIST_CAP, -1)
            await pipe.execute()

    # -- transcript API (get/append/touch) ----------------------------------

    async def get(self, session_id: str) -> list[dict[str, Any]]:
        raw = await get_redis().lrange(_k("chat_messages", session_id), 0, -1)
        return [json.loads(r) for r in raw]

    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        r = get_redis()
        key = _k("chat_messages", session_id)
        async with r.pipeline(transaction=True) as pipe:
            for msg in messages:
                pipe.rpush(key, json.dumps(msg, ensure_ascii=False))
            await pipe.execute()
        await self._refresh_ttl(session_id)

    async def touch(self, session_id: str) -> None:
        await self._refresh_ttl(session_id)

    # -- session metadata ---------------------------------------------------

    async def init_session(
        self,
        session_id: str,
        student_id: str,
        grade: int,
        language: str,
    ) -> None:
        r = get_redis()
        await r.hset(
            _k("chat_sessions", session_id),
            mapping={
                "student_id": student_id,
                "grade": str(grade),
                "language": language,
                "started_at": str(int(time.time())),
                "last_active_at": str(int(time.time())),
                "status": "active",
            },
        )
        await self._refresh_ttl(session_id)

    async def get_session_meta(self, session_id: str) -> dict[str, Any] | None:
        data = await get_redis().hgetall(_k("chat_sessions", session_id))
        return dict(data) if data else None

    # -- context (working memory) ------------------------------------------

    async def set_context(self, session_id: str, **fields: Any) -> None:
        if not fields:
            return
        await get_redis().hset(
            _k("session_contexts", session_id),
            mapping={k: str(v) for k, v in fields.items()},
        )
        await self._refresh_ttl(session_id)

    async def get_context(self, session_id: str) -> dict[str, Any]:
        data = await get_redis().hgetall(_k("session_contexts", session_id))
        return dict(data) if data else {}

    # -- intent routes ------------------------------------------------------

    async def log_intent(
        self,
        session_id: str,
        intent: str,
        routed_to: str,
        confidence: float | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "intent": intent,
            "routed_to": routed_to,
            "confidence": confidence,
            "ts": int(time.time()),
        }
        await self._rpush_capped(session_id, "intent_routes", entry)
        await self._refresh_ttl(session_id)

    # -- service calls -------------------------------------------------------

    async def log_service_call(
        self,
        session_id: str,
        service_name: str,
        latency_ms: float,
        status: str,
    ) -> None:
        entry: dict[str, Any] = {
            "service": service_name,
            "latency_ms": latency_ms,
            "status": status,
            "ts": int(time.time()),
        }
        await self._rpush_capped(session_id, "service_calls", entry)
        await self._refresh_ttl(session_id)

    # -- conversation summary -----------------------------------------------

    async def set_summary(self, session_id: str, summary_text: str) -> None:
        await get_redis().set(
            _k("conversation_summaries", session_id),
            summary_text,
            ex=self._ttl,
        )

    async def get_summary(self, session_id: str) -> str | None:
        raw = await get_redis().get(_k("conversation_summaries", session_id))
        return raw if raw else None

    # -- feedback -----------------------------------------------------------

    async def set_feedback(
        self, session_id: str, rating: int, comment: str = ""
    ) -> None:
        await get_redis().hset(
            _k("chat_feedback", session_id),
            mapping={
                "rating": str(rating),
                "comment": comment,
                "submitted_at": str(int(time.time())),
            },
        )
        await self._refresh_ttl(session_id)

    # -- attachments --------------------------------------------------------

    async def log_attachment(
        self, session_id: str, file_key: str, file_type: str
    ) -> None:
        entry: dict[str, Any] = {
            "file_key": file_key,
            "file_type": file_type,
            "uploaded_at": int(time.time()),
        }
        await self._rpush_capped(session_id, "chat_attachments", entry)
        await self._refresh_ttl(session_id)

    # -- failed requests ----------------------------------------------------

    async def log_failure(
        self,
        session_id: str,
        error_type: str,
        message: str,
        node: str = "",
    ) -> None:
        entry: dict[str, Any] = {
            "error_type": error_type,
            "message": message,
            "node": node,
            "ts": int(time.time()),
        }
        await self._rpush_capped(session_id, "failed_requests", entry)
        await self._refresh_ttl(session_id)

    # -- model usage --------------------------------------------------------

    async def log_model_usage(
        self,
        session_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        entry: dict[str, Any] = {
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "ts": int(time.time()),
        }
        await self._rpush_capped(session_id, "model_usage_logs", entry)
        await self._refresh_ttl(session_id)


# In-memory test double

class InMemorySessionStore(SessionStore):
    """Test double: same interface, plain dicts, no TTL enforcement."""

    def __init__(self) -> None:
        self._messages: dict[str, list[dict[str, Any]]] = {}
        self._meta: dict[str, dict[str, Any]] = {}
        self._context: dict[str, dict[str, Any]] = {}
        self._intents: dict[str, list[dict[str, Any]]] = {}
        self._calls: dict[str, list[dict[str, Any]]] = {}
        self._summaries: dict[str, str] = {}
        self._feedback: dict[str, dict[str, Any]] = {}
        self._attachments: dict[str, list[dict[str, Any]]] = {}
        self._failures: dict[str, list[dict[str, Any]]] = {}
        self._usage: dict[str, list[dict[str, Any]]] = {}
        self.touched: list[str] = []

    async def get(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._messages.get(session_id, []))

    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        self._messages.setdefault(session_id, []).extend(messages)

    async def touch(self, session_id: str) -> None:
        self.touched.append(session_id)

    async def init_session(
        self,
        session_id: str,
        student_id: str,
        grade: int,
        language: str,
    ) -> None:
        self._meta[session_id] = {
            "student_id": student_id,
            "grade": grade,
            "language": language,
            "started_at": int(time.time()),
            "status": "active",
        }

    async def get_session_meta(self, session_id: str) -> dict[str, Any] | None:
        return dict(self._meta[session_id]) if session_id in self._meta else None

    async def set_context(self, session_id: str, **fields: Any) -> None:
        self._context.setdefault(session_id, {}).update(fields)

    async def get_context(self, session_id: str) -> dict[str, Any]:
        return dict(self._context.get(session_id, {}))

    async def log_intent(
        self,
        session_id: str,
        intent: str,
        routed_to: str,
        confidence: float | None = None,
    ) -> None:
        self._intents.setdefault(session_id, []).append(
            {"intent": intent, "routed_to": routed_to, "confidence": confidence}
        )

    async def log_service_call(
        self,
        session_id: str,
        service_name: str,
        latency_ms: float,
        status: str,
    ) -> None:
        self._calls.setdefault(session_id, []).append(
            {"service": service_name, "latency_ms": latency_ms, "status": status}
        )

    async def set_summary(self, session_id: str, summary_text: str) -> None:
        self._summaries[session_id] = summary_text

    async def get_summary(self, session_id: str) -> str | None:
        return self._summaries.get(session_id)

    async def set_feedback(
        self, session_id: str, rating: int, comment: str = ""
    ) -> None:
        self._feedback[session_id] = {
            "rating": rating,
            "comment": comment,
            "submitted_at": int(time.time()),
        }

    async def log_attachment(
        self, session_id: str, file_key: str, file_type: str
    ) -> None:
        self._attachments.setdefault(session_id, []).append(
            {"file_key": file_key, "file_type": file_type}
        )

    async def log_failure(
        self,
        session_id: str,
        error_type: str,
        message: str,
        node: str = "",
    ) -> None:
        self._failures.setdefault(session_id, []).append(
            {"error_type": error_type, "message": message, "node": node}
        )

    async def log_model_usage(
        self,
        session_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self._usage.setdefault(session_id, []).append(
            {
                "model_id": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
        )
