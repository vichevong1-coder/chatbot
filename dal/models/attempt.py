"""Answer attempts and hint usage — the raw event stream behind mastery modelling."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from dal.models.base import Base, TimestampMixin


class Attempt(Base, TimestampMixin):
    """One answer submission.

    ``hint_rung_used`` matters as much as correctness: reaching rung 3 before attempting
    anything is a different signal from rung 1 after two tries (.claude/plan.md P2.3).

    ``student_answer`` is a child's own words and counts as children's data — it must
    never reach the logs (.claude/claude.md section 5).
    """

    __tablename__ = "attempts"
    __table_args__ = (
        Index("ix_attempts_student_created", "student_id", "created_at"),
        Index("ix_attempts_misconception", "misconception_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[str | None] = mapped_column(String(64))
    problem_id: Mapped[str] = mapped_column(String(128), nullable=False)
    step_id: Mapped[str] = mapped_column(String(128), nullable=False)
    student_answer: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    misconception_code: Mapped[str | None] = mapped_column(String(64))
    hint_rung_used: Mapped[int | None] = mapped_column(Integer)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
