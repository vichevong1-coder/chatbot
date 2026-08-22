"""POST /extract — image OCR and math expression extraction endpoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.core.image_preprocess import ImageValidationError, validate_and_preprocess_image

logger = logging.getLogger(__name__)

router = APIRouter()


class OcrExtractResponse(BaseModel):
    text_khmer: str = ""
    text_eng: str = ""
    math_expressions: list[str] = Field(default_factory=list)
    confidence: float = 1.0


@router.post("/extract", response_model=OcrExtractResponse)
async def extract(
    request: Request,
    file: UploadFile = File(...),
) -> OcrExtractResponse:
    """Extract printed Khmer, English text, and math expressions from uploaded image."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image payload")

    try:
        preprocessed = validate_and_preprocess_image(data, filename=file.filename)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.warning("image_preprocess: unexpected failure (%s: %s)", type(exc).__name__, str(exc))
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(exc)}")

    engine = getattr(request.app.state, "ocr_engine", None)
    if engine is None:
        from app.core.math_ocr import MathOcrEngine
        engine = MathOcrEngine()

    try:
        result = await engine.extract(
            preprocessed.image_bytes,
            filename=file.filename or "image.jpg",
            mime_type=preprocessed.mime_type,
        )
        return OcrExtractResponse(**result)
    except Exception as exc:
        logger.error("math_ocr: extraction failed (%s: %s)", type(exc).__name__, str(exc))
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(exc)}")
