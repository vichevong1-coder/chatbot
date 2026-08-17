"""Client for grading_service ``POST /grade``."""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class GradingClient(BaseServiceClient):
    service_name = "grading_service"

    async def grade(
        self,
        correct_answer: str,
        student_answer: str,
        input_format: str = "number",
        options: list[str] | None = None,
        language: str = "km",
        question_text: str = ""
    ) -> dict[str, Any]:
        """Returns ``{is_correct, misconception_code}``."""
        payload = {
            "correct_answer": correct_answer,
            "student_answer": student_answer,
            "input_format": input_format,
            "options": options,
            "language": language,
            "question_text": question_text
        }
        response = await self._request("POST", "/grade", json=payload)
        response.raise_for_status()
        return response.json()
