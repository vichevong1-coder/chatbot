"""Normalizes spoken mathematical operations in Khmer and English into arithmetic expressions."""

from __future__ import annotations

import re

# Khmer numerals ០-៩ -> ASCII 0-9
_KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"
_KHMER_TO_ASCII = {ord(k): str(i) for i, k in enumerate(_KHMER_DIGITS)}

_KHMER_SPOKEN_WORDS = {
    "បូក": "+",
    "ថែម": "+",
    "ដក": "-",
    "គុណ": "*",
    "ចែក": "/",
    "ស្មើ": "=",
    "ភាគរយ": "%",
}

_ENGLISH_SPOKEN_WORDS = {
    "plus": "+",
    "add": "+",
    "minus": "-",
    "subtract": "-",
    "times": "*",
    "multiplied by": "*",
    "divided by": "/",
    "divide by": "/",
    "over": "/",
    "equals": "=",
    "percent": "%",
}


def normalize_spoken_math(text: str) -> str:
    """Translate spoken math words to standard operators and Khmer numerals to ASCII."""
    # Convert numerals
    result = text.translate(_KHMER_TO_ASCII)

    # Convert Khmer spoken operators
    for word, sym in _KHMER_SPOKEN_WORDS.items():
        result = result.replace(word, f" {sym} ")

    # Convert English spoken operators
    for word, sym in _ENGLISH_SPOKEN_WORDS.items():
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        result = pattern.sub(f" {sym} ", result)

    # Collapse extra whitespace
    return re.sub(r"\s+", " ", result).strip()
