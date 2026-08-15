"""Pure arithmetic parsing and evaluation for grade 4-6 math.

Scope (deliberately thin, per plan P1.5): the four operations, fractions,
decimals, and "N% of X" percentages. No word problems, no LLM, no eval().

Khmer numerals (០១២៣៤៥៦៧៨៩) and the school operators × and ÷ are
normalized before parsing, because that is what Khmer children type.

Everything here is a pure function; no FastAPI imports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

__all__ = ["SolverError", "SolveResult", "normalize_expression", "solve"]

# ---------------------------------------------------------------------------
# Errors and result types
# ---------------------------------------------------------------------------


class SolverError(ValueError):
    """Raised for any expression we cannot (or will not) solve.

    The message is safe to show to the caller: no stack traces, no internals.
    """


@dataclass
class Operation:
    """One recorded arithmetic step, consumed by step_formatter."""

    kind: str  # "binary" | "percent_of" | "simplify"
    op: str = ""  # "+", "-", "*", "/" for binary ops
    left: Optional[Fraction] = None
    right: Optional[Fraction] = None
    result: Optional[Fraction] = None
    # For fraction addition/subtraction with unlike denominators:
    # the two operands rewritten over the common denominator, plus that
    # denominator and the un-reduced result (numerator, denominator).
    common_denominator: Optional[int] = None
    rewritten: Optional[tuple[tuple[int, int], tuple[int, int]]] = None
    raw_result: Optional[tuple[int, int]] = None


@dataclass
class SolveResult:
    expression: str  # the normalized expression that was solved
    value: Fraction  # exact value
    answer: str  # formatted answer, always a string
    prefer_decimal: bool  # True when the input used decimal notation
    operations: list[Operation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"
_KHMER_TO_ASCII = {ord(k): str(i) for i, k in enumerate(_KHMER_DIGITS)}
_OPERATOR_ALIASES = {ord("×"): "*", ord("÷"): "/", ord("−"): "-"}


def normalize_expression(expression: str) -> str:
    """Map Khmer numerals and school operator glyphs to ASCII."""
    text = expression.translate(_KHMER_TO_ASCII).translate(_OPERATOR_ALIASES)
    return text.strip()


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<number>\d+(?:\.\d+)?)
      | (?P<of>of\b)
      | (?P<op>[+\-*/()%])
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


@dataclass
class Token:
    kind: str  # "number" | "of" | one of "+-*/()%"
    text: str


def _tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if match is None:
            bad = text[pos:].lstrip()[:1] or text[pos]
            raise SolverError(
                f"I can only solve arithmetic with numbers, + - * / ( ) and "
                f"percentages. I don't understand {bad!r}."
            )
        if match.group("number") is not None:
            tokens.append(Token("number", match.group("number")))
        elif match.group("of") is not None:
            tokens.append(Token("of", "of"))
        else:
            op = match.group("op")
            tokens.append(Token(op, op))
        pos = match.end()
    return tokens


# ---------------------------------------------------------------------------
# Parser (recursive descent) -> immediate evaluation with an operation trace
# ---------------------------------------------------------------------------
#
# Grammar:
#   expr   := term (("+" | "-") term)*
#   term   := factor (("*" | "/") factor)*
#   factor := "-" factor | atom
#   atom   := NUMBER ["%" "of" factor] | "(" expr ")"


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.operations: list[Operation] = []
        self.saw_decimal = False

    # -- token helpers ----------------------------------------------------

    def _peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> Token:
        token = self._peek()
        if token is None:
            raise SolverError("The expression ends too soon — is a number missing?")
        self.pos += 1
        return token

    # -- grammar ----------------------------------------------------------

    def parse(self) -> Fraction:
        if not self.tokens:
            raise SolverError("The expression is empty.")
        value = self.expr()
        leftover = self._peek()
        if leftover is not None:
            raise SolverError(
                f"I got confused at {leftover.text!r} — check the expression."
            )
        return value

    def expr(self) -> Fraction:
        value = self.term()
        while (token := self._peek()) is not None and token.kind in "+-":
            self._next()
            right = self.term()
            value = self._apply(token.kind, value, right)
        return value

    def term(self) -> Fraction:
        value = self.factor()
        while (token := self._peek()) is not None and token.kind in "*/":
            self._next()
            right = self.factor()
            value = self._apply(token.kind, value, right)
        return value

    def factor(self) -> Fraction:
        token = self._peek()
        if token is not None and token.kind == "-":
            self._next()
            return -self.factor()
        return self.atom()

    def atom(self) -> Fraction:
        token = self._next()
        if token.kind == "(":
            value = self.expr()
            closing = self._peek()
            if closing is None or closing.kind != ")":
                raise SolverError("A closing parenthesis ')' is missing.")
            self._next()
            return value
        if token.kind == "number":
            value = self._to_fraction(token.text)
            if (nxt := self._peek()) is not None and nxt.kind == "%":
                self._next()
                of_token = self._peek()
                if of_token is None or of_token.kind != "of":
                    raise SolverError(
                        "Percentages must look like '25% of 80' — "
                        "the 'of <number>' part is missing."
                    )
                self._next()
                base = self.factor()
                result = value / 100 * base
                self.operations.append(
                    Operation(kind="percent_of", left=value, right=base, result=result)
                )
                return result
            return value
        raise SolverError(
            f"I got confused at {token.text!r} — check the expression."
        )

    # -- evaluation -------------------------------------------------------

    def _to_fraction(self, text: str) -> Fraction:
        if "." in text:
            self.saw_decimal = True
        return Fraction(text)  # exact, including "3.25"

    def _apply(self, op: str, left: Fraction, right: Fraction) -> Fraction:
        operation = Operation(kind="binary", op=op, left=left, right=right)
        if op == "+":
            result = left + right
        elif op == "-":
            result = left - right
        elif op == "*":
            result = left * right
        else:  # "/"
            if right == 0:
                raise SolverError("Division by zero is not allowed — you cannot share among zero groups!")
            result = left / right
        # Record common-denominator detail for unlike-fraction +/- so the
        # step formatter can show the working a teacher would expect.
        if (
            op in "+-"
            and left.denominator != 1
            and right.denominator != 1
            and left.denominator != right.denominator
            and not self.saw_decimal
        ):
            common = _lcm(left.denominator, right.denominator)
            l_num = left.numerator * (common // left.denominator)
            r_num = right.numerator * (common // right.denominator)
            raw = l_num + r_num if op == "+" else l_num - r_num
            operation.common_denominator = common
            operation.rewritten = ((l_num, common), (r_num, common))
            operation.raw_result = (raw, common)
        operation.result = result
        self.operations.append(operation)
        return result


def _lcm(a: int, b: int) -> int:
    from math import gcd

    return a * b // gcd(a, b)


# ---------------------------------------------------------------------------
# Answer formatting
# ---------------------------------------------------------------------------


def format_value(value: Fraction, prefer_decimal: bool = False) -> str:
    """Format an exact value the way a grade-school answer sheet would.

    Whole numbers print bare ("40"); fraction inputs keep fraction form
    ("3/4"); decimal inputs print exact terminating decimals ("0.3"),
    falling back to fraction form if the decimal would not terminate.
    """
    if value.denominator == 1:
        return str(value.numerator)
    if prefer_decimal:
        decimal = _terminating_decimal(value)
        if decimal is not None:
            return decimal
    return f"{value.numerator}/{value.denominator}"


def _terminating_decimal(value: Fraction) -> Optional[str]:
    den = value.denominator
    exp2 = exp5 = 0
    while den % 2 == 0:
        den //= 2
        exp2 += 1
    while den % 5 == 0:
        den //= 5
        exp5 += 1
    if den != 1:
        return None  # non-terminating; caller falls back to fraction form
    places = max(exp2, exp5)
    scaled = abs(value.numerator) * 10**places // value.denominator
    digits = str(scaled).rjust(places + 1, "0")
    sign = "-" if value < 0 else ""
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


# ---------------------------------------------------------------------------
# Entry point (grade-agnostic: algebra will be added beside this later)
# ---------------------------------------------------------------------------

_MAX_LENGTH = 500


def solve(expression: str) -> SolveResult:
    """Solve a grade 4-6 arithmetic expression exactly.

    Raises SolverError with a caller-safe message for anything invalid.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise SolverError("The expression is empty.")
    if len(expression) > _MAX_LENGTH:
        raise SolverError("That expression is too long for me to solve.")

    normalized = normalize_expression(expression)
    parser = _Parser(_tokenize(normalized))
    value = parser.parse()
    answer = format_value(value, prefer_decimal=parser.saw_decimal)
    return SolveResult(
        expression=normalized,
        value=value,
        answer=answer,
        prefer_decimal=parser.saw_decimal,
        operations=parser.operations,
    )
