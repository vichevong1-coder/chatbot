"""Structured JSON-lines logging — the observability story (claude.md §4, §5).

Stdlib only, deliberately dependency-free: this module is meant to be lifted into
other services later, one shared format across the fleet.

Fields: ts, level, service, event, request_id, student_id, session_id, intent,
duration_ms. NEVER log the prompt, transcript text, answers, homework images, or
audio — the users are children (claude.md §5).
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
from typing import Any

# Set by the request-id middleware; carried into every log line automatically.
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_ALLOWED_EXTRA = ("request_id", "student_id", "session_id", "intent", "duration_ms")


class JsonFormatter(logging.Formatter):
    """One JSON object per line. No free-text message field beyond ``event``."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname.lower(),
            "service": self._service,
            "event": record.getMessage(),
        }
        rid = getattr(record, "request_id", None) or request_id_var.get()
        if rid is not None:
            line["request_id"] = rid
        for key in _ALLOWED_EXTRA[1:]:
            value = getattr(record, key, None)
            if value is not None:
                line[key] = value
        return json.dumps(line, ensure_ascii=False)


def get_logger(service: str = "orchestrator") -> logging.Logger:
    """Return the service logger, configured once with the JSON formatter."""
    logger = logging.getLogger(f"tunsay.{service}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter(service))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    student_id: str | None = None,
    session_id: str | None = None,
    intent: str | None = None,
    duration_ms: float | None = None,
    request_id: str | None = None,
) -> None:
    """Emit one structured event. Only whitelisted fields — never content."""
    logger.log(
        level,
        event,
        extra={
            "request_id": request_id,
            "student_id": student_id,
            "session_id": session_id,
            "intent": intent,
            "duration_ms": round(duration_ms, 1) if duration_ms is not None else None,
        },
    )
