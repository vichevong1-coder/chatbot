"""Request/response models for safety_service (contracts.md §4).

Wire format is snake_case JSON — the gateway is the camelCase boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

try:  # shared enum from the dal package (claude.md §5)
    from dal.schemas import Language
except ImportError:  # pragma: no cover — Docker image without dal installed
    from enum import StrEnum

    class Language(StrEnum):  # type: ignore[no-redef]
        KHMER = "km"
        ENGLISH = "en"


class CheckRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str
    language: Language
    direction: Literal["input", "output"]


class CheckResponse(BaseModel):
    """Never contains the child's text — refusals are fixed authored strings."""

    is_safe: bool
    reason: str | None
    refusal_khmer: str
    refusal_eng: str
