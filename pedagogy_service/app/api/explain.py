"""POST /explain router: parse, delegate to core, serialize. No business logic.

The generator is built once at import time with the real (Gemini-backed) LlmClient;
tests swap it via ``set_generator`` / FastAPI dependency-free injection, keeping the
fake ``call`` inside dal's LlmClient rather than patching SDK internals.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import Field

from dal.schemas.base import TunsayModel
from dal.schemas.enums import Language, UserMode

from app.core.explanation_generator import ExplanationGenerator

router = APIRouter()

_generator: ExplanationGenerator | None = None


def get_generator() -> ExplanationGenerator:
    global _generator
    if _generator is None:
        _generator = ExplanationGenerator()
    return _generator


def set_generator(generator: ExplanationGenerator | None) -> None:
    """Test seam: install a generator built around a fake LlmClient ``call``."""
    global _generator
    _generator = generator


class ExplainRequest(TunsayModel):
    prompt: str = Field(..., min_length=1)
    grade: int = Field(..., ge=1, le=12)  # structural bounds; supported-set policy is dal's
    language: Language
    mode: UserMode
    context: str | None = None  # optional problem/step text from the orchestrator
    misconception_code: str | None = None  # optional classification from grading_service (P2.2)


class ExplainResponse(TunsayModel):
    text_khmer: str  # single-language rule (contracts.md §3): the other side is ""
    text_eng: str
    from_fallback: bool
    prompt_tokens: int | None = None
    output_tokens: int | None = None


# snake_case on the wire between services — the gateway is the camelCase boundary
# (.claude/claude.md §5), so switch off FastAPI's default by_alias serialization.
@router.post("/explain", response_model=ExplainResponse, response_model_by_alias=False)
async def explain(request: ExplainRequest) -> ExplainResponse:
    result = await get_generator().explain(
        prompt=request.prompt,
        grade=request.grade,
        language=request.language,
        mode=request.mode,
        context=request.context,
        misconception_code=request.misconception_code,
    )
    return ExplainResponse(**result)
