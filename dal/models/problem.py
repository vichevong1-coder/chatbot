"""Homework problems."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dal.models.base import Base, TimestampMixin


class Problem(Base, TimestampMixin):
    """``id`` is the authored slug ("math-g4-apples"), not a surrogate key — it is stable,
    human-readable, and already referenced by the seed files and the frontend."""

    __tablename__ = "problems"
    __table_args__ = (Index("ix_problems_grade_subject", "grade", "subject"),)

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title_khmer: Mapped[str] = mapped_column(String(512), nullable=False)
    title_eng: Mapped[str] = mapped_column(String(512), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(16), nullable=False)
    problem_statement_khmer: Mapped[str] = mapped_column(String, nullable=False)
    problem_statement_eng: Mapped[str] = mapped_column(String, nullable=False)
    image_uri: Mapped[str | None] = mapped_column(String(1024))

    steps: Mapped[list["Step"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="Step.step_number",
    )
