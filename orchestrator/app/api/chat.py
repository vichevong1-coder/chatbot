"""POST /chat — the core loop (contracts.md §4).

Router only: parse the dal ChatRequest, run the compiled graph, persist the
turn, serialize the dal ChatResponse. dal is canonical — the shapes are
imported, never redefined here.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from typing import Any

from fastapi import APIRouter, Request

from dal.schemas import ChatMessage, ChatRequest, ChatResponse

from app.utils.logging import get_logger, log_event

router = APIRouter()
logger = get_logger("orchestrator")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _message(sender: str, *, text_khmer: str, text_eng: str, **flags: Any) -> dict:
    """Build a dal-validated ChatMessage dict for the transcript."""
    return ChatMessage(
        id=str(uuid.uuid4()),
        sender=sender,
        text_khmer=text_khmer,
        text_eng=text_eng,
        timestamp=_now_iso(),
        **flags,
    ).model_dump(mode="json")


# response_model_by_alias=False: FastAPI defaults to by_alias=True, which would
# leak camelCase onto the service-to-service wire. snake_case everywhere except
# the gateway->browser boundary (claude.md §5). This bug was already caught once.
@router.post("/chat", response_model=ChatResponse, response_model_by_alias=False)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    store = request.app.state.session_store
    graph = request.app.state.graph
    

    # Init session metadata on first message (no-op if already set)
    if await store.get_session_meta(body.session_id) is None:
        grade = body.grade if body.grade is not None else 4
        await store.init_session(
            body.session_id,
            student_id=body.student_id,
            grade=grade,
            language=body.language.value if hasattr(body.language, "value") else (body.language or "km"),
        )

    transcript = await store.get(body.session_id)

    state: dict[str, Any] = {
        "student_id": body.student_id,
        "session_id": body.session_id,
        "language": body.language.value,
        "mode": body.mode.value,
        "problem_id": body.problem_id,
        "active_step_index": body.active_step_index,
        "prompt": body.prompt,
        "transcript": transcript,
    }
    result = await graph.ainvoke(state)

    # Log detected intent for this turn
    await store.log_intent(
        body.session_id,
        intent=result.get("intent", "unknown"),
        routed_to=result.get("routed_to", result.get("intent", "unknown")),
    )

    # Persist conversation summary if the graph produced one
    if summary := result.get("conversation_summary"):
        await store.set_summary(body.session_id, summary)

    # Log service call timing
    await store.log_service_call(
        body.session_id,
        service_name=result.get("intent", "unknown"),
        latency_ms=(time.perf_counter() - started) * 1000,
        status="ok",
    )

    response = ChatResponse(
        text_khmer=result.get("text_khmer", ""),
        text_eng=result.get("text_eng", ""),
        is_safety_refusal=result.get("is_safety_refusal", False),
        is_parent_help=result.get("is_parent_help", False),
        session_id=body.session_id,
        suggested_next=result.get("suggested_next"),
    )

    # Persist the turn: the child's message + Tunsay's reply (single-language
    # user text mirrors the requested language).
    is_khmer = body.language.value == "km"
    await store.append(
        body.session_id,
        _message(
            "user",
            text_khmer=body.prompt if is_khmer else "",
            text_eng="" if is_khmer else body.prompt,
        ),
        _message(
            "sayo",
            text_khmer=response.text_khmer,
            text_eng=response.text_eng,
            is_safety_refusal=response.is_safety_refusal,
            is_parent_help=response.is_parent_help,
        ),
    )

    # Structured, content-free logging (claude.md §5): never the prompt or reply.
    log_event(
        logger,
        "chat_turn",
        student_id=body.student_id,
        session_id=body.session_id,
        intent=result.get("intent"),
        duration_ms=(time.perf_counter() - started) * 1000,
    )
    return response
