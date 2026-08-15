"""User, profile and auth schemas.

There is no password and no email anywhere in this product. LoginView.tsx collects a
school code, a Khmer display name and an optional 4-digit PIN — the users are 6-12 years
old. See .claude/contracts.md section 4 "Auth credentials".

**There is exactly one role: student.** No Role enum, no account types, no
parent_student_link. The frontend has no account-type picker and never sends one; teachers
appear only as prose ("your teacher gave you a code"). Do not confuse this with
:class:`~dal.schemas.enums.UserMode`, which is an in-app student/parent *toggle* on the
same student account.
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator

from dal.schemas.base import TunsayModel
from dal.schemas.enums import Language, Subject, UserMode
from dal.schemas.grades import validate_grade

NonBlank = Annotated[str, Field(min_length=1)]
Pin = Annotated[str, Field(min_length=4, max_length=4, pattern=r"^\d{4}$")]


class UserProfile(TunsayModel):
    """What the app renders for the signed-in child.

    ``name`` is a display string like "សុជា (Sochea)" — Khmer with a parenthesised Latin
    transliteration, which utils/language.ts::getDisplayName splits. It is *not* an
    identifier on its own: two children in different schools may share a name.
    """

    name: NonBlank
    grade: int
    subject: Subject = Subject.MATH
    mode: UserMode = UserMode.STUDENT
    language: Language = Language.KHMER
    completed_problems_count: int = Field(default=0, ge=0)
    stars_earned: int = Field(default=0, ge=0)

    _validate_grade = field_validator("grade")(lambda cls, v: validate_grade(v))


class SchoolContext(TunsayModel):
    """What a school code resolves to. LoginView.tsx hardcodes this today; auth_service
    must serve it from a schools/classes table.

    Stored as flat fields rather than a school -> class -> student hierarchy: real
    multi-tenancy is deferred (.claude/claude.md section 4), but the login UI already
    depends on codes and class names, so they cannot simply be dropped.
    """

    school_code: NonBlank
    school_name: str | None = None
    class_name: str | None = None
    grade: int | None = None
    subject_track: str | None = None

    @field_validator("grade")
    @classmethod
    def _check_grade(cls, v: int | None) -> int | None:
        return None if v is None else validate_grade(v)


class RegisterRequest(TunsayModel):
    """Covers both entry flows in LoginView.tsx.

    - school-code:    school_code + student_name, PIN optional
    - public-signup:  student_name + grade, parent_contact + PIN

    A school-code signup may omit ``grade`` because the code resolves it.
    """

    student_name: NonBlank
    school_code: str | None = None
    class_name: str | None = None
    grade: int | None = None
    parent_contact: str | None = None
    pin: Pin | None = None
    language: Language = Language.KHMER

    @field_validator("grade")
    @classmethod
    def _check_grade(cls, v: int | None) -> int | None:
        return None if v is None else validate_grade(v)

    @model_validator(mode="after")
    def _need_school_code_or_grade(self) -> Self:
        if not self.school_code and self.grade is None:
            raise ValueError(
                "provide school_code (which resolves the grade) or an explicit grade"
            )
        return self


class LoginRequest(TunsayModel):
    """The returning-login flow accepts a school code *or* a student name, plus the PIN.

    A 4-digit PIN is 10,000 combinations, so auth_service must throttle by
    (school_code, student_name) — the PIN is not a secret on its own.
    """

    student_name: str | None = None
    school_code: str | None = None
    pin: Pin | None = None

    @model_validator(mode="after")
    def _need_an_identifier(self) -> Self:
        if not self.student_name and not self.school_code:
            raise ValueError("provide student_name or school_code")
        return self


class TokenResponse(TunsayModel):
    access_token: NonBlank
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)
    profile: UserProfile
