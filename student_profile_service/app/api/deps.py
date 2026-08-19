"""Dependencies for the student profile API."""

from __future__ import annotations

from fastapi import Request

from app.infrastructure.progress_repository import ProgressRepository


def get_repository(request: Request) -> ProgressRepository:
    """Dependency injector to obtain the ProgressRepository instance."""
    return ProgressRepository(request.app.state.session_factory)
