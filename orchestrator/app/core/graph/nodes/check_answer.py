"""Node 6 — check_answer compares student's answer using grading_service.

If incorrect, classifies the misconception and passes it to the explain node.
"""

from __future__ import annotations

from typing import Any
from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients, ServiceUnavailable

# Congratulatory messages for correct answers
CONGRATS_KHMER = "អបអរសាទរ! នោះជាចម្លើយត្រឹមត្រូវ។ 🎉"
CONGRATS_ENG = "Congratulations! That is the correct answer. 🎉"

def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    if language == "km":
        return khmer, ""
    return "", eng

async def check_answer(state: GraphState, clients: ServiceClients) -> dict[str, Any]:
    language = state.get("language", "km")
    problem_id = state.get("problem_id")
    active_step_index = state.get("active_step_index", 0)
    student_answer = state.get("prompt", "")

    if not problem_id:
        # Fallback if no problem is selected
        return {"is_correct": False, "intent": "explain"}

    try:
        problem = await clients.content.get_problem(problem_id)
    except ServiceUnavailable:
        return {
            "is_correct": False,
            "text_khmer": "មានបញ្ហាបច្ចេកទេសក្នុងការទាញយកលំហាត់។ សូមព្យាយាមម្តងទៀត។",
            "text_eng": "There was a technical issue fetching the problem. Please try again.",
            "intent": "explain"
        }

    if not problem:
        return {"is_correct": False, "intent": "explain"}

    steps = problem.get("steps") or []
    if active_step_index < 0 or active_step_index >= len(steps):
        return {"is_correct": False, "intent": "explain"}

    step = steps[active_step_index]
    correct_answer = step.get("correct_answer", "")
    input_format = step.get("input_format", "number")
    options = step.get("options")
    question_text = step.get("question_khmer") if language == "km" else step.get("question_eng")

    try:
        result = await clients.grading.grade(
            correct_answer=correct_answer,
            student_answer=student_answer,
            input_format=input_format,
            options=options,
            language=language,
            question_text=question_text or ""
        )
        is_correct = result.get("is_correct", False)
        misconception_code = result.get("misconception_code")
    except ServiceUnavailable:
        # Fallback to local string matching if grading_service is down
        norm_student = student_answer.strip().lower()
        norm_correct = correct_answer.strip().lower()
        is_correct = norm_student == norm_correct or norm_correct in norm_student
        misconception_code = None

    # Notify profile service of the attempt
    student_id = state.get("student_id")
    step_id = step.get("id")
    if student_id and problem_id and step_id:
        try:
            await clients.profile.record_attempt(
                student_id=student_id,
                problem_id=problem_id,
                step_id=step_id,
                is_correct=is_correct,
            )
        except ServiceUnavailable:
            pass

    if is_correct:
        txt_km, txt_en = _pick(CONGRATS_KHMER, CONGRATS_ENG, language)
        
        # Advance the step index
        next_step_index = active_step_index + 1
        is_completed = next_step_index >= len(steps)
        
        return {
            "is_correct": True,
            "misconception_code": None,
            "text_khmer": txt_km,
            "text_eng": txt_en,
            "active_step_index": next_step_index if not is_completed else active_step_index,
            "intent": "congratulate"
        }
    else:
        # For incorrect answer, we want the graph to transition to the explain node
        # We pass the misconception_code in the state
        return {
            "is_correct": False,
            "misconception_code": misconception_code,
            "intent": "explain"
        }
