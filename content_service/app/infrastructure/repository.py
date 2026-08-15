"""Postgres-backed problem repository.

Converts between the canonical Pydantic contract (``dal.schemas.HomeworkProblem``) and
the ORM rows (``dal.models.Problem`` + ``Step``). The hint rungs, the analogy card and
mcq ``options`` live in JSONB columns as plain dicts/lists — they are opaque authored
blobs, always read and written whole with their step (see dal/models/base.py).

The session factory is constructor-injectable so tests run against SQLite without
patching dal internals; the default is the process-wide factory from
``dal.clients.postgres``.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from dal.clients.postgres import get_session_factory
from dal.models import Problem, Step
from dal.schemas import HomeworkProblem


def _row_to_schema(row: Problem) -> HomeworkProblem:
    """Rebuild the validated contract model from ORM rows.

    Goes through ``model_validate`` on purpose: anything read back from the database is
    re-checked against the same rules that gated ingest, so a hand-edited row cannot
    quietly leak an invalid problem to callers.
    """
    return HomeworkProblem.model_validate(
        {
            "id": row.id,
            "title_khmer": row.title_khmer,
            "title_eng": row.title_eng,
            "grade": row.grade,
            "subject": row.subject,
            "problem_statement_khmer": row.problem_statement_khmer,
            "problem_statement_eng": row.problem_statement_eng,
            "image_uri": row.image_uri,
            "steps": [
                {
                    "id": s.id,
                    "step_number": s.step_number,
                    "total_steps": s.total_steps,
                    "question_khmer": s.question_khmer,
                    "question_eng": s.question_eng,
                    "input_format": s.input_format,
                    "options": s.options,
                    "correct_answer": s.correct_answer,
                    "hint1": s.hint1,
                    "hint2": s.hint2,
                    "hint3": s.hint3,
                    "explain_differently": s.explain_differently,
                }
                for s in row.steps
            ],
        }
    )


def _schema_to_step_rows(problem: HomeworkProblem) -> list[Step]:
    return [
        Step(
            id=s.id,
            problem_id=problem.id,
            step_number=s.step_number,
            total_steps=s.total_steps,
            question_khmer=s.question_khmer,
            question_eng=s.question_eng,
            input_format=s.input_format.value,
            options=s.options,
            correct_answer=s.correct_answer,
            hint1=s.hint1.model_dump(),
            hint2=s.hint2.model_dump(),
            hint3=s.hint3.model_dump(),
            explain_differently=s.explain_differently.model_dump(),
        )
        for s in problem.steps
    ]


class ProblemRepository:
    """CRUD over the problem catalog. All methods are async and open short sessions."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        # Resolved lazily so importing this module never requires DATABASE_URL.
        if self._session_factory is None:
            self._session_factory = get_session_factory()
        return self._session_factory

    async def list_problems(
        self, grade: int | None = None, subject: str | None = None
    ) -> list[HomeworkProblem]:
        stmt = (
            select(Problem).options(selectinload(Problem.steps)).order_by(Problem.id)
        )
        if grade is not None:
            stmt = stmt.where(Problem.grade == grade)
        if subject is not None:
            stmt = stmt.where(Problem.subject == subject)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
            return [_row_to_schema(r) for r in rows]

    async def get_problem(self, problem_id: str) -> HomeworkProblem | None:
        stmt = (
            select(Problem)
            .options(selectinload(Problem.steps))
            .where(Problem.id == problem_id)
        )
        async with self.session_factory() as session:
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _row_to_schema(row) if row is not None else None

    async def upsert_problem(self, problem: HomeworkProblem) -> None:
        """Insert or fully replace a problem. Steps are delete-and-reinsert: the step
        set is authored as a whole, so partial step updates are not a real operation."""
        async with self.session_factory() as session:
            async with session.begin():
                existing = await session.get(Problem, problem.id)
                if existing is not None:
                    await session.execute(
                        delete(Step).where(Step.problem_id == problem.id)
                    )
                    existing.title_khmer = problem.title_khmer
                    existing.title_eng = problem.title_eng
                    existing.grade = problem.grade
                    existing.subject = problem.subject.value
                    existing.problem_statement_khmer = problem.problem_statement_khmer
                    existing.problem_statement_eng = problem.problem_statement_eng
                    existing.image_uri = problem.image_uri
                else:
                    session.add(
                        Problem(
                            id=problem.id,
                            title_khmer=problem.title_khmer,
                            title_eng=problem.title_eng,
                            grade=problem.grade,
                            subject=problem.subject.value,
                            problem_statement_khmer=problem.problem_statement_khmer,
                            problem_statement_eng=problem.problem_statement_eng,
                            image_uri=problem.image_uri,
                        )
                    )
                await session.flush()
                session.add_all(_schema_to_step_rows(problem))

    async def delete_problem(self, problem_id: str) -> bool:
        """Delete a problem and its steps. Returns False if it did not exist."""
        async with self.session_factory() as session:
            async with session.begin():
                # Eager-load steps so the delete-orphan cascade never lazy-loads in an
                # async context, and so it works on SQLite where the FK's ON DELETE
                # CASCADE is not enforced by default.
                row = await session.get(
                    Problem, problem_id, options=[selectinload(Problem.steps)]
                )
                if row is None:
                    return False
                await session.delete(row)
                return True
