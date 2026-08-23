"""POST /translate — educational translation route for pedagogy_service."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import Field

from dal.schemas.base import TunsayModel
from dal.schemas.enums import Language

from app.core.translator import TranslatorService

router = APIRouter()

_translator: TranslatorService | None = None


def get_translator() -> TranslatorService:
    global _translator
    if _translator is None:
        _translator = TranslatorService()
    return _translator


def set_translator(translator: TranslatorService | None) -> None:
    """Test seam for injecting a custom TranslatorService."""
    global _translator
    _translator = translator


class TranslateRequest(TunsayModel):
    text: str = Field(..., min_length=1)
    target_language: Language
    source_language: Language | None = None


class TranslateResponse(TunsayModel):
    translated_text: str
    target_language: str
    from_fallback: bool


@router.post("/translate", response_model=TranslateResponse, response_model_by_alias=False)
async def translate(request: TranslateRequest) -> TranslateResponse:
    result = await get_translator().translate(
        text=request.text,
        target_language=request.target_language,
        source_language=request.source_language,
    )
    return TranslateResponse(**result)
