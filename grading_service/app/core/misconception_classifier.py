from __future__ import annotations

import re
from app.core.checker import normalize_text, parse_to_fraction

def classify_misconception(
    student_answer: str,
    correct_answer: str,
    input_format: str = "number",
    question_text: str = ""
) -> str | None:
    """Classifies the misconception code for an incorrect answer.
    
    Returns one of:
    - 'place_value_error'
    - 'operation_confusion'
    - 'off_by_one'
    - 'unit_omission'
    - 'calculation_error'
    - None (if it cannot be classified or is correct)
    """
    norm_student = normalize_text(student_answer)
    norm_correct = normalize_text(correct_answer)
    
    if not norm_student or not norm_correct or norm_student == norm_correct:
        return None
        
    # Check for unit omission first
    # e.g., correct is "5 kg" and student answered "5"
    # Find if correct answer has a number followed by non-digits
    match_unit = re.match(r"^([\d.,]+)\s*([a-zA-Z\u1780-\u17F9]+)$", correct_answer.strip())
    if match_unit:
        number_part, unit_part = match_unit.groups()
        norm_num = normalize_text(number_part)
        if norm_student == norm_num:
            return "unit_omission"
            
    # Try parsing both as fractions/numbers
    student_frac = parse_to_fraction(student_answer)
    correct_frac = parse_to_fraction(correct_answer)
    
    if student_frac is not None and correct_frac is not None:
        try:
            student_val = float(student_frac)
            correct_val = float(correct_frac)
            
            # Place value error (off by a factor of 10)
            if student_val == correct_val * 10 or student_val == correct_val / 10:
                return "place_value_error"
                
            # Off by one
            if abs(student_val - correct_val) == 1.0:
                return "off_by_one"
                
            # Operation confusion: check if numbers in question text were combined wrongly
            # Translate Khmer digits in question text first
            from app.core.checker import DIGIT_TRANSLATOR
            q_translated = question_text.translate(DIGIT_TRANSLATOR)
            # Find all numbers in the question text
            nums = [float(x) for x in re.findall(r"\d+\.\d+|\d+", q_translated)]
            if len(nums) >= 2:
                # Let's check common operations between the first two numbers
                a, b = nums[0], nums[1]
                candidates = {
                    "add": a + b,
                    "sub_ab": a - b,
                    "sub_ba": b - a,
                    "mul": a * b,
                    "div_ab": a / b if b != 0 else None,
                    "div_ba": b / a if a != 0 else None
                }
                
                # Filter out candidates that equal the correct value (or are None)
                confused_operations = []
                for op, val in candidates.items():
                    if val is not None and abs(val - student_val) < 0.0001:
                        if abs(val - correct_val) >= 0.0001:
                            confused_operations.append(op)
                            
                if confused_operations:
                    return "operation_confusion"
                    
            # If it's a number but doesn't match the above, it's a general calculation error
            return "calculation_error"
        except (ValueError, OverflowError):
            pass
            
    return "calculation_error"
