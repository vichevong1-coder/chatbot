"""Test fixtures for student_profile_service."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

# Make `import app` resolve to student_profile_service/app regardless of pytest root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dal.models.base import Base
from dal.models.user import User
from dal.models.problem import Problem
from dal.models.step import Step

from app.main import create_app


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):  # noqa: ANN001, ANN003, ANN202
    """Render postgres JSONB columns as JSON when creating tables on SQLite."""
    return "JSON"


@pytest.fixture()
def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed initial test data
        async with factory() as session:
            student = User(
                id="test-student-id",
                student_name="Sokha",
                language="km",
                grade=4,
            )
            problem = Problem(
                id="math-g4-apples",
                title_khmer="ចំណោទគណិតវិទ្យា៖ ការគុណ",
                title_eng="Math Problem: Multiplication",
                grade=4,
                subject="math",
                problem_statement_khmer="មាន ៥ ប្រអប់។",
                problem_statement_eng="There are 5 boxes.",
            )
            step = Step(
                id="step-1",
                problem_id="math-g4-apples",
                step_number=1,
                total_steps=1,
                question_khmer="តើមានប្រអប់ចំនួនប៉ុន្មាន?",
                question_eng="How many boxes are there?",
                input_format="number",
                correct_answer="5",
                hint1={},
                hint2={},
                hint3={},
                explain_differently={},
            )
            session.add(student)
            session.add(problem)
            session.add(step)
            await session.commit()

    asyncio.run(_setup())
    yield factory
    asyncio.run(engine.dispose())


@pytest.fixture()
def client(session_factory):
    app = create_app(session_factory=session_factory)
    with TestClient(app) as test_client:
        yield test_client
