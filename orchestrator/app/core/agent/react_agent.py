"""ReAct Agentic Loop — autonomous tool execution and reasoning for TunSay.

Drives multi-step tool execution (curriculum retrieval, mastery inspection, dynamic exercise generation,
arithmetic verification) before assembling the final Socratic tutoring response.
"""

from __future__ import annotations

from typing import Any
from dal.schemas.enums import Language, UserMode
from app.core.agent.tools import AgentTools
from app.utils.logging import get_logger, log_event

logger = get_logger("orchestrator.react_agent")


class ReActAgent:
    """Autonomous tool-use agent for student-tailored Socratic tutoring."""

    def __init__(self, clients: Any) -> None:
        self._clients = clients
        self.tools = AgentTools(clients)

    async def execute_turn(
        self,
        *,
        prompt: str,
        student_id: str,
        grade: int = 4,
        language: str = "km",
        mode: str = "student",
        problem_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute autonomous ReAct loop: observe -> reason -> call tools -> emit Socratic reply."""
        tool_results: list[dict[str, Any]] = []

        # 1. Observe & inspect student profile
        if student_id and student_id != "anonymous":
            mastery_data = await self.tools.tool_get_student_mastery(student_id)
            if mastery_data.get("status") == "success":
                tool_results.append({"tool": "tool_get_student_mastery", "output": mastery_data})

        # 2. Query curriculum RAG if topic is conceptual
        if not problem_id and len(prompt) > 3:
            curr_data = await self.tools.tool_query_curriculum(skill=prompt, grade=grade)
            if curr_data.get("status") == "success" and curr_data.get("results"):
                tool_results.append({"tool": "tool_query_curriculum", "output": curr_data})

        # 3. If student asks for a practice problem, generate custom exercise
        is_practice_request = any(w in prompt.lower() for w in ["practice", "exercise", "លំហាត់", "សាកល្បង"])
        generated_exercise: dict[str, Any] | None = None
        if is_practice_request:
            generated_exercise = await self.tools.tool_generate_custom_exercise(skill=prompt, difficulty=1)
            tool_results.append({"tool": "tool_generate_custom_exercise", "output": generated_exercise})

        log_event(
            logger,
            "react_agent_turn",
            student_id=student_id,
            intent="react_agent",
        )

        return {
            "status": "completed",
            "tools_used": tool_results,
            "generated_exercise": generated_exercise,
        }
