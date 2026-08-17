"""POST /answers — server-side answer checking router (contracts.md §4)."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from dal.schemas import AnswerRequest, AnswerResponse, ChatMessage

from app.utils.logging import get_logger, log_event

router = APIRouter()
logger = get_logger("orchestrator")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _message(sender: str, *, text_khmer: str, text_eng: str, **flags: Any) -> dict:
    return ChatMessage(
        id=str(uuid.uuid4()),
        sender=sender,
        text_khmer=text_khmer,
        text_eng=text_eng,
        timestamp=_now_iso(),
        **flags,
    ).model_dump(mode="json")


@router.post("/answers", response_model=AnswerResponse, response_model_by_alias=False)
async def check_answer(request: Request, body: AnswerRequest) -> AnswerResponse:
    started = time.perf_counter()
    store = request.app.state.session_store
    graph = request.app.state.graph
    clients = request.app.state.clients

    # 1. Fetch transcript from Redis
    transcript = await store.get(body.session_id)

    # 2. Fetch the problem to find the active_step_index corresponding to body.step_id
    try:
        problem = await clients.content.get_problem(body.problem_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch problem from content service: {str(exc)}"
        )

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {body.problem_id} not found")

    steps = problem.get("steps") or []
    active_step_index = 0
    found = False
    for idx, step in enumerate(steps):
        if step.get("id") == body.step_id:
            active_step_index = idx
            found = True
            break

    if not found:
        raise HTTPException(
            status_code=404,
            detail=f"Step {body.step_id} not found in problem {body.problem_id}"
        )

    # 3. Invoke the LangGraph state machine with intent="check_answer"
    state: dict[str, Any] = {
        "student_id": body.student_id or "anonymous",
        "session_id": body.session_id,
        "language": body.language.value,
        "mode": "student",  # grading is always done in student mode
        "problem_id": body.problem_id,
        "active_step_index": active_step_index,
        "prompt": body.student_answer,
        "transcript": transcript,
        "intent": "check_answer",
    }
    result = await graph.ainvoke(state)

    is_correct = result.get("is_correct", False)
    response = AnswerResponse(
        is_correct=is_correct,
        misconception_code=result.get("misconception_code"),
        feedback_khmer=result.get("text_khmer", ""),
        feedback_eng=result.get("text_eng", ""),
        advance_to_step=result.get("active_step_index") if is_correct else active_step_index
    )

    # 4. Save the turn in the transcript
    is_khmer = body.language.value == "km"
    await store.append(
        body.session_id,
        _message(
            "user",
            text_khmer=body.student_answer if is_khmer else "",
            text_eng="" if is_khmer else body.student_answer,
        ),
        _message(
            "sayo",
            text_khmer=response.feedback_khmer,
            text_eng=response.feedback_eng,
            active_step_index=response.advance_to_step
        ),
    )

    log_event(
        logger,
        "answer_check",
        student_id=body.student_id or "anonymous",
        session_id=body.session_id,
        problem_id=body.problem_id,
        step_id=body.step_id,
        is_correct=is_correct,
        duration_ms=(time.perf_counter() - started) * 1000,
    )

    return response
