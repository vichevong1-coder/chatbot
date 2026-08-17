"""Closed vocabularies shared across services.

Every value here is mirrored in frontend_tunsay/src/types.ts. Adding a member is a
breaking change on both sides — see .claude/contracts.md section 2.
"""

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class Language(StrEnum):
    KHMER = "km"
    ENGLISH = "en"


class Subject(StrEnum):
    MATH = "math"
    SCIENCE = "science"
    ENGLISH = "english"


class InputFormat(StrEnum):
    """Selects which answer widget StepCard.tsx renders."""

    MCQ = "mcq"
    NUMBER = "number"
    TEXT = "text"


class AnalogyType(StrEnum):
    """Selects the illustration in ExplanationCard.tsx.

    Adding a member here without a matching frontend change renders nothing.
    """

    APPLES = "apples"
    PIZZA = "pizza"
    WATER = "water"
    PLANTS = "plants"


class UserMode(StrEnum):
    """How the tutor is currently speaking — **not** an account type.

    Every account is a student (there is no Role enum; see dal/schemas/user.py). This is
    an in-app toggle owned by ModeSwitcher.tsx: a parent sitting with their child flips it
    to get "here is how to explain this", which may reveal the answer and the method.
    Student mode never does. It resets per session and is not stored on the user.
    """

    STUDENT = "student"
    PARENT = "parent"


class MessageSender(StrEnum):
    USER = "user"
    SAYO = "sayo"  # the mascot; "sayo" is the wire value the frontend already uses
    SYSTEM = "system"
