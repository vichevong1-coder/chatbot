"""Chat and answer-checking wire schemas.

These replace the frontend's current POST /api/tutor contract, which is stateless,
unauthenticated and carries no history. See .claude/contracts.md section 4.
"""

from __future__ import annotations

from typing import Annotated
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from pydantic import Field, model_validator

from dal.schemas.base import TunsayModel
from dal.schemas.enums import Language, MessageSender, UserMode
from dal.schemas.problem import PublicHomeworkProblem

NonBlank = Annotated[str, Field(min_length=1)]


class ChatMessage(TunsayModel):
    """One turn in the transcript.

    ``is_safety_refusal`` and ``is_parent_help`` are render flags: they pick the bubble
    colour in ChatView.tsx (pink refusal, yellow parent). The backend must set them —
    the frontend will not infer them.
    """

    id: NonBlank
    sender: MessageSender
    text_khmer: str = ""
    text_eng: str = ""
    timestamp: str
    image_uri: str | None = None
    problem: PublicHomeworkProblem | None = None
    active_step_index: int | None = Field(default=None, ge=0)
    is_safety_refusal: bool = False
    is_parent_help: bool = False

    @model_validator(mode="after")
    def _at_least_one_language(self) -> Self:
        """Generated content may be single-language, but not no-language.

        Empty string rather than None is deliberate: ChatView.tsx falls back with
        ``textKhmer || textEng``, which relies on "" being falsy.
        """
        if not self.text_khmer and not self.text_eng:
            raise ValueError(
                f"message {self.id!r}: at least one of text_khmer/text_eng must be set"
            )
        return self


class ChatRequest(TunsayModel):
    """POST /chat.

    ``student_id`` is injected by the gateway from the verified JWT and **overwrites**
    anything the client sent, or a child could impersonate a classmate. ``problem_id``
    replaces the frontend's habit of posting the whole problem back up — the orchestrator
    loads it from content_service rather than trusting a client blob.
    """

    session_id: NonBlank
    student_id: NonBlank
    prompt: NonBlank
    mode: UserMode = UserMode.STUDENT
    language: Language = Language.KHMER
    problem_id: str | None = None
    active_step_index: int | None = Field(default=None, ge=0)


class ChatResponse(TunsayModel):
    """The tutor's reply.

    Per the bilingual rule (.claude/contracts.md section 3), *generated* content fills the
    requested language and leaves the other as "". Authored content must fill both.
    """

    text_khmer: str = ""
    text_eng: str = ""
    is_safety_refusal: bool = False
    is_parent_help: bool = False
    session_id: NonBlank
    suggested_next: str | None = None

    @model_validator(mode="after")
    def _at_least_one_language(self) -> Self:
        if not self.text_khmer and not self.text_eng:
            raise ValueError("at least one of text_khmer/text_eng must be set")
        return self


class AnswerRequest(TunsayModel):
    """POST /answers — server-side answer checking.

    Exists because ChatView.tsx currently grades in the browser with a substring compare,
    so "55" scores correct against "5". See .claude/contracts.md section 4.
    """

    session_id: NonBlank
    student_id: str | None = None
    problem_id: NonBlank
    step_id: NonBlank
    student_answer: str
    language: Language = Language.KHMER


class AnswerResponse(TunsayModel):
    """``misconception_code`` is the input to misconception-aware pedagogy (P2.2) and to
    mastery modelling (P2.3), so it is a stable code, never free text."""

    is_correct: bool
    misconception_code: str | None = None
    feedback_khmer: str = ""
    feedback_eng: str = ""
    advance_to_step: int | None = Field(default=None, ge=0)


class HintRequest(TunsayModel):
    """POST /hints — request an AI-generated progressive hint for a problem step."""

    session_id: NonBlank
    student_id: str | None = None
    problem_id: NonBlank
    step_id: NonBlank
    hint_level: int = Field(default=1, ge=1, le=3)
    language: Language = Language.KHMER


class HintResponse(TunsayModel):
    """Bilingual AI-generated hint response."""

    hint_khmer: str = ""
    hint_eng: str = ""
    hint_level: int = 1
