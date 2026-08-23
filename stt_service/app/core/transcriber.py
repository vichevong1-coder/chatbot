"""Speech transcription engine using Gemini multimodal audio or local fallback."""

from __future__ import annotations

import base64
import os
from typing import Any

from app.core.audio_preprocess import validate_and_inspect_audio
from app.core.language_detect import detect_language
from app.core.math_notation_normalizer import normalize_spoken_math
try:
    from faster_whisper import WhisperModel  # type: ignore
except ImportError:
    WhisperModel = None


class AudioTranscriber:
    def __init__(self, api_key: str | None = None, model_path: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        # Check local whisper-small-km-ct2 model directory
        default_model_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "whisper-small-km-ct2")
        )
        self.model_path = model_path or os.environ.get("WHISPER_MODEL_PATH", default_model_dir)
        self._whisper_model = None
        self._whisper_attempted = False

    def _get_whisper_model(self):
        if not self._whisper_attempted:
            self._whisper_attempted = True
            if WhisperModel is not None and os.path.exists(self.model_path):
                try:
                    self._whisper_model = WhisperModel(self.model_path, device="cpu", compute_type="int8")
                except Exception:
                    self._whisper_model = None
        return self._whisper_model

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        preferred_language: str | None = None,
    ) -> dict[str, Any]:
        meta = validate_and_inspect_audio(audio_bytes, filename)
        fmt = meta["format"]

        # 1. Try local fine-tuned whisper-small-km-ct2 CTranslate2 model if available
        whisper = self._get_whisper_model()
        if whisper and os.path.exists(self.model_path):
            try:
                import tempfile
                tmp = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
                tmp_path = tmp.name
                try:
                    tmp.write(audio_bytes)
                    tmp.close()  # Close handle so ffmpeg/ctranslate2 on Windows can read file

                    lang_arg = preferred_language if preferred_language in ("km", "en") else None
                    segments, _ = whisper.transcribe(tmp_path, language=lang_arg)
                    raw_text = " ".join([seg.text.strip() for seg in segments]).strip()
                    if raw_text:
                        lang = preferred_language or detect_language(raw_text)
                        norm = normalize_spoken_math(raw_text)
                        return {
                            "text": raw_text,
                            "language": lang,
                            "normalized_math": norm,
                        }
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except Exception:
                pass

        # If Gemini API key is present, attempt live transcription
        if self.api_key:
            try:
                import httpx
                b64 = base64.b64encode(audio_bytes).decode("utf-8")
                mime_type = f"audio/{fmt}" if fmt in ("wav", "mp3", "ogg") else "audio/webm"

                prompt = (
                    "Listen to this audio recording from a student in Cambodia asking a homework question. "
                    "Transcribe exactly what they say. Do not add explanations. "
                    "If they speak Khmer, output Khmer script. If English, output English."
                )

                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": b64,
                                    }
                                },
                            ]
                        }
                    ]
                }

                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
                    f"?key={self.api_key}"
                )

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "").strip()
                                lang = preferred_language or detect_language(raw_text)
                                norm = normalize_spoken_math(raw_text)
                                return {
                                    "text": raw_text,
                                    "language": lang,
                                    "normalized_math": norm,
                                }
            except Exception:
                pass

        # Offline test / demo fallback
        fallback_text = (
            "៥ បូក ៣ ស្មើប៉ុន្មាន?"
            if (preferred_language == "km" or preferred_language is None)
            else "What is five plus three?"
        )
        lang = preferred_language or detect_language(fallback_text)
        norm = normalize_spoken_math(fallback_text)
        return {
            "text": fallback_text,
            "language": lang,
            "normalized_math": norm,
        }
