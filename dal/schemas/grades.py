"""Grade policy.

Three different numbers get confused constantly, so they are named separately here
(see .claude/claude.md section 2):

  GRADE_MIN / GRADE_MAX   1..12   the product's eventual reach. A structural bound.
                                  Nothing outside it is ever a valid grade.
  supported grades        1..6    what the system accepts *today*. Configurable.
  focus grades            4..6    what the team is building first. A priority, NOT a
                                  validation rule — see the note below.

**Why the supported default is 1-6 and not 4-6.** The plan describes the focus band as
"4-6 today", but the seed corpus shipped with the product contains grade 3 problems
(math-g3-perimeter, english-g3-continuous), and frontend_tunsay/src/types.ts declares
``Grade = 1|2|3|4|5|6``. Defaulting the *validator* to 4-6 would reject content the product
already ships and the UI can already render. So the supported set is what the UI can
represent; 4-6 stays a roadmap priority, not a constraint enforced here.

Widening to grade 9 is a config change, never a schema edit::

    TUNSAY_SUPPORTED_GRADES=1-9        # range
    TUNSAY_SUPPORTED_GRADES=4,5,6,9    # explicit list
"""

from __future__ import annotations

import os

GRADE_MIN = 1
GRADE_MAX = 12

FOCUS_GRADES: frozenset[int] = frozenset({4, 5, 6})
"""Roadmap priority only. Deliberately not consulted by any validator."""

_DEFAULT_SUPPORTED = frozenset(range(1, 7))
_ENV_VAR = "TUNSAY_SUPPORTED_GRADES"


def _parse(spec: str) -> frozenset[int]:
    """Parse "1-6" or "4,5,6" or "1-3,9" into a set of grades."""
    grades: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            low, _, high = chunk.partition("-")
            grades.update(range(int(low), int(high) + 1))
        else:
            grades.add(int(chunk))
    if not grades:
        raise ValueError(f"{_ENV_VAR} parsed to an empty set: {spec!r}")
    out_of_range = sorted(g for g in grades if not GRADE_MIN <= g <= GRADE_MAX)
    if out_of_range:
        raise ValueError(
            f"{_ENV_VAR} contains grades outside {GRADE_MIN}-{GRADE_MAX}: {out_of_range}"
        )
    return frozenset(grades)


_override: frozenset[int] | None = None


def supported_grades() -> frozenset[int]:
    """The grades this deployment accepts. Read at validation time, not import time,
    so tests and services can change it without reimporting the schemas."""
    if _override is not None:
        return _override
    spec = os.environ.get(_ENV_VAR)
    return _parse(spec) if spec else _DEFAULT_SUPPORTED


def set_supported_grades(grades: frozenset[int] | set[int] | None) -> None:
    """Override the supported set in-process. Pass None to fall back to env/default."""
    global _override
    _override = None if grades is None else _parse(",".join(str(g) for g in sorted(grades)))


def validate_grade(grade: int) -> int:
    """Validator shared by every schema carrying a grade."""
    if not GRADE_MIN <= grade <= GRADE_MAX:
        raise ValueError(
            f"grade {grade} is outside the product range {GRADE_MIN}-{GRADE_MAX}"
        )
    allowed = supported_grades()
    if grade not in allowed:
        raise ValueError(
            f"grade {grade} is not currently supported "
            f"(supported: {sorted(allowed)}; widen with {_ENV_VAR})"
        )
    return grade
