"""Tests for language detection and spoken math normalization in stt_service."""

from __future__ import annotations

from app.core.language_detect import detect_language
from app.core.math_notation_normalizer import normalize_spoken_math


def test_language_detection():
    assert detect_language("សួស្តី តើខ្ញុំត្រូវធ្វើដូចម្តេច?") == "km"
    assert detect_language("How do I solve this equation?") == "en"
    assert detect_language("៥ បូក ៣") == "km"
    assert detect_language("5 + 3") == "en"


def test_spoken_math_normalization_khmer():
    assert normalize_spoken_math("៥ បូក ៣") == "5 + 3"
    assert normalize_spoken_math("១២ ចែក ៤") == "12 / 4"
    assert normalize_spoken_math("៧ គុណ ៨ ស្មើប៉ុន្មាន?") == "7 * 8 = ប៉ុន្មាន?"
    assert normalize_spoken_math("២០ ដក ៥") == "20 - 5"


def test_spoken_math_normalization_english():
    assert normalize_spoken_math("5 plus 3") == "5 + 3"
    assert normalize_spoken_math("12 divided by 4") == "12 / 4"
    assert normalize_spoken_math("7 times 8 equals what?") == "7 * 8 = what?"
    assert normalize_spoken_math("20 minus 5") == "20 - 5"
