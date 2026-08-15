"""Problem steps, with their authored scaffolding."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dal.models.base import Base, TimestampMixin


class Step(Base, TimestampMixin):
    """One step of a problem.

    The hint rungs and the analogy card are JSONB: opaque authored blobs, always read and
    written whole with the step (see dal/models/base.py). ``options`` is JSONB for the
    same reason. ``correct_answer`` is a string even for numeric steps — "40", never 40 —
    because grading normalises at compare time and the stored form stays as authored.
    """

    __tablename__ = "steps"
    __table_args__ = (
        UniqueConstraint("problem_id", "step_number", name="problem_id_step_number"),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    question_khmer: Mapped[str] = mapped_column(String, nullable=False)
    question_eng: Mapped[str] = mapped_column(String, nullable=False)
    input_format: Mapped[str] = mapped_column(String(16), nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSONB)
    correct_answer: Mapped[str] = mapped_column(String(512), nullable=False)
    hint1: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    hint2: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    hint3: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    explain_differently: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    problem: Mapped["Problem"] = relationship(back_populates="steps")
