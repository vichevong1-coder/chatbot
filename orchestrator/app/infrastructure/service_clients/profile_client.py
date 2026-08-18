"""Client for student_profile_service."""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class ProfileClient(BaseServiceClient):
    service_name = "student_profile_service"

    async def get_profile(self, student_id: str) -> dict[str, Any]:
        """Fetch student profile stars, completed problems, and mastery."""
        response = await self._request(
            "GET",
            f"/profile/{student_id}",
        )
        response.raise_for_status()
        return response.json()

    async def record_attempt(
        self,
        *,
        student_id: str,
        problem_id: str,
        step_id: str,
        is_correct: bool,
    ) -> dict[str, Any]:
        """Log a student attempt on a problem step, awarding stars/mastery."""
        response = await self._request(
            "POST",
            "/profile/attempts",
            json={
                "student_id": student_id,
                "problem_id": problem_id,
                "step_id": step_id,
                "is_correct": is_correct,
            },
        )
        response.raise_for_status()
        return response.json()
