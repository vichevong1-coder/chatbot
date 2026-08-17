from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.checker import check_answer
from app.core.misconception_classifier import classify_misconception

router = APIRouter(tags=["grade"])

class GradeRequest(BaseModel):
    correct_answer: str
    student_answer: str
    input_format: str = "number"  # "mcq" | "number" | "text"
    options: list[str] | None = None
    language: str = "km"
    question_text: str = ""

class GradeResponse(BaseModel):
    is_correct: bool
    misconception_code: str | None = None

@router.post("/grade", response_model=GradeResponse)
async def grade_answer(body: GradeRequest) -> GradeResponse:
    is_correct = check_answer(
        student_answer=body.student_answer,
        correct_answer=body.correct_answer,
        input_format=body.input_format,
        options=body.options,
        language=body.language
    )
    
    misconception_code = None
    if not is_correct:
        misconception_code = classify_misconception(
            student_answer=body.student_answer,
            correct_answer=body.correct_answer,
            input_format=body.input_format,
            question_text=body.question_text
        )
        
    return GradeResponse(
        is_correct=is_correct,
        misconception_code=misconception_code
    )
