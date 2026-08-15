"""HS256 JWT issue/verify.

Claims: ``sub`` (user id), ``student_name``, ``school_code``, ``grade``, ``iat``, ``exp``.
There is no ``role`` claim — every account is a student (.claude/contracts.md section 4).

Configuration comes from the environment (see .env.example):
``JWT_SECRET`` (required), ``JWT_ALGORITHM`` (default HS256), ``JWT_EXPIRE_MINUTES``
(default 60). Read at call time, not import time, so tests can set them per-run.

Pure module: no FastAPI imports; callers map :class:`TokenError` to HTTP 401.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


class TokenError(Exception):
    """The token is missing, malformed, tampered with, or expired."""


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET is not set (see .env.example)")
    return secret


def _algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256").strip() or "HS256"


def expire_minutes() -> int:
    raw = os.environ.get("JWT_EXPIRE_MINUTES", "").strip()
    return int(raw) if raw else 60


def issue_token(
    *,
    user_id: str,
    student_name: str,
    school_code: str | None,
    grade: int | None,
) -> tuple[str, int]:
    """Return ``(encoded_token, expires_in_seconds)``."""
    expires_in = expire_minutes() * 60
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "student_name": student_name,
        "school_code": school_code,
        "grade": grade,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, _secret(), algorithm=_algorithm()), expires_in


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify; raises :class:`TokenError` on any failure (incl. expiry)."""
    try:
        return jwt.decode(token, _secret(), algorithms=[_algorithm()])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid token") from exc
