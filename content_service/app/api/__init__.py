"""Routers: parse, delegate, serialize — no business logic (.claude/claude.md section 5)."""

from app.api.admin import admin_router
from app.api.problems import problems_router

__all__ = ["admin_router", "problems_router"]
