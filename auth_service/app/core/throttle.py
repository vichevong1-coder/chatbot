"""Per-identity auth attempt throttling.

A 4-digit PIN is 10,000 combinations, so the throttle — not the hash — is the real
defence (.claude/contracts.md section 4). Failures are counted per
``(school_code, student_name)``; after ``max_failures`` consecutive wrong PINs the
identity is locked for ``lockout_seconds`` and login returns a structured 429.

TODO(redis): this store is in-process only. It resets on restart and is not shared
across replicas — move the counters to Redis (``dal.clients.redis``) before running
more than one auth_service instance.

Pure module: no FastAPI imports; the clock is injectable for tests.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

ThrottleKey = tuple[str, str]  # (school_code or "", student_name or "")


@dataclass
class _Entry:
    failures: int = 0
    locked_until: float | None = None


@dataclass
class AttemptThrottle:
    """Consecutive-failure lockout: 5 wrong PINs -> locked 15 minutes."""

    max_failures: int = 5
    lockout_seconds: float = 15 * 60
    now: Callable[[], float] = time.monotonic
    _entries: dict[ThrottleKey, _Entry] = field(default_factory=dict)

    def retry_after(self, key: ThrottleKey) -> int | None:
        """Seconds until this identity may try again, or ``None`` if not locked."""
        entry = self._entries.get(key)
        if entry is None or entry.locked_until is None:
            return None
        remaining = entry.locked_until - self.now()
        if remaining <= 0:
            # Lockout served; start fresh.
            del self._entries[key]
            return None
        return math.ceil(remaining)

    def record_failure(self, key: ThrottleKey) -> None:
        entry = self._entries.setdefault(key, _Entry())
        entry.failures += 1
        if entry.failures >= self.max_failures:
            entry.locked_until = self.now() + self.lockout_seconds

    def record_success(self, key: ThrottleKey) -> None:
        self._entries.pop(key, None)

    def reset(self) -> None:
        """Test helper: forget every counter."""
        self._entries.clear()
