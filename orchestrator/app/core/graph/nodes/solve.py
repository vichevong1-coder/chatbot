"""Node 4 — solver_service computes bare arithmetic; Tunsay voices the answer.

If the solver rejects the expression (422) or is down, the node falls through to
the explain path by resetting ``intent`` — the child still gets a tutor answer,
never an error.
"""

from __future__ import annotations

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import (
    ServiceClients,
    ServiceUnavailable,
    SolverUnparseable,
)


def _voice_answer(answer: str, steps: list[str], language: str) -> dict:
    lines = list(steps or [])
    if language == "km":
        lines.append(f"ចម្លើយគឺ {answer}! 🐰")
        return {"text_khmer": "\n".join(lines), "text_eng": ""}
    lines.append(f"The answer is {answer}! 🐰")
    return {"text_khmer": "", "text_eng": "\n".join(lines)}


async def solve(state: GraphState, clients: ServiceClients) -> dict:
    try:
        result = await clients.solver.solve(state.get("normalized_prompt", ""))
    except (SolverUnparseable, ServiceUnavailable):
        # Not actually solvable arithmetic (or solver down) — hand the prompt
        # to the explain path instead of failing at the child.
        return {"intent": "explain"}

    return {
        "intent": "solve",
        "is_parent_help": False,
        **_voice_answer(
            str(result.get("answer", "")),
            result.get("steps") or [],
            state.get("language", "km"),
        ),
    }
