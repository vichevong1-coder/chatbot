"""Language detection for transcribed audio and text prompts."""

from __future__ import annotations

import re

# Khmer Unicode Range: U+1780 to U+17FF and U+19E0 to U+19FF
_KHMER_CHAR_RE = re.compile(r"[\u1780-\u17FF\u19E0-\u19FF]")


def detect_language(text: str) -> str:
    """Detect if the transcription is primarily Khmer ('km') or English ('en')."""
    if not text.strip():
        return "km"
    khmer_matches = len(_KHMER_CHAR_RE.findall(text))
    total_chars = len(text.replace(" ", ""))
    if total_chars > 0 and (khmer_matches / total_chars) > 0.15:
        return "km"
    return "en"
