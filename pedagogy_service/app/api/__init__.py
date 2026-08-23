"""Routers for pedagogy_service."""

from app.api.explain import router as explain_router
from app.api.translate import router as translate_router

__all__ = ["explain_router", "translate_router"]
