"""Pydantic schemas shared by every Tunsay service.

Mirrors frontend_tunsay/src/types.ts. The frontend is the customer here: these models
were derived from working UI code, not designed ahead of it. See .claude/contracts.md.
"""

from dal.schemas.base import BilingualText, TunsayModel
from dal.schemas.chat import (
    AnswerRequest,
    AnswerResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
)
from dal.schemas.enums import (
    AnalogyType,
    InputFormat,
    Language,
    MessageSender,
    Subject,
    UserMode,
)
from dal.schemas.grades import (
    FOCUS_GRADES,
    GRADE_MAX,
    GRADE_MIN,
    set_supported_grades,
    supported_grades,
    validate_grade,
)
from dal.schemas.problem import (
    ExplainDifferently,
    Hint3,
    HomeworkProblem,
    PublicHomeworkProblem,
    PublicStepItem,
    StepItem,
)
from dal.schemas.user import (
    LoginRequest,
    RegisterRequest,
    SchoolContext,
    TokenResponse,
    UserProfile,
)

__all__ = [
    "AnalogyType",
    "AnswerRequest",
    "AnswerResponse",
    "BilingualText",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ExplainDifferently",
    "FOCUS_GRADES",
    "GRADE_MAX",
    "GRADE_MIN",
    "Hint3",
    "HomeworkProblem",
    "InputFormat",
    "Language",
    "LoginRequest",
    "MessageSender",
    "PublicHomeworkProblem",
    "PublicStepItem",
    "RegisterRequest",
    "SchoolContext",
    "StepItem",
    "Subject",
    "TokenResponse",
    "TunsayModel",
    "UserMode",
    "UserProfile",
    "set_supported_grades",
    "supported_grades",
    "validate_grade",
]
