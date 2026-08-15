"""DB access for auth: users and schools.

Uses the shared ``dal`` ORM models and, by default, the process-wide async session
factory from ``dal.clients.postgres``. The factory is constructor-injectable so tests
can hand in a SQLite (aiosqlite) factory instead — nothing here is Postgres-specific.

Duplicate detection leans on the DB's UNIQUE(school_code, student_name) constraint
rather than a check-then-insert race.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dal.clients.postgres import get_session_factory
from dal.models.user import School, User


class DuplicateStudentError(Exception):
    """(school_code, student_name) already registered."""


class AuthRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory

    @property
    def _factory(self) -> async_sessionmaker[AsyncSession]:
        # Lazy: importing/instantiating never requires DATABASE_URL; only a query does.
        return self._session_factory or get_session_factory()

    async def get_school(self, code: str) -> School | None:
        async with self._factory() as session:
            return await session.get(School, code)

    async def create_user(
        self,
        *,
        student_name: str,
        school_code: str | None,
        class_name: str | None,
        grade: int | None,
        parent_contact: str | None,
        pin_hash: str | None,
        language: str,
    ) -> User:
        user = User(
            id=str(uuid4()),
            student_name=student_name,
            school_code=school_code,
            class_name=class_name,
            grade=grade,
            parent_contact=parent_contact,
            pin_hash=pin_hash,
            language=language,
        )
        async with self._factory() as session:
            session.add(user)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise DuplicateStudentError(
                    "student already registered at this school"
                ) from exc
            return user

    async def find_users(
        self, *, student_name: str | None = None, school_code: str | None = None
    ) -> list[User]:
        """Users matching the identifiers given (returning-login accepts either).

        Capped at 2 rows: callers only need "exactly one match" vs "not exactly one".
        """
        stmt = select(User)
        if student_name is not None:
            stmt = stmt.where(User.student_name == student_name)
        if school_code is not None:
            stmt = stmt.where(User.school_code == school_code)
        async with self._factory() as session:
            result = await session.execute(stmt.limit(2))
            return list(result.scalars())

    async def get_user_by_id(self, user_id: str) -> User | None:
        async with self._factory() as session:
            return await session.get(User, user_id)
