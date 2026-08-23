"""Admin CRUD — internal compose network ONLY, deliberately unauthenticated.

Decided in .claude/contracts.md section 4 ("Admin is not on the gateway"): there is one
role (student), so no admin credential exists; instead this surface is simply never
reachable from outside Docker (`expose:` in compose, never `ports:`, and no gateway
route). Do not add auth here and do not route it through the gateway.

Unlike the public router, admin responses carry the FULL problem including
``correct_answer`` — operators need to see what they authored.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.models import HomeworkProblem, problem_not_found_detail
from app.infrastructure.repository import ProblemRepository

admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _repository(request: Request) -> ProblemRepository:
    return request.app.state.repository


# response_model_by_alias=False: snake_case on the wire between services, camelCase
# only at the gateway (.claude/claude.md section 5).


@admin_router.post(
    "/problems", response_model=HomeworkProblem, response_model_by_alias=False
)
async def upsert_problem(request: Request, problem: HomeworkProblem) -> HomeworkProblem:
    """Insert or fully replace a problem.

    The body is validated by the dal schema (bilingual fields, mcq options,
    total_steps == len(steps)) before it touches the database — an invalid problem
    is a 422, same rules as seed ingest.
    """
    await _repository(request).upsert_problem(problem)
    return problem


@admin_router.get(
    "/problems/{problem_id}",
    response_model=HomeworkProblem,
    response_model_by_alias=False,
)
async def get_problem_full(request: Request, problem_id: str) -> HomeworkProblem:
    problem = await _repository(request).get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=problem_not_found_detail(problem_id))
    return problem


from fastapi import Response

@admin_router.delete("/problems/{problem_id}", status_code=204)
async def delete_problem(request: Request, problem_id: str) -> Response:
    deleted = await _repository(request).delete_problem(problem_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=problem_not_found_detail(problem_id))
    return Response(status_code=204)
