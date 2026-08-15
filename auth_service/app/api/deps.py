"""FastAPI dependencies.

The session factory and throttle live on ``app.state`` (set by ``create_app``), so tests
inject a SQLite factory / fresh throttle simply by building their own app instance.
"""

from __future__ import annotations

from fastapi import Request

from app.core.throttle import AttemptThrottle
from app.infrastructure.repository import AuthRepository


def get_repository(request: Request) -> AuthRepository:
    return AuthRepository(request.app.state.session_factory)


def get_throttle(request: Request) -> AttemptThrottle:
    return request.app.state.throttle
