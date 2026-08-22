"""POST /chat/image — image upload, OCR analysis, and tutoring turn router."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from dal.schemas import ChatMessage, ChatResponse
from app.infrastructure.service_clients import ServiceUnavailable
from app.utils.logging import get_logger, log_event

router = APIRouter()
logger = get_logger("orchestrator")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _message(sender: str, *, text_khmer: str, text_eng: str, image_uri: str | None = None, **flags: Any) -> dict:
    """Build a dal-validated ChatMessage dict for the transcript."""
    return ChatMessage(
        id=str(uuid.uuid4()),
        sender=sender,
        text_khmer=text_khmer,
        text_eng=text_eng,
        image_uri=image_uri,
        timestamp=_now_iso(),
        **flags,
    ).model_dump(mode="json")


@router.post("/chat/image", response_model=ChatResponse, response_model_by_alias=False)
@router.post("/chat_image", response_model=ChatResponse, response_model_by_alias=False)
async def chat_image(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    student_id: str = Form(default="anonymous"),
    language: str = Form(default="km"),
    mode: str = Form(default="student"),
    problem_id: str | None = Form(default=None),
) -> ChatResponse:
    """Process uploaded homework image, extract math problem via OCR, and route to tutor graph."""
    started = time.perf_counter()
    store = request.app.state.session_store
    graph = request.app.state.graph
    clients = request.app.state.clients

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image payload")

    # 1. Run OCR extraction
    ocr_client = getattr(clients, "ocr", None)
    ocr_result: dict[str, Any] = {}
    if ocr_client:
        try:
            ocr_result = await ocr_client.extract(image_bytes, filename=file.filename or "image.jpg")
        except ServiceUnavailable:
            logger.warning("chat_image: ocr_service unavailable; using fallback math problem")
            ocr_result = {
                "text_khmer": "៥ + ៣ = ?",
                "text_eng": "5 + 3 = ?",
                "math_expressions": ["5 + 3 = ?"],
                "confidence": 0.5,
            }
        except Exception as exc:
            logger.error("chat_image: OCR extraction failed (%s: %s)", type(exc).__name__, str(exc))
            raise HTTPException(status_code=400, detail=f"Image OCR failed: {str(exc)}")
    else:
        ocr_result = {
            "text_khmer": "៥ + ៣ = ?",
            "text_eng": "5 + 3 = ?",
            "math_expressions": ["5 + 3 = ?"],
            "confidence": 0.5,
        }

    text_khmer = (ocr_result.get("text_khmer") or "").strip()
    text_eng = (ocr_result.get("text_eng") or "").strip()
    math_exprs = ocr_result.get("math_expressions") or []

    is_khmer = language == "km"
    if is_khmer:
        prompt_text = text_khmer or (math_exprs[0] if math_exprs else text_eng)
    else:
        prompt_text = text_eng or (math_exprs[0] if math_exprs else text_khmer)

    if not prompt_text:
        prompt_text = math_exprs[0] if math_exprs else "5 + 3 = ?"

    # 2. Match problem if not explicitly provided
    matched_problem_id = problem_id
    if not matched_problem_id and hasattr(clients, "content") and clients.content is not None:
        try:
            catalog = await clients.content.list_problems()
            for prob in catalog:
                p_stmt_km = prob.get("problem_statement_khmer") or ""
                p_stmt_en = prob.get("problem_statement_eng") or ""
                p_title_km = prob.get("title_khmer") or ""
                p_title_en = prob.get("title_eng") or ""
                for expr in math_exprs:
                    if expr and (expr in p_stmt_km or expr in p_stmt_en):
                        matched_problem_id = prob.get("id")
                        break
                if matched_problem_id:
                    break
                if prompt_text and (prompt_text in p_stmt_km or prompt_text in p_stmt_en or prompt_text in p_title_km or prompt_text in p_title_en):
                    matched_problem_id = prob.get("id")
                    break
        except Exception:
            pass

    # 3. Invoke LangGraph state machine
    transcript = await store.get(session_id)
    state: dict[str, Any] = {
        "student_id": student_id,
        "session_id": session_id,
        "language": language,
        "mode": mode,
        "problem_id": matched_problem_id,
        "active_step_index": 0,
        "prompt": prompt_text,
        "transcript": transcript,
    }
    result = await graph.ainvoke(state)

    response = ChatResponse(
        text_khmer=result.get("text_khmer", ""),
        text_eng=result.get("text_eng", ""),
        is_safety_refusal=result.get("is_safety_refusal", False),
        is_parent_help=result.get("is_parent_help", False),
        session_id=session_id,
        suggested_next=result.get("suggested_next"),
    )

    # 4. Save turn to transcript
    await store.append(
        session_id,
        _message(
            "user",
            text_khmer=prompt_text if is_khmer else (text_khmer or ""),
            text_eng="" if is_khmer else prompt_text,
            image_uri=file.filename or "uploaded_image.jpg",
        ),
        _message(
            "sayo",
            text_khmer=response.text_khmer,
            text_eng=response.text_eng,
            is_safety_refusal=response.is_safety_refusal,
            is_parent_help=response.is_parent_help,
        ),
    )

    # 5. Content-free structured logging
    log_event(
        logger,
        "chat_image_turn",
        student_id=student_id,
        session_id=session_id,
        intent=result.get("intent"),
        duration_ms=(time.perf_counter() - started) * 1000,
    )

    return response
