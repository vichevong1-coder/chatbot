"""Postgres-backed session store (plan.md P2.4).

Architecture: Postgres is **authoritative**; Redis is the hot-read cache.

  get()    → Redis first; on miss, load from Postgres and re-warm Redis.
  append() → write to Postgres first, then update Redis.
  touch()  → refresh updated_at in Postgres + refresh Redis TTL.

All other namespace methods (log_intent, log_service_call, etc.) delegate to
the Redis layer only — those are ephemeral hot-path logs, not durability data.
The ``sessions`` table (dal.models.session.Session) already exists; no migration
is required.

Verify: complete a tutoring turn → kill Redis → restart the orchestrator →
confirm the transcript loads correctly from Postgres.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from dal.clients.postgres import get_session_factory
from dal.clients.redis import get_redis
from dal.models.session import Session

from app.session_store.redis_store import (
    SESSION_TTL_SECONDS,
    SessionStore,
    _k,
    _all_keys,
    _LIST_CAP,
)

import time


class PostgresSessionStore(SessionStore):
    """Write-through store: Postgres is authoritative, Redis is the hot cache.

    Tests should inject ``InMemorySessionStore`` via the DI seam in
    ``create_app()`` — this class requires a live Postgres + Redis to function.
    """

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _redis_refresh(self, session_id: str) -> None:
        """Refresh TTL on all Redis keys for this session."""
        r = get_redis()
        async with r.pipeline(transaction=False) as pipe:
            for key in _all_keys(session_id):
                pipe.expire(key, self._ttl)
            await pipe.execute()

    async def _redis_get(self, session_id: str) -> list[dict[str, Any]] | None:
        """Return transcript from Redis cache, or None on miss."""
        try:
            raw = await get_redis().lrange(_k("chat_messages", session_id), 0, -1)
            if raw:
                return [json.loads(r) for r in raw]
        except Exception:
            pass
        return None

    async def _redis_warm(
        self, session_id: str, transcript: list[dict[str, Any]]
    ) -> None:
        """Write the transcript list into Redis and set TTL."""
        try:
            r = get_redis()
            key = _k("chat_messages", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.delete(key)
                for msg in transcript:
                    pipe.rpush(key, json.dumps(msg, ensure_ascii=False))
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass  # Redis failure must never break the Postgres path

    # ------------------------------------------------------------------
    # Core transcript API
    # ------------------------------------------------------------------

    async def get(self, session_id: str) -> list[dict[str, Any]]:
        """Redis-first read; falls back to Postgres and re-warms the cache."""
        cached = await self._redis_get(session_id)
        if cached is not None:
            return cached

        # Redis miss → load from Postgres
        async with get_session_factory()() as db:
            row = await db.get(Session, session_id)
            if row is None:
                return []
            transcript: list[dict[str, Any]] = row.transcript or []

        # Re-warm Redis so the next read is fast
        if transcript:
            await self._redis_warm(session_id, transcript)

        return transcript

    async def append(self, session_id: str, *messages: dict[str, Any]) -> None:
        """Append to Postgres first, then update Redis."""
        async with get_session_factory()() as db:
            row = await db.get(Session, session_id)
            if row is None:
                # Session not yet initialised via init_session — create a bare row
                new_row = Session(
                    id=session_id,
                    student_id="anonymous",
                    language="km",
                    mode="student",
                    transcript=list(messages),
                )
                db.add(new_row)
            else:
                existing = list(row.transcript or [])
                existing.extend(messages)
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(transcript=existing)
                )
            await db.commit()

        # Mirror into Redis
        try:
            r = get_redis()
            key = _k("chat_messages", session_id)
            async with r.pipeline(transaction=True) as pipe:
                for msg in messages:
                    pipe.rpush(key, json.dumps(msg, ensure_ascii=False))
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass  # Redis failure must not roll back the Postgres write

    async def touch(self, session_id: str) -> None:
        """Refresh updated_at in Postgres + all Redis TTLs."""
        async with get_session_factory()() as db:
            await db.execute(
                update(Session)
                .where(Session.id == session_id)
                .values()  # triggers onupdate=utcnow on updated_at
            )
            await db.commit()
        await self._redis_refresh(session_id)

    # ------------------------------------------------------------------
    # Session metadata
    # ------------------------------------------------------------------

    async def init_session(
        self,
        session_id: str,
        student_id: str,
        grade: int = 4,
        language: str = "km",
    ) -> None:
        """UPSERT a session row. Safe to call multiple times."""
        stmt = (
            pg_insert(Session)
            .values(
                id=session_id,
                student_id=student_id,
                language=language,
                mode="student",
                transcript=[],
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        async with get_session_factory()() as db:
            await db.execute(stmt)
            await db.commit()

        # Also init Redis metadata hash
        try:
            await get_redis().hset(
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
            await self._redis_refresh(session_id)
        except Exception:
            pass

    async def get_session_meta(self, session_id: str) -> dict[str, Any] | None:
        """Check Redis first (fast), then fall back to Postgres row existence."""
        try:
            data = await get_redis().hgetall(_k("chat_sessions", session_id))
            if data:
                return dict(data)
        except Exception:
            pass

        # Redis miss → check Postgres
        async with get_session_factory()() as db:
            row = await db.get(Session, session_id)
            if row is None:
                return None
            return {
                "student_id": row.student_id,
                "language": row.language,
                "mode": row.mode,
                "started_at": str(row.created_at),
                "status": "active",
            }

    # ------------------------------------------------------------------
    # Summary (persisted to Postgres + Redis)
    # ------------------------------------------------------------------

    async def set_summary(self, session_id: str, summary_text: str) -> None:
        """Persist summary to Postgres and mirror to Redis."""
        async with get_session_factory()() as db:
            await db.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(summary=summary_text)
            )
            await db.commit()
        try:
            await get_redis().set(
                _k("conversation_summaries", session_id),
                summary_text,
                ex=self._ttl,
            )
        except Exception:
            pass

    async def get_summary(self, session_id: str) -> str | None:
        """Redis-first; falls back to Postgres."""
        try:
            raw = await get_redis().get(_k("conversation_summaries", session_id))
            if raw:
                return raw
        except Exception:
            pass

        async with get_session_factory()() as db:
            row = await db.get(Session, session_id)
            return row.summary if row else None

    # ------------------------------------------------------------------
    # Hot-path Redis-only methods (no-ops for Postgres durability)
    # These are ephemeral logs — intentionally not written to Postgres.
    # ------------------------------------------------------------------

    async def set_context(self, session_id: str, **fields: Any) -> None:
        try:
            if fields:
                await get_redis().hset(
                    _k("session_contexts", session_id),
                    mapping={k: str(v) for k, v in fields.items()},
                )
                await self._redis_refresh(session_id)
        except Exception:
            pass

    async def get_context(self, session_id: str) -> dict[str, Any]:
        try:
            data = await get_redis().hgetall(_k("session_contexts", session_id))
            return dict(data) if data else {}
        except Exception:
            return {}

    async def log_intent(
        self,
        session_id: str,
        intent: str,
        routed_to: str,
        confidence: float | None = None,
    ) -> None:
        try:
            entry = {
                "intent": intent,
                "routed_to": routed_to,
                "confidence": confidence,
                "ts": int(time.time()),
            }
            r = get_redis()
            key = _k("intent_routes", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.ltrim(key, -_LIST_CAP, -1)
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass

    async def log_service_call(
        self,
        session_id: str,
        service_name: str,
        latency_ms: float,
        status: str,
    ) -> None:
        try:
            entry = {
                "service": service_name,
                "latency_ms": latency_ms,
                "status": status,
                "ts": int(time.time()),
            }
            r = get_redis()
            key = _k("service_calls", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.ltrim(key, -_LIST_CAP, -1)
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass

    async def set_feedback(
        self, session_id: str, rating: int, comment: str = ""
    ) -> None:
        try:
            await get_redis().hset(
                _k("chat_feedback", session_id),
                mapping={
                    "rating": str(rating),
                    "comment": comment,
                    "submitted_at": str(int(time.time())),
                },
            )
            await self._redis_refresh(session_id)
        except Exception:
            pass

    async def log_attachment(
        self, session_id: str, file_key: str, file_type: str
    ) -> None:
        try:
            entry = {
                "file_key": file_key,
                "file_type": file_type,
                "uploaded_at": int(time.time()),
            }
            r = get_redis()
            key = _k("chat_attachments", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.ltrim(key, -_LIST_CAP, -1)
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass

    async def log_failure(
        self,
        session_id: str,
        error_type: str,
        message: str,
        node: str = "",
    ) -> None:
        try:
            entry = {
                "error_type": error_type,
                "message": message,
                "node": node,
                "ts": int(time.time()),
            }
            r = get_redis()
            key = _k("failed_requests", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.ltrim(key, -_LIST_CAP, -1)
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass

    async def log_model_usage(
        self,
        session_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        try:
            entry = {
                "model_id": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "ts": int(time.time()),
            }
            r = get_redis()
            key = _k("model_usage_logs", session_id)
            async with r.pipeline(transaction=True) as pipe:
                pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                pipe.ltrim(key, -_LIST_CAP, -1)
                pipe.expire(key, self._ttl)
                await pipe.execute()
        except Exception:
            pass
