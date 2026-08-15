"""Structured, bilingual gateway errors.

Every failure the gateway authors itself carries a stable machine ``error``
code plus Tunsay-voiced Khmer AND English messages — authored content is
always bilingual (.claude/contracts.md section 3); a child never sees a stack
trace or an English-only error (.claude/claude.md section 5).

Judgment call: these bodies use camelCase keys (``messageKhmer``) because the
gateway is the camelCase side of the boundary — its own responses go straight
to the browser and must not need a second translation pass.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def _detail(error: str, message_khmer: str, message_eng: str, **extra: Any) -> dict[str, Any]:
    return {
        "detail": {
            "error": error,
            "messageKhmer": message_khmer,
            "messageEng": message_eng,
            **extra,
        }
    }


def unauthorized_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=_detail(
            "not_authenticated",
            "សូមចូលគណនីជាមុនសិន ទើបទន្សាយអាចជួយអ្នកបាន។ 🐰",
            "Please log in first so Tunsay can help you. 🐰",
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )


def rate_limited_response(retry_after_seconds: int) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=_detail(
            "rate_limited",
            "សំណួរច្រើនណាស់! សូមសម្រាកបន្តិចសិន រួចទន្សាយនឹងជួយបន្តទៀត។ 🐰",
            "So many questions! Take a little break, and Tunsay will help again soon. 🐰",
            retryAfterSeconds=retry_after_seconds,
        ),
        headers={"Retry-After": str(retry_after_seconds)},
    )


def upstream_unreachable_response() -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=_detail(
            "upstream_unreachable",
            "ទន្សាយមានបញ្ហាក្នុងការភ្ជាប់ទៅអ្នកជំនួយរបស់ខ្លួនបន្តិច។ សូមព្យាយាមម្តងទៀតក្នុងពេលបន្តិចទៀតណា។ 🐰",
            "Tunsay is having trouble reaching its helpers right now. Please try again in a moment. 🐰",
        ),
    )
