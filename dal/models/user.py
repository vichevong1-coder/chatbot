"""Users and schools.

No email, no password. Identity is (school_code, student_name) plus an optional 4-digit
PIN — see .claude/contracts.md section 4.

**Every user is a student.** There is deliberately no ``role`` column, no account types and
no parent_student_link table: the frontend has no account-type picker and never sends one.
The student/parent split in the UI is :class:`~dal.schemas.enums.UserMode`, an in-app
toggle on the child's own session, not an identity.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dal.models.base import Base, TimestampMixin


class School(Base, TimestampMixin):
    """What a school code resolves to.

    Deliberately flat, not a school -> class -> student hierarchy: real multi-tenancy is
    deferred (.claude/claude.md section 4), but LoginView.tsx already depends on school
    codes and class names, so they need somewhere to live now.
    """

    __tablename__ = "schools"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    class_name: Mapped[str | None] = mapped_column(String(64))
    grade: Mapped[int | None] = mapped_column(Integer)
    subject_track: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="school")


class User(Base, TimestampMixin):
    """A student. There is no other kind of account.

    ``student_name`` is a Khmer display string ("សុជា (Sochea)") and is **not** globally
    unique — two children at different schools may share one. Uniqueness is scoped to the
    school code, which is why there is no unique index on the name alone.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("school_code", "student_name", name="school_code_student_name"),
        Index("ix_users_student_name", "student_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    school_code: Mapped[str | None] = mapped_column(
        ForeignKey("schools.code", ondelete="SET NULL")
    )
    class_name: Mapped[str | None] = mapped_column(String(64))
    grade: Mapped[int | None] = mapped_column(Integer)
    parent_contact: Mapped[str | None] = mapped_column(String(255))
    pin_hash: Mapped[str | None] = mapped_column(String(255))
    """Nullable: the PIN is optional in the school-code flow, where a shared classroom
    device makes the school code itself the credential."""
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="km")

    school: Mapped["School | None"] = relationship(back_populates="users")
