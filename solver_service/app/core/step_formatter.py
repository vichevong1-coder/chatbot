"""Turn a SolveResult's operation trace into ordered, human-readable steps.

Pure functions, no FastAPI imports. Steps are simple English strings for
now; bilingual step text is a later phase (pedagogy_service owns voice).
"""

from __future__ import annotations

from fractions import Fraction

from app.core.math_solver import Operation, SolveResult, format_value

__all__ = ["format_steps"]

_DISPLAY_OP = {"+": "+", "-": "-", "*": "×", "/": "÷"}


def _fmt(value: Fraction, prefer_decimal: bool) -> str:
    return format_value(value, prefer_decimal=prefer_decimal)


def format_steps(result: SolveResult) -> list[str]:
    """Ordered working steps, innermost operation first."""
    steps: list[str] = []
    dec = result.prefer_decimal
    for op in result.operations:
        if op.kind == "percent_of":
            percent = _fmt(op.left, dec)
            base = _fmt(op.right, dec)
            steps.append(
                f"{percent}% of {base} means {percent}/100 × {base}"
            )
            steps.append(
                f"{percent}/100 × {base} = {_fmt(op.result, dec)}"
            )
        elif op.kind == "binary":
            steps.extend(_binary_steps(op, dec))
    if not steps:
        # A bare number (or just parentheses/unary minus around one).
        steps.append(f"{result.expression} = {result.answer}")
    return steps


def _binary_steps(op: Operation, prefer_decimal: bool) -> list[str]:
    symbol = _DISPLAY_OP[op.op]
    left = _fmt(op.left, prefer_decimal)
    right = _fmt(op.right, prefer_decimal)
    result = _fmt(op.result, prefer_decimal)

    if op.common_denominator is None:
        return [f"{left} {symbol} {right} = {result}"]

    # Unlike-denominator fraction addition/subtraction: show the common
    # denominator rewrite, the combine step, and any simplification.
    (l_num, common), (r_num, _) = op.rewritten
    raw_num, raw_den = op.raw_result
    steps = [
        f"Find a common denominator for {left} and {right}: it is {common}, "
        f"so {left} = {l_num}/{common} and {right} = {r_num}/{common}",
        f"{l_num}/{common} {symbol} {r_num}/{common} = {raw_num}/{raw_den}",
    ]
    reduced = Fraction(raw_num, raw_den)
    if (reduced.numerator, reduced.denominator) != (raw_num, raw_den):
        steps.append(f"Simplify: {raw_num}/{raw_den} = {result}")
    return steps
