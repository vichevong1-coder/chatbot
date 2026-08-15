"""Public problem catalog: what the gateway proxies to the browser.

Every response goes through ``HomeworkProblem.to_public()`` — ``correct_answer`` must
never leave this service on the public surface (.claude/contracts.md section 4).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.models import (
    PublicHomeworkProblem,
    Subject,
    problem_not_found_detail,
)
from app.infrastructure.repository import ProblemRepository

problems_router = APIRouter(tags=["problems"])


def _repository(request: Request) -> ProblemRepository:
    return request.app.state.repository


# response_model_by_alias=False throughout: FastAPI would otherwise serialize through
# the camelCase aliases. Services speak snake_case on the wire; the gateway is the only
# translation boundary (.claude/claude.md section 5).


@problems_router.get(
    "/problems",
    response_model=list[PublicHomeworkProblem],
    response_model_by_alias=False,
)
async def list_problems(
    request: Request,
    grade: int | None = None,
    subject: Subject | None = None,
) -> list[PublicHomeworkProblem]:
    problems = await _repository(request).list_problems(
        grade=grade, subject=subject.value if subject else None
    )
    return [p.to_public() for p in problems]


@problems_router.get(
    "/problems/{problem_id}",
    response_model=PublicHomeworkProblem,
    response_model_by_alias=False,
)
async def get_problem(request: Request, problem_id: str) -> PublicHomeworkProblem:
    problem = await _repository(request).get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=problem_not_found_detail(problem_id))
    return problem.to_public()
