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


def _get_grade_analogy(expression: str, grade: int, language: str) -> str:
    is_km = language == "km"
    if grade <= 3:
        if is_km:
            return f"ដើម្បីគណនា {expression}៖ ស្រមៃថាអ្នកមានផ្លែប៉ោម ឬខ្មៅដៃជាក្រុម... យើងអាចបំបែកលេខ និងរាប់ម្តងមួយក្រុម!"
        return f"To solve {expression}: Imagine you have groups of items (like apples or pencils)... We can group and count them step by step!"
    elif grade <= 6:
        if is_km:
            return f"ដើម្បីគណនា {expression}៖ យើងអាចបំបែកលេខ (ឧទាហរណ៍ ៥៥ = ៥០ + ៥) ឬស្រមៃមើលប្រអប់ចំនួន ២២ ដែលក្នុងមួយប្រអប់មាន ៥៥ ផ្លែប៉ោម!"
        return f"To solve {expression}: We can break numbers into tens and ones (or imagine equal boxes of items like 5 apples) to multiply step by step!"
    elif grade <= 9:
        if is_km:
            return f"ដើម្បីគណនា {expression}៖ ប្រើប្រាស់លក្ខណៈបំបែកនៃវិធីគុណ (ឧទាហរណ៍ ២២ × (៥០ + ៥)) ដើម្បីគណនាបានងាយស្រួល!"
        return f"To solve {expression}: Use the distributive property (e.g., 22 × (50 + 5)) to simplify and solve step by step!"
    else:
        if is_km:
            return f"ដើម្បីគណនា {expression}៖ ពិនិត្យមើលរចនាសម្ព័ន្ធនៃសមីការ និងបំបែកជាកត្តាមួយៗ!"
        return f"To solve {expression}: Analyze the mathematical structure and decompose into simpler intermediate components step by step!"


def _voice_answer(answer: str, steps: list[str], language: str, is_parent: bool, grade: int = 4) -> dict:
    if is_parent:
        lines = list(steps or [])
        if language == "km":
            lines.append(f"ចម្លើយគឺ {answer}! 🐰")
            return {"text_khmer": "\n".join(lines), "text_eng": ""}
        lines.append(f"The answer is {answer}! 🐰")
        return {"text_khmer": "", "text_eng": "\n".join(lines)}

    # Student mode: Socratic guidance with grade-appropriate real-world explanation & example
    lines = []
    expr_label = ""
    for step in (steps or []):
        if " = " in step:
            parts = step.rsplit(" = ", 1)
            expr_label = parts[0]
            lines.append(f"{parts[0]} = ?")
        else:
            lines.append(step)

    explanation = _get_grade_analogy(expr_label or "this problem", grade, language)
    lines.append(explanation)

    if language == "km":
        lines.append("តោះសាកល្បងគិតចម្លើយចុងក្រោយទាំងអស់គ្នាណា! 🐰")
        return {"text_khmer": "\n".join(lines), "text_eng": ""}
    lines.append("Let me know what you get for the final step! 🐰")
    return {"text_khmer": "", "text_eng": "\n".join(lines)}


async def solve(state: GraphState, clients: ServiceClients) -> dict:
    mode = state.get("mode", "student")
    if hasattr(mode, "value"):
        mode = mode.value
    is_parent = str(mode).lower() == "parent"
    language = state.get("language", "km")
    grade = state.get("grade", 4)
    prompt = state.get("prompt") or state.get("normalized_prompt") or ""

    try:
        result = await clients.solver.solve(state.get("normalized_prompt", ""))
    except (SolverUnparseable, ServiceUnavailable):
        # Not actually solvable arithmetic (or solver down) — hand the prompt to explain.
        return {"intent": "explain"}

    if is_parent:
        return {
            "intent": "solve",
            "is_parent_help": True,
            **_voice_answer(
                str(result.get("answer", "")),
                result.get("steps") or [],
                language,
                is_parent=True,
                grade=grade,
            ),
        }

    # Student Mode: Primary path delegates to pedagogy_service (LLM generation with single-step Socratic prompt)
    transcript = state.get("transcript") or []
    history_str = ""
    if transcript:
        recent = transcript[-4:]  # Last 2 dialogue turns
        history_lines = []
        for msg in recent:
            sender = "Student" if msg.get("sender") == "user" else "Tunsay"
            text = msg.get("text_khmer") or msg.get("text_eng") or ""
            if text:
                history_lines.append(f"{sender}: {text}")
        if history_lines:
            history_str = "Recent Conversation History:\n" + "\n".join(history_lines)

    context_parts = [f"Math expression to solve: {prompt}."]
    if result.get("steps"):
        context_parts.append(f"Solver Steps: {result.get('steps')}")
    if history_str:
        context_parts.append(history_str)

    context = "\n\n".join(context_parts)

    try:
        explanation = await clients.pedagogy.explain(
            prompt=prompt,
            grade=grade,
            language=language,
            mode="student",
            context=context,
        )
        text_km = explanation.get("text_khmer") or ""
        text_en = explanation.get("text_eng") or ""
        if text_km or text_en:
            return {
                "intent": "solve",
                "is_parent_help": False,
                "text_khmer": text_km,
                "text_eng": text_en,
            }
    except (ServiceUnavailable, Exception):
        pass

    # Static fallback ONLY when pedagogy_service is unreachable
    return {
        "intent": "solve",
        "is_parent_help": False,
        **_voice_answer(
            str(result.get("answer", "")),
            result.get("steps") or [],
            language,
            is_parent=False,
            grade=grade,
        ),
    }
