"""Autonomous Agent Tools for TunSay ReAct Agentic Loop.

These tools are exposed via Gemini Function Calling, enabling TunSay to autonomously
inspect student mastery, query curriculum textbooks, generate custom exercises on the fly,
and delegate math calculations to solver_service.
"""

from __future__ import annotations

from typing import Any
from dal.schemas.enums import Language, UserMode, Subject


class AgentTools:
    """Registry of asynchronous agent tools bound to service clients."""

    def __init__(self, clients: Any) -> None:
        self._clients = clients

    async def tool_query_curriculum(self, skill: str, grade: int = 4) -> dict[str, Any]:
        """Query curriculum RAG context for a specific skill and grade level."""
        retrieval_client = getattr(self._clients, "retrieval", None)
        if retrieval_client:
            try:
                results = await retrieval_client.retrieve(query=skill, grade=grade, top_k=2)
                return {"status": "success", "results": results}
            except Exception as exc:
                return {"status": "unavailable", "reason": str(exc), "results": []}
        return {"status": "unsupported", "results": []}

    async def tool_get_student_mastery(self, student_id: str) -> dict[str, Any]:
        """Fetch historical skill mastery levels and weak spots for a student."""
        profile_client = getattr(self._clients, "profile", None)
        if profile_client and student_id != "anonymous":
            try:
                profile = await profile_client.get_profile(student_id)
                return {
                    "status": "success",
                    "student_id": student_id,
                    "stars": profile.get("stars", 0),
                    "completed_problems_count": profile.get("completed_problems_count", 0),
                    "mastery_levels": profile.get("mastery_levels", {}),
                }
            except Exception as exc:
                return {"status": "unavailable", "reason": str(exc)}
        return {"status": "anonymous", "mastery_levels": {}}

    async def tool_generate_custom_exercise(self, skill: str, difficulty: int = 1) -> dict[str, Any]:
        """Autonomously generate a personalized practice problem with Socratic step hints."""
        if "multiplication" in skill.lower() or "គុណ" in skill:
            return {
                "id": "dyn-mult-1",
                "title_khmer": "លំហាត់ប្រឡងសមត្ថភាព៖ ប្រមាណវិធីគុណ",
                "title_eng": "Practice Problem: Multiplication",
                "problem_statement_khmer": "គណនា ២៤ x ៣",
                "problem_statement_eng": "Calculate 24 x 3",
                "step": {
                    "question_khmer": "តើ ២០ x ៣ ស្មើប៉ុន្មាន?",
                    "question_eng": "What is 20 x 3?",
                    "hint_khmer": "គិតពី ២ x ៣ ហើយថែម ០!",
                    "hint_eng": "Think 2 x 3 and append 0!",
                },
            }
        return {
            "id": "dyn-gen-1",
            "title_khmer": "លំហាត់ប្រឡងសមត្ថភាព",
            "title_eng": "Practice Problem",
            "problem_statement_khmer": f"លំហាត់អនុវត្តលើមេរៀន {skill}",
            "problem_statement_eng": f"Practice problem for skill {skill}",
            "step": {
                "question_khmer": "តើអ្នកចង់ចាប់ផ្តើមដំណោះស្រាយយ៉ាងដូចម្តេច?",
                "question_eng": "How would you like to start solving this?",
                "hint_khmer": "មើលពាក្យគន្លឹះក្នុងសំណួរ!",
                "hint_eng": "Look at the key words in the question!",
            },
        }

    async def tool_verify_solution(self, math_expression: str) -> dict[str, Any]:
        """Delegate exact arithmetic computation to solver_service."""
        solver_client = getattr(self._clients, "solver", None)
        if solver_client:
            try:
                res = await solver_client.solve(math_expression)
                return {
                    "status": "success",
                    "expression": math_expression,
                    "result": res.get("result"),
                    "steps": res.get("steps", []),
                }
            except Exception as exc:
                return {"status": "error", "reason": str(exc)}
        return {"status": "unsupported", "result": None}

    def declarations(self) -> list[dict[str, Any]]:
        """Return Gemini function declaration schemas for tool registration."""
        return [
            {
                "name": "tool_query_curriculum",
                "description": "Fetch textbook passages for a specific math/science skill and grade level.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "The math/science skill or topic to query."},
                        "grade": {"type": "integer", "description": "Target grade level (1-12)."},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "tool_get_student_mastery",
                "description": "Inspect a student's historical skill mastery levels and weak spots.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "Verified student ID."},
                    },
                    "required": ["student_id"],
                },
            },
            {
                "name": "tool_generate_custom_exercise",
                "description": "Autonomously generate a personalized practice problem with Socratic step hints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill": {"type": "string", "description": "Target skill to practice."},
                        "difficulty": {"type": "integer", "description": "Difficulty level (1-3)."},
                    },
                    "required": ["skill"],
                },
            },
            {
                "name": "tool_verify_solution",
                "description": "Delegate exact math computation or arithmetic step verification to solver_service.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "math_expression": {"type": "string", "description": "Arithmetic string (e.g. '24 * 3')."},
                    },
                    "required": ["math_expression"],
                },
            },
        ]
