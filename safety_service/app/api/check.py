"""POST /check — router only: parse, delegate to core, serialize.

A block is a normal result (HTTP 200 with is_safe=false), never an HTTP error.
The child's text is never echoed back and never logged (children's data).
"""

from __future__ import annotations

from fastapi import APIRouter

from ..core import age_gate, content_filter
from ..schemas import CheckRequest, CheckResponse

router = APIRouter()


@router.post("/check", response_model=CheckResponse)
async def check(request: CheckRequest) -> CheckResponse:
    if request.direction == "output":
        verdict = age_gate.screen_output(request.text)
    else:
        verdict = content_filter.check(request.text)

    refusal_khmer, refusal_eng = content_filter.refusal_for(verdict.reason)
    return CheckResponse(
        is_safe=verdict.is_safe,
        reason=verdict.reason,
        refusal_khmer=refusal_khmer,
        refusal_eng=refusal_eng,
    )
