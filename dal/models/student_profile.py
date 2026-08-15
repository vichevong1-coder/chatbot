"""Mastery and progress.

Replaces the useState in App.tsx, where stars and completed-problem counts vanish on
refresh (.claude/contracts.md section 5).
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from dal.models.base import Base, TimestampMixin


class StudentProfile(Base, TimestampMixin):
    """Aggregate counters the ProfileView renders."""

    __tablename__ = "student_profiles"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    completed_problems_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    stars_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SkillMastery(Base, TimestampMixin):
    """Mastery per (subject, grade, skill).

    ``skill`` is a coarse tag ("multiplication", "fractions") rather than a per-problem
    key, so mastery generalises to problems the child has not seen — which is the whole
    point of recommend_next.
    """

    __tablename__ = "skill_mastery"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject", "grade", "skill", name="student_subject_grade_skill"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(16), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    skill: Mapped[str] = mapped_column(String(64), nullable=False)
    mastery: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
