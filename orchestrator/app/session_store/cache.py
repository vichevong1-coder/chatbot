"""Explanation cache for the orchestrator (plan.md P2.4).

Provides caching of grade-banded explanations keyed by
(problem_id, step_index, grade, misconception_code, language, mode).

Supports RedisExplanationCache (production) and InMemoryExplanationCache (tests / fallback).
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from dal.clients.redis import get_redis

DEFAULT_EXPLANATION_TTL = 3600 * 24  # 24h


def hash_explanation_key(
    problem_id: str | None,
    step_index: int | None,
    grade: int,
    misconception_code: str | None,
    language: str,
    mode: str,
) -> str:
    """Generate a deterministic hashed cache key for an explanation request."""
    raw = f"{problem_id}:{step_index}:{grade}:{misconception_code}:{language}:{mode}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"cache:explain:{digest}"


class ExplanationCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> dict[str, str] | None:
        """Return dict with text_khmer and text_eng if cached, or None."""

    @abstractmethod
    async def set(
        self,
        key: str,
        text_khmer: str,
        text_eng: str,
        ttl: int = DEFAULT_EXPLANATION_TTL,
    ) -> None:
        """Cache explanation text."""


class InMemoryExplanationCache(ExplanationCache):
    """In-memory cache for tests and fallback."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[dict[str, str], float | None]] = {}

    async def get(self, key: str) -> dict[str, str] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        payload, expire_at = entry
        if expire_at is not None and time.time() > expire_at:
            del self._store[key]
            return None
        return dict(payload)

    async def set(
        self,
        key: str,
        text_khmer: str,
        text_eng: str,
        ttl: int = DEFAULT_EXPLANATION_TTL,
    ) -> None:
        expire_at = time.time() + ttl if ttl > 0 else None
        self._store[key] = (
            {"text_khmer": text_khmer, "text_eng": text_eng},
            expire_at,
        )

    def clear(self) -> None:
        self._store.clear()


class RedisExplanationCache(ExplanationCache):
    """Production explanation cache over dal.clients.redis."""

    def __init__(self, default_ttl: int = DEFAULT_EXPLANATION_TTL) -> None:
        self.default_ttl = default_ttl

    async def get(self, key: str) -> dict[str, str] | None:
        try:
            raw = await get_redis().get(key)
            if not raw:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def set(
        self,
        key: str,
        text_khmer: str,
        text_eng: str,
        ttl: int | None = None,
    ) -> None:
        try:
            payload = json.dumps(
                {"text_khmer": text_khmer, "text_eng": text_eng},
                ensure_ascii=False,
            )
            await get_redis().set(
                key,
                payload,
                ex=ttl if ttl is not None else self.default_ttl,
            )
        except Exception:
            pass


_active_cache: ExplanationCache = InMemoryExplanationCache()


def get_cache() -> ExplanationCache:
    return _active_cache


def set_cache(cache_instance: ExplanationCache) -> None:
    global _active_cache
    _active_cache = cache_instance


def reset_cache() -> None:
    global _active_cache
    _active_cache = InMemoryExplanationCache()


async def get(key: str) -> dict[str, str] | None:
    return await _active_cache.get(key)


async def set(
    key: str,
    text_khmer: str,
    text_eng: str,
    ttl: int = DEFAULT_EXPLANATION_TTL,
) -> None:
    await _active_cache.set(key, text_khmer=text_khmer, text_eng=text_eng, ttl=ttl)
