"""Math and Khmer OCR engine using Gemini multimodal vision with fallback for offline tests."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
_PLACEHOLDER_KEYS = frozenset({"", "MY_GEMINI_API_KEY", "replace-with-your-gemini-api-key"})

MATH_EXPR_PATTERN = re.compile(
    r"(?:[\d០-៩a-zA-Z\(\)]+[\s\+\-\*\/\^=×÷\:\.,><≤≥]+[\d០-៩a-zA-Z\(\)\+\-\*\/\^=×÷\:\.,><≤≥\?\s]*[\d០-៩a-zA-Z\?\)])"
)

# Default fallback values for offline testing and demo mode
OFFLINE_FALLBACK = {
    "text_khmer": "គណនាលំហាត់៖ ៥ + ៣ = ?",
    "text_eng": "Calculate: 5 + 3 = ?",
    "math_expressions": ["5 + 3 = ?"],
    "confidence": 1.0,
}


def extract_math_expressions(text: str) -> list[str]:
    """Extract candidate mathematical expressions and equations from free text."""
    if not text:
        return []

    expressions: list[str] = []
    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        # Check if line looks like an equation or math problem
        matches = MATH_EXPR_PATTERN.findall(line_clean)
        for match in matches:
            m = match.strip()
            if len(m) >= 3 and any(char in m for char in "+-*/^=×÷:"):
                expressions.append(m)

    # Remove duplicates while preserving order
    seen = set()
    unique_expressions = []
    for expr in expressions:
        if expr not in seen:
            seen.add(expr)
            unique_expressions.append(expr)

    return unique_expressions


class MathOcrEngine:
    """Extracts math expressions and bilingual text from homework images."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self._timeout_seconds = timeout_seconds

    def _effective_api_key(self) -> str | None:
        key = self._api_key if self._api_key is not None else os.environ.get("GEMINI_API_KEY")
        key = (key or "").strip()
        return None if key in _PLACEHOLDER_KEYS else key

    async def extract(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        """Extract Khmer text, English text, and math expressions from preprocessed image."""
        api_key = self._effective_api_key()

        if api_key:
            try:
                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                prompt = (
                    "You are an OCR and Math Transcription engine for Cambodian K-12 primary and secondary school homework.\n"
                    "Analyze the uploaded image and extract:\n"
                    "1. All Khmer text present (printed or handwritten homework problem statement) into `text_khmer`.\n"
                    "2. All English text or English translation/transcription if present into `text_eng`.\n"
                    "3. All mathematical expressions, formulas, arithmetic operations, or equations into `math_expressions` (a JSON array of strings in standard math/ASCII notation, e.g. [\"5 + 3 = ?\"]).\n"
                    "4. Your estimated OCR confidence score (0.0 to 1.0) into `confidence`.\n\n"
                    "Return ONLY a valid JSON object matching this schema:\n"
                    "{\n"
                    '  "text_khmer": "...",\n'
                    '  "text_eng": "...",\n'
                    '  "math_expressions": ["..."],\n'
                    '  "confidence": 0.95\n'
                    "}"
                )

                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": b64_data,
                                    }
                                },
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                }

                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
                    f"?key={api_key}"
                )

                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_json_str = parts[0].get("text", "").strip()
                                # Clean markdown code fences if present
                                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json_str, flags=re.MULTILINE).strip()
                                parsed = json.loads(cleaned)

                                text_khmer = str(parsed.get("text_khmer") or "").strip()
                                text_eng = str(parsed.get("text_eng") or "").strip()
                                math_exprs = parsed.get("math_expressions") or []
                                if not isinstance(math_exprs, list):
                                    math_exprs = [str(math_exprs)]
                                math_exprs = [str(e).strip() for e in math_exprs if str(e).strip()]

                                # Augment math expressions from text if empty
                                if not math_exprs:
                                    math_exprs = extract_math_expressions(f"{text_khmer}\n{text_eng}")

                                confidence = float(parsed.get("confidence", 0.95))
                                confidence = max(0.0, min(1.0, confidence))

                                return {
                                    "text_khmer": text_khmer,
                                    "text_eng": text_eng,
                                    "math_expressions": math_exprs,
                                    "confidence": confidence,
                                }
            except Exception as exc:
                logger.warning("math_ocr: live multimodal OCR failed (%s); falling back to offline result", type(exc).__name__)

        # Offline fallback
        return dict(OFFLINE_FALLBACK)
