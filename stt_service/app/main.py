"""FastAPI application for stt_service."""

from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.audio_preprocess import AudioValidationError
from app.core.transcriber import AudioTranscriber

SERVICE_NAME = "stt_service"


class TranscribeResponse(BaseModel):
    text: str
    language: str
    normalized_math: str


def create_app(transcriber: AudioTranscriber | None = None) -> FastAPI:
    app = FastAPI(title=SERVICE_NAME)
    app.state.transcriber = transcriber or AudioTranscriber()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": SERVICE_NAME}

    @app.post("/transcribe", response_model=TranscribeResponse)
    async def transcribe(
        file: UploadFile = File(...),
        language: str | None = Form(default=None),
    ) -> TranscribeResponse:
        data = await file.read()
        try:
            result = await app.state.transcriber.transcribe(
                audio_bytes=data,
                filename=file.filename or "audio.webm",
                preferred_language=language,
            )
            return TranscribeResponse(**result)
        except AudioValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(exc)}")

    return app


app = create_app()
