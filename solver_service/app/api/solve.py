"""POST /solve router: parse, delegate to core, serialize. No business logic."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.math_solver import SolverError, solve
from app.core.step_formatter import format_steps

router = APIRouter()


class SolveRequest(BaseModel):
    expression: str = Field(..., description="Arithmetic expression, e.g. '5*8' or '១/២ + ១/៤'")


class SolveResponse(BaseModel):
    expression: str
    answer: str  # always a string, matching the product's correct_answer convention
    steps: list[str]


@router.post("/solve", response_model=SolveResponse)
async def solve_expression(request: SolveRequest) -> SolveResponse:
    try:
        result = solve(request.expression)
    except SolverError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": str(exc), "expression": request.expression},
        ) from exc
    return SolveResponse(
        expression=result.expression,
        answer=result.answer,
        steps=format_steps(result),
    )
