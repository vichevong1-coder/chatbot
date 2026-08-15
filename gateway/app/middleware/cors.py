"""CORS: allow exactly one origin — ``FRONTEND_ORIGIN`` (.claude/plan.md P1.9).

Outermost middleware so even 401/429 responses carry CORS headers for the
legitimate origin, and preflights from anywhere else get no allow-origin at all.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.settings import Settings


def add_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
