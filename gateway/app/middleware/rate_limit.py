"""Per-student rate limiting on the LLM-cost-heavy paths only (``/chat*``).

Keyed by the VERIFIED ``student_id`` (set by auth_verify from the JWT ``sub``,
never from the body); unauthenticated requests fall back to client IP.
``/problems`` and ``/auth`` are deliberately not limited (.claude/contracts.md
section 4).

Fixed-window counters in process memory with an injectable clock for tests.

TODO(redis): move the counters to Redis (REDIS_URL, per .env.example) so
limits survive gateway restarts and hold across replicas. The in-process
store is correct for a single gateway container, which is the compose story.
"""

from __future__ import annotations

import math
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import errors


class RateLimiter:
    """Fixed-window counter: at most ``limit`` hits per ``window_seconds``."""

    def __init__(
        self,
        limit: int = 20,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> tuple[bool, int]:
        """Record a hit for ``key``; return ``(allowed, retry_after_seconds)``."""
        now = self._clock()
        window_start, count = self._buckets.get(key, (now, 0))
        if now - window_start >= self._window:
            window_start, count = now, 0
        count += 1
        self._buckets[key] = (window_start, count)
        if count > self._limit:
            retry_after = max(1, math.ceil(self._window - (now - window_start)))
            return False, retry_after
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter) -> None:
        super().__init__(app)
        self._limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS" or not request.url.path.startswith("/chat"):
            return await call_next(request)

        key = getattr(request.state, "student_id", None)
        if not key:
            key = f"ip:{request.client.host if request.client else 'unknown'}"

        allowed, retry_after = self._limiter.check(key)
        if not allowed:
            return errors.rate_limited_response(retry_after)
        return await call_next(request)
