"""Structured, bilingual auth errors.

Every failure carries a stable machine ``error`` code plus Tunsay-voiced Khmer and
English messages (.claude/claude.md section 5: a child never sees an English-only
error). Auth failures deliberately do not reveal *which* part was wrong.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def _detail(error: str, message_khmer: str, message_eng: str, **extra: Any) -> dict[str, Any]:
    return {
        "error": error,
        "message_khmer": message_khmer,
        "message_eng": message_eng,
        **extra,
    }


def unknown_school_code(code: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=_detail(
            "unknown_school_code",
            "រកមិនឃើញលេខកូដសាលានេះទេ។ សូមពិនិត្យជាមួយគ្រូរបស់អ្នក។",
            "We couldn't find that school code. Please check it with your teacher.",
            school_code=code,
        ),
    )


def duplicate_student() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail=_detail(
            "duplicate_student",
            "ឈ្មោះនេះបានចុះឈ្មោះនៅសាលានេះរួចហើយ។ សូមព្យាយាមចូលវិញ។",
            "That name is already registered at this school. Try logging in instead.",
        ),
    )


def grade_unresolved() -> HTTPException:
    return HTTPException(
        status_code=422,
        detail=_detail(
            "grade_unresolved",
            "យើងមិនអាចដឹងថ្នាក់របស់អ្នកទេ។ សូមប្រាប់ថ្នាក់របស់អ្នក។",
            "We couldn't work out your grade. Please tell us your grade.",
        ),
    )


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=_detail(
            "invalid_credentials",
            "ឈ្មោះ ឬលេខសម្ងាត់មិនត្រឹមត្រូវទេ។ សូមព្យាយាមម្តងទៀត។",
            "That name or PIN doesn't match. Please try again.",
        ),
    )


def too_many_attempts(retry_after_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail=_detail(
            "too_many_attempts",
            "ព្យាយាមច្រើនដងពេកហើយ។ សូមរង់ចាំបន្តិច រួចព្យាយាមម្តងទៀត។",
            "Too many tries. Please wait a little while, then try again.",
            retry_after_seconds=retry_after_seconds,
        ),
        headers={"Retry-After": str(retry_after_seconds)},
    )


def invalid_token() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=_detail(
            "invalid_token",
            "សូមចូលម្តងទៀត។",
            "Please log in again.",
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )
