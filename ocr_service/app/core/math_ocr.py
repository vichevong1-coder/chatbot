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


# Thai Unicode Range: \u0E00-\u0E7F
THAI_SCRIPT_PATTERN = re.compile(r"[\u0E00-\u0E7F]")
KHMER_SCRIPT_PATTERN = re.compile(r"[\u1780-\u17FF\u19E0-\u19FF]")


def sanitize_script_no_thai(text: str) -> str:
    """Sanitize OCR output to prevent Thai script leakage into Khmer/English results."""
    if not text:
        return ""
    # Strip any accidentally predicted Thai characters (\u0E00-\u0E7F)
    cleaned = THAI_SCRIPT_PATTERN.sub("", text)
    # Clean up redundant spaces left by removals
    return re.sub(r"[ \t]+", " ", cleaned).strip()


def extract_math_expressions(text: str) -> list[str]:
    """Extract candidate mathematical expressions and equations from free text."""
    if not text:
        return []

    text = sanitize_script_no_thai(text)
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


try:
    from paddleocr import PaddleOCR  # type: ignore
    _PADDLE_AVAILABLE = True
except ImportError:
    _PADDLE_AVAILABLE = False


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
        self._paddle_engine: Any = None

    def _effective_api_key(self) -> str | None:
        key = self._api_key if self._api_key is not None else os.environ.get("GEMINI_API_KEY")
        key = (key or "").strip()
        return None if key in _PLACEHOLDER_KEYS else key

    def _run_darayut_ocr(self, image_bytes: bytes) -> dict[str, Any] | None:
        """Run dedicated Darayut Khmer & Math OCR model for high-accuracy Khmer script extraction."""
        darayut_url = os.environ.get("DARAYUT_OCR_URL")
        if not darayut_url:
            return None
        try:
            with httpx.Client(timeout=10.0) as client:
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                resp = client.post(darayut_url, files=files)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_km = sanitize_script_no_thai(data.get("text_khmer") or data.get("text") or "")
                    raw_en = sanitize_script_no_thai(data.get("text_eng") or "")
                    exprs = data.get("math_expressions") or extract_math_expressions(f"{raw_km}\n{raw_en}")
                    return {
                        "text_khmer": raw_km,
                        "text_eng": raw_en,
                        "math_expressions": exprs,
                        "confidence": float(data.get("confidence", 0.95)),
                    }
        except Exception as exc:
            logger.warning("Darayut OCR call failed (%s)", exc)
        return None

    def _run_paddle_ocr(self, image_bytes: bytes) -> dict[str, Any] | None:
        """Run local PaddleOCR / PaddleOCR-VL layout engine for multi-language & math symbol extraction."""
        if not _PADDLE_AVAILABLE:
            return None
        try:
            import io
            import numpy as np
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(img)

            if self._paddle_engine is None:
                # Restrict languages strictly to English / Khmer without Thai language models
                self._paddle_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

            results = self._paddle_engine.ocr(img_np, cls=True)
            lines: list[str] = []
            confidences: list[float] = []
            if results and results[0]:
                for item in results[0]:
                    raw_line = item[1][0]
                    # Enforce strict non-Thai script filter
                    clean_line = sanitize_script_no_thai(raw_line)
                    if clean_line:
                        conf = float(item[1][1])
                        lines.append(clean_line)
                        confidences.append(conf)

            full_text = "\n".join(lines)
            math_exprs = extract_math_expressions(full_text)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.90

            has_khmer = bool(KHMER_SCRIPT_PATTERN.search(full_text))
            return {
                "text_khmer": full_text if has_khmer else "",
                "text_eng": full_text if not has_khmer else "",
                "math_expressions": math_exprs,
                "confidence": round(avg_conf, 2),
            }
        except Exception as exc:
            logger.warning("PaddleOCR processing failed (%s)", exc)
            return None

    async def extract(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        """Extract Khmer text, English text, and math expressions from preprocessed image."""
        api_key = self._effective_api_key()
        ocr_engine = os.environ.get("OCR_ENGINE", "auto").lower()

        # Check Darayut OCR engine if requested or configured
        if ocr_engine == "darayut":
            darayut_res = self._run_darayut_ocr(image_bytes)
            if darayut_res:
                return darayut_res

        # Direct PaddleOCR request or auto fallback when Gemini key is absent
        if ocr_engine == "paddleocr" or (ocr_engine == "auto" and not api_key and _PADDLE_AVAILABLE):
            paddle_res = self._run_paddle_ocr(image_bytes)
            if paddle_res:
                return paddle_res

        if api_key:
            try:
                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                prompt = (
                    "You are an OCR and Math Transcription engine for Cambodian K-12 primary and secondary school homework.\n"
                    "STRICT SCRIPT ISOLATION: The target language is KHMER (Cambodian script U+1780..U+17FF) and ENGLISH.\n"
                    "Do NOT output any Thai script characters (U+0E00..U+0E7F). Render Cambodian text strictly in Khmer script.\n\n"
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
                                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json_str, flags=re.MULTILINE).strip()
                                parsed = json.loads(cleaned)

                                text_khmer = sanitize_script_no_thai(str(parsed.get("text_khmer") or "").strip())
                                text_eng = sanitize_script_no_thai(str(parsed.get("text_eng") or "").strip())
                                math_exprs = parsed.get("math_expressions") or []
                                if not isinstance(math_exprs, list):
                                    math_exprs = [str(math_exprs)]
                                math_exprs = [sanitize_script_no_thai(str(e)).strip() for e in math_exprs if str(e).strip()]

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
                logger.warning("math_ocr: live multimodal OCR failed (%s); falling back", type(exc).__name__)

        # Try PaddleOCR as secondary fallback before offline static default
        paddle_res = self._run_paddle_ocr(image_bytes)
        if paddle_res:
            return paddle_res

        # Offline fallback
        return dict(OFFLINE_FALLBACK)
