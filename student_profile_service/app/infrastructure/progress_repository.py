"""Database access repository for student progress and attempts."""

from __future__ import annotations

from typing import Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dal.clients.postgres import get_session_factory
from dal.models.attempt import Attempt
from dal.models.student_profile import SkillMastery, StudentProfile


class ProgressRepository:
    """Handles persistence of stars, completed problems, and skill masteries."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory

    @property
    def _factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory or get_session_factory()

    async def get_or_create_profile(self, student_id: str) -> StudentProfile:
        """Fetch student profile, creating it with zero values if missing."""
        async with self._factory() as session:
            profile = await session.get(StudentProfile, student_id)
            if not profile:
                profile = StudentProfile(
                    student_id=student_id,
                    completed_problems_count=0,
                    stars_earned=0,
                )
                session.add(profile)
                await session.commit()
                # Retrieve fully initialized record
                profile = await session.get(StudentProfile, student_id)
            return profile

    async def get_skill_masteries(self, student_id: str) -> Sequence[SkillMastery]:
        """Fetch all skill masteries for a student."""
        async with self._factory() as session:
            stmt = select(SkillMastery).where(SkillMastery.student_id == student_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_or_create_mastery(
        self,
        *,
        student_id: str,
        subject: str,
        grade: int,
        skill: str,
    ) -> SkillMastery:
        """Fetch or create a skill mastery record for a student."""
        async with self._factory() as session:
            stmt = select(SkillMastery).where(
                SkillMastery.student_id == student_id,
                SkillMastery.subject == subject,
                SkillMastery.grade == grade,
                SkillMastery.skill == skill,
            )
            result = await session.execute(stmt)
            mastery = result.scalar_one_or_none()

            if not mastery:
                mastery = SkillMastery(
                    id=str(uuid4()),
                    student_id=student_id,
                    subject=subject,
                    grade=grade,
                    skill=skill,
                    mastery=0.0,
                    attempts=0,
                    correct=0,
                )
                session.add(mastery)
                await session.commit()
                # Retrieve fully initialized record
                mastery = await session.get(SkillMastery, mastery.id)
            return mastery

    async def update_mastery(
        self,
        mastery_id: str,
        *,
        mastery: float,
        is_correct: bool,
    ) -> None:
        """Update skill mastery levels and attempts counts."""
        async with self._factory() as session:
            record = await session.get(SkillMastery, mastery_id)
            if record:
                record.mastery = mastery
                record.attempts += 1
                if is_correct:
                    record.correct += 1
                await session.commit()

    async def get_step_attempt_count(
        self,
        *,
        student_id: str,
        problem_id: str,
        step_id: str,
    ) -> int:
        """Count the number of attempts a student has made on a specific step."""
        async with self._factory() as session:
            stmt = select(func.count(Attempt.id)).where(
                Attempt.student_id == student_id,
                Attempt.problem_id == problem_id,
                Attempt.step_id == step_id,
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def record_attempt(
        self,
        *,
        student_id: str,
        session_id: str | None,
        problem_id: str,
        step_id: str,
        student_answer: str,
        is_correct: bool,
        misconception_code: str | None = None,
        hint_rung_used: int | None = None,
        attempt_number: int,
    ) -> Attempt:
        """Log a new answer submission attempt."""
        async with self._factory() as session:
            attempt = Attempt(
                id=str(uuid4()),
                student_id=student_id,
                session_id=session_id,
                problem_id=problem_id,
                step_id=step_id,
                student_answer=student_answer,
                is_correct=is_correct,
                misconception_code=misconception_code,
                hint_rung_used=hint_rung_used,
                attempt_number=attempt_number,
            )
            session.add(attempt)
            await session.commit()
            return attempt

    async def add_stars(self, student_id: str, count: int) -> None:
        """Add (or deduct, if count is negative) stars for a student profile."""
        async with self._factory() as session:
            profile = await session.get(StudentProfile, student_id)
            if not profile:
                profile = StudentProfile(
                    student_id=student_id,
                    completed_problems_count=0,
                    stars_earned=0,
                )
                session.add(profile)
            profile.stars_earned = max(0, profile.stars_earned + count)
            await session.commit()

    async def increment_completed_problems(self, student_id: str) -> None:
        """Increment the completed problem count for a student profile."""
        async with self._factory() as session:
            profile = await session.get(StudentProfile, student_id)
            if not profile:
                profile = StudentProfile(
                    student_id=student_id,
                    completed_problems_count=0,
                    stars_earned=0,
                )
                session.add(profile)
            profile.completed_problems_count += 1
            await session.commit()
