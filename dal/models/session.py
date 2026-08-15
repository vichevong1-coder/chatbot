"""Conversation sessions.

Redis is the hot store for an in-flight conversation; this table is the durable record
that survives a restart and backs the summariser (.claude/architecture.md section 2).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dal.models.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """One tutoring conversation.

    ``transcript`` holds ChatMessage dicts. It is children's data: never log it, and
    apply a retention policy before any pilot (.claude/plan.md P4.3).
    """

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_student_updated", "student_id", "updated_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[str | None] = mapped_column(String(128))
    active_step_index: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="km")
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    transcript: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    summary: Mapped[str | None] = mapped_column(String)
