"""POST /chat/audio — voice-driven chat endpoint."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from dal.schemas import ChatMessage, ChatResponse
from app.utils.logging import get_logger, log_event

router = APIRouter()
logger = get_logger("orchestrator")


def _resolve_student_id(request: Request, form_student_id: str | None) -> str | None:
    if form_student_id and form_student_id != "anonymous":
        return form_student_id
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        parts = token.split(".")
        if len(parts) >= 2:
            try:
                import base64, json
                padding = "=" * (4 - len(parts[1]) % 4)
                payload_bytes = base64.b64decode(parts[1] + padding)
                payload = json.loads(payload_bytes)
                if payload.get("sub"):
                    return str(payload["sub"])
            except Exception:
                pass
    return None


@router.post("/chat/audio", response_model=ChatResponse, response_model_by_alias=False)
async def chat_audio(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    student_id: str | None = Form(default=None),
    mode: str = Form(default="student"),
    language: str = Form(default="km"),
    problem_id: str | None = Form(default=None),
    active_step_index: int | None = Form(default=None),
) -> ChatResponse:
    started = time.perf_counter()
    store = request.app.state.session_store
    graph = request.app.state.graph
    clients = request.app.state.clients

    resolved_student_id = _resolve_student_id(request, student_id)
    if resolved_student_id:
        if await store.get_session_meta(session_id) is None:
            await store.init_session(
                session_id,
                student_id=resolved_student_id,
                grade=4,
                language=language,
            )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # Transcribe audio using STT client
    try:
        stt_result = await clients.stt.transcribe(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.webm",
            language=language,
        )
        prompt_text = stt_result.get("text") or stt_result.get("normalized_math") or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"STT transcription failed: {exc}")

    if not prompt_text.strip():
        raise HTTPException(status_code=422, detail="No speech detected in audio")

    # Fetch transcript from Redis
    transcript = await store.get(session_id)

    # Drive LangGraph
    final_student_id = resolved_student_id or student_id or "anonymous"
    state: dict[str, Any] = {
        "student_id": final_student_id,
        "session_id": session_id,
        "language": language,
        "mode": mode,
        "problem_id": problem_id,
        "active_step_index": active_step_index,
        "prompt": prompt_text,
        "transcript": transcript,
    }
    result = await graph.ainvoke(state)

    # Log the audio file as an attachment
    await store.log_attachment(session_id, file_key=file.filename or "audio.webm", file_type="audio")

    # Log detected intent
    await store.log_intent(
        session_id,
        intent=result.get("intent", "unknown"),
        routed_to=result.get("routed_to", result.get("intent", "unknown")),
    )

    response = ChatResponse(
        text_khmer=result.get("text_khmer", ""),
        text_eng=result.get("text_eng", ""),
        is_safety_refusal=result.get("is_safety_refusal", False),
        is_parent_help=result.get("is_parent_help", False),
        session_id=session_id,
        suggested_next=result.get("suggested_next"),
    )

    # Save turn
    is_khmer = language == "km"
    await store.append(
        session_id,
        ChatMessage(
            id=str(time.time()),
            sender="user",
            text_khmer=prompt_text if is_khmer else "",
            text_eng="" if is_khmer else prompt_text,
            timestamp=str(time.time()),
        ).model_dump(mode="json"),
        ChatMessage(
            id=str(time.time() + 0.001),
            sender="sayo",
            text_khmer=response.text_khmer,
            text_eng=response.text_eng,
            timestamp=str(time.time() + 0.001),
            is_safety_refusal=response.is_safety_refusal,
            is_parent_help=response.is_parent_help,
        ).model_dump(mode="json"),
    )

    log_event(
        logger,
        "chat_audio_turn",
        student_id=student_id or "anonymous",
        session_id=session_id,
        intent=result.get("intent", "explain"),
        duration_ms=(time.perf_counter() - started) * 1000,
    )

    return response
