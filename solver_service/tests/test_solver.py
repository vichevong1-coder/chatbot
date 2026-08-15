"""Unit tests for the pure solver core (no server needed)."""

import pytest

from app.core.math_solver import SolverError, normalize_expression, solve
from app.core.step_formatter import format_steps


def answer(expression: str) -> str:
    return solve(expression).answer


# --- the four operations ---------------------------------------------------


def test_addition():
    assert answer("3 + 4") == "7"


def test_subtraction():
    assert answer("10 - 4") == "6"


def test_multiplication():
    assert answer("5*8") == "40"


def test_division_exact():
    assert answer("20 / 4") == "5"


def test_khmer_school_operators():
    assert answer("6 × 7") == "42"
    assert answer("42 ÷ 6") == "7"


# --- precedence and parentheses -------------------------------------------


def test_operator_precedence():
    assert answer("2 + 3 * 4") == "14"
    assert answer("10 - 6 / 2") == "7"


def test_parentheses_override_precedence():
    assert answer("(2 + 3) * 4") == "20"


def test_nested_parentheses():
    assert answer("((1 + 2) * (3 + 4))") == "21"


def test_unary_minus():
    assert answer("-5 + 8") == "3"


# --- fractions (exact) -----------------------------------------------------


def test_fraction_addition_exact():
    assert answer("1/2 + 1/4") == "3/4"  # not 0.75


def test_fraction_result_simplified():
    assert answer("1/4 + 1/4") == "1/2"


def test_fraction_multiplication():
    assert answer("2/3 * 3/4") == "1/2"


def test_fraction_subtraction():
    assert answer("5/6 - 1/3") == "1/2"


def test_fraction_steps_show_common_denominator():
    steps = format_steps(solve("1/2 + 1/4"))
    joined = " | ".join(steps)
    assert "common denominator" in joined
    assert "2/4" in joined  # 1/2 rewritten over 4
    assert "3/4" in joined


# --- decimals --------------------------------------------------------------


def test_decimals_stay_decimal():
    assert answer("1.5 + 2.25") == "3.75"


def test_decimal_addition_is_exact():
    assert answer("0.1 + 0.2") == "0.3"  # no float noise


def test_decimal_times_integer():
    assert answer("2.5 * 4") == "10"


# --- percentages -----------------------------------------------------------


def test_percent_of():
    assert answer("25% of 80") == "20"


def test_percent_of_in_larger_expression():
    assert answer("25% of 80 + 10") == "30"


def test_percent_of_steps():
    steps = format_steps(solve("25% of 80"))
    assert any("25/100" in step for step in steps)


def test_percent_without_of_rejected():
    with pytest.raises(SolverError):
        solve("25% + 1")


# --- Khmer numerals --------------------------------------------------------


def test_khmer_numeral_normalization():
    assert normalize_expression("៥*៨") == "5*8"


def test_khmer_numeral_multiplication():
    assert answer("៥*៨") == "40"


def test_khmer_numeral_fraction():
    assert answer("១/២ + ១/៤") == "3/4"


def test_khmer_numerals_with_khmer_operators():
    assert answer("៦ × ៧") == "42"


# --- errors: safe, structured, never a crash -------------------------------


def test_division_by_zero_is_solver_error():
    with pytest.raises(SolverError):
        solve("5 / 0")


def test_division_by_zero_inside_parentheses():
    with pytest.raises(SolverError):
        solve("1 / (2 - 2)")


def test_injection_dunder_rejected():
    with pytest.raises(SolverError):
        solve("__import__('os').system('ls')")


def test_letters_rejected():
    with pytest.raises(SolverError):
        solve("two + two")


def test_function_call_rejected():
    with pytest.raises(SolverError):
        solve("pow(2, 10)")


def test_empty_expression_rejected():
    with pytest.raises(SolverError):
        solve("   ")


def test_unbalanced_parentheses_rejected():
    with pytest.raises(SolverError):
        solve("(1 + 2")


def test_trailing_operator_rejected():
    with pytest.raises(SolverError):
        solve("5 +")


def test_overlong_expression_rejected():
    with pytest.raises(SolverError):
        solve("1+" * 400 + "1")


# --- contract: answers are always strings ----------------------------------


@pytest.mark.parametrize(
    "expression",
    ["5*8", "1/2 + 1/4", "1.5 + 2.25", "25% of 80", "៥*៨", "-3 * 2"],
)
def test_answer_is_always_str(expression):
    result = solve(expression)
    assert isinstance(result.answer, str)
    assert all(isinstance(step, str) for step in format_steps(result))
