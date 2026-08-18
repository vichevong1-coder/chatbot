"""Fakes + app fixture for orchestrator tests.

Every service client is faked and injected through ``create_app``; sessions live
in an InMemorySessionStore. No network, no Redis, no LLM.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from app.infrastructure.service_clients import (  # noqa: E402
    ServiceClients,
    ServiceUnavailable,
    SolverUnparseable,
)
from app.main import create_app  # noqa: E402
from app.session_store.redis_store import InMemorySessionStore  # noqa: E402

REFUSAL_KHMER = "ទន្សាយមិនអាចជួយរឿងនោះបានទេ។ 🐰"
REFUSAL_ENG = "Tunsay can't help with that. 🐰"

PEDAGOGY_KHMER = "តោះគិតជំហានទីមួយជាមួយគ្នា! 🐰"
PEDAGOGY_ENG = "Let's think about the first step together! 🐰"


class FakeSafetyClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.unsafe = False
        self.down = False

    async def check(self, text: str, language: str, direction: str = "input") -> dict:
        if self.down:
            raise ServiceUnavailable("safety_service", "connection refused")
        self.calls.append({"text": text, "language": language, "direction": direction})
        if self.unsafe:
            return {
                "is_safe": False,
                "reason": "violence",
                "refusal_khmer": REFUSAL_KHMER,
                "refusal_eng": REFUSAL_ENG,
            }
        return {"is_safe": True, "reason": None, "refusal_khmer": "", "refusal_eng": ""}


class FakeSolverClient:
    ANSWERS = {
        "5*8": ("40", ["5 * 8 = 40"]),
        "25% of 80": ("20", ["25% of 80 = 20"]),
    }

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.down = False

    async def solve(self, expression: str) -> dict:
        if self.down:
            raise ServiceUnavailable("solver_service", "connection refused")
        self.calls.append(expression)
        if expression not in self.ANSWERS:
            raise SolverUnparseable(expression)
        answer, steps = self.ANSWERS[expression]
        return {"expression": expression, "answer": answer, "steps": steps}


class FakeContentClient:
    def __init__(self, problems: dict[str, dict] | None = None) -> None:
        self.calls: list[str] = []
        self.down = False
        self.problems = problems or {}

    async def get_problem(self, problem_id: str) -> dict | None:
        if self.down:
            raise ServiceUnavailable("content_service", "connection refused")
        self.calls.append(problem_id)
        return self.problems.get(problem_id)


class FakePedagogyClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.down = False

    async def explain(self, *, prompt, grade, language, mode, context=None, misconception_code=None) -> dict:
        if self.down:
            raise ServiceUnavailable("pedagogy_service", "connection refused")
        self.calls.append(
            {
                "prompt": prompt,
                "grade": grade,
                "language": language,
                "mode": mode,
                "context": context,
                "misconception_code": misconception_code,
            }
        )
        if language == "km":
            return {"text_khmer": PEDAGOGY_KHMER, "text_eng": "", "from_fallback": False}
        return {"text_khmer": "", "text_eng": PEDAGOGY_ENG, "from_fallback": False}


class FakeAuthClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_me(self, token: str) -> dict:
        self.calls.append(token)
        return {"name": "សុជា (Sochea)", "grade": 4}


class FakeGradingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.down = False

    async def grade(
        self,
        correct_answer: str,
        student_answer: str,
        input_format: str = "number",
        options: list[str] | None = None,
        language: str = "km",
        question_text: str = ""
    ) -> dict:
        if self.down:
            raise ServiceUnavailable("grading_service", "connection refused")
        self.calls.append({
            "correct_answer": correct_answer,
            "student_answer": student_answer,
            "input_format": input_format,
            "options": options,
            "language": language,
            "question_text": question_text
        })
        is_correct = student_answer.strip() == correct_answer.strip()
        misconception_code = None
        if not is_correct:
            misconception_code = "calculation_error"
        return {"is_correct": is_correct, "misconception_code": misconception_code}


class FakeProfileClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.down = False

    async def get_profile(self, student_id: str) -> dict[str, Any]:
        if self.down:
            raise ServiceUnavailable("student_profile_service", "connection refused")
        self.calls.append({"student_id": student_id})
        return {"stars": 10, "completed_problems": []}

    async def record_attempt(
        self,
        *,
        student_id: str,
        problem_id: str,
        step_id: str,
        is_correct: bool,
    ) -> dict[str, Any]:
        if self.down:
            raise ServiceUnavailable("student_profile_service", "connection refused")
        self.calls.append({
            "student_id": student_id,
            "problem_id": problem_id,
            "step_id": step_id,
            "is_correct": is_correct,
        })
        return {"status": "recorded"}


# Public problem shape — correct_answer already stripped by content_service.
APPLES_PROBLEM = {
    "id": "math-g4-apples",
    "title_khmer": "ចែកផ្លែប៉ោម",
    "title_eng": "Sharing Apples",
    "grade": 4,
    "subject": "math",
    "problem_statement_khmer": "មានផ្លែប៉ោម ២៤ ផ្លែ ចែកឱ្យក្មេង ៦ នាក់។",
    "problem_statement_eng": "There are 24 apples shared among 6 children.",
    "image_uri": None,
    "steps": [
        {
            "id": "apples-step-1",
            "step_number": 1,
            "total_steps": 2,
            "question_khmer": "តើត្រូវប្រើប្រមាណវិធីអ្វី?",
            "question_eng": "Which operation should we use?",
            "input_format": "mcq",
            "options": ["+", "-", "*", "/"],
        }
    ],
}


@pytest.fixture
def fakes() -> ServiceClients:
    return ServiceClients(
        safety=FakeSafetyClient(),
        solver=FakeSolverClient(),
        content=FakeContentClient({"math-g4-apples": APPLES_PROBLEM}),
        pedagogy=FakePedagogyClient(),
        auth=FakeAuthClient(),
        grading=FakeGradingClient(),
        profile=FakeProfileClient(),
    )


@pytest.fixture
def store() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture
def client(fakes: ServiceClients, store: InMemorySessionStore) -> TestClient:
    app = create_app(clients=fakes, session_store=store)
    with TestClient(app) as test_client:
        yield test_client


def post_chat(client: TestClient, prompt: str, **overrides: Any):
    body = {
        "session_id": "sess-1",
        "student_id": "stu-1",
        "prompt": prompt,
        "mode": "student",
        "language": "km",
        "problem_id": None,
        "active_step_index": None,
    }
    body.update(overrides)
    return client.post("/chat", json=body)


def post_answer(client: TestClient, student_answer: str, **overrides: Any):
    body = {
        "session_id": "sess-1",
        "student_id": "stu-1",
        "problem_id": "math-g4-apples",
        "step_id": "apples-step-1",
        "student_answer": student_answer,
        "language": "km",
    }
    body.update(overrides)
    return client.post("/answers", json=body)
