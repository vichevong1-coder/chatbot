from __future__ import annotations

from fractions import Fraction
import re

KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"
LATIN_DIGITS = "0123456789"
DIGIT_TRANSLATOR = str.maketrans(KHMER_DIGITS, LATIN_DIGITS)

def normalize_text(text: str) -> str:
    """Normalize general text by trimming, collapsing spaces, and lowering case."""
    if not text:
        return ""
    # Translate Khmer numerals to Latin digits
    text = text.translate(DIGIT_TRANSLATOR)
    # Lowercase and strip whitespace
    text = text.strip().lower()
    # Collapse multiple spaces into one
    text = re.sub(r"\s+", " ", text)
    return text

def parse_to_fraction(val_str: str) -> Fraction | None:
    """Try to parse a string value into a Fraction if it's purely numeric."""
    normalized = normalize_text(val_str)
    # Reject strings containing letters (either English or Khmer)
    if re.search(r"[a-z\u1780-\u17F9]", normalized):
        return None
        
    try:
        # e.g., "1/2" or "0.5" or "5"
        return Fraction(normalized)
    except (ValueError, ZeroDivisionError):
        return None

def check_answer(
    student_answer: str,
    correct_answer: str,
    input_format: str = "number",
    options: list[str] | None = None,
    language: str = "km"
) -> bool:
    """Grades a student's answer against the correct answer.
    
    Supports:
    - Text exact match (normalized, case-insensitive).
    - MCQ exact match.
    - Numerical equivalence (e.g. 1/2 == 0.5 == 2/4).
    """
    norm_student = normalize_text(student_answer)
    norm_correct = normalize_text(correct_answer)
    
    if not norm_student or not norm_correct:
        return False
        
    if norm_student == norm_correct:
        return True
        
    # Numerical validation
    if input_format == "number" or re.search(r"\d", correct_answer):
        student_frac = parse_to_fraction(student_answer)
        correct_frac = parse_to_fraction(correct_answer)
        
        if student_frac is not None and correct_frac is not None:
            return student_frac == correct_frac
            
    # Substring matches or other fallback text checks (only for text answers)
    if input_format == "text":
        return norm_student == norm_correct
        
    return False
