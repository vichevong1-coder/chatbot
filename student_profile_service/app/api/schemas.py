"""Pydantic schemas for the student profile API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StudentProfileResponse(BaseModel):
    student_id: str
    stars: int = Field(..., alias="stars")
    completed_problems_count: int
    mastery_levels: dict[str, float]

    class Config:
        populate_by_name = True


class AnswerAttemptRequest(BaseModel):
    student_id: str
    problem_id: str
    step_id: str
    is_correct: bool
    student_answer: str | None = "submitted answer"
    session_id: str | None = None
    misconception_code: str | None = None
    hint_rung_used: int | None = None


class HintUsageRequest(BaseModel):
    student_id: str
    problem_id: str
    step_id: str
    rung: int


class HintUsageResponse(BaseModel):
    success: bool
    remaining_stars: int
