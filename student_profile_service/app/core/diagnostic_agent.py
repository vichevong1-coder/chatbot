"""Autonomous Student Diagnostic & Recovery Agent.

Analyzes a student's attempt logs, hint usage, and misconception codes to generate
a personalized 3-day recovery learning path for targeted skill mastery.
"""

from __future__ import annotations

from typing import Any


class DiagnosticAgent:
    """Autonomous agent that diagnoses student struggle patterns."""

    def diagnose_student_struggles(
        self,
        *,
        student_id: str,
        attempt_history: list[dict[str, Any]],
        mastery_levels: dict[str, float],
    ) -> dict[str, Any]:
        """Examine misconception frequency and return targeted recovery recommendations."""
        misconception_counts: dict[str, int] = {}
        for att in attempt_history:
            code = att.get("misconception_code")
            if code:
                misconception_counts[code] = misconception_counts.get(code, 0) + 1

        primary_struggle = None
        if misconception_counts:
            primary_struggle = max(misconception_counts, key=misconception_counts.get)

        # Build 3-day recovery learning path based on primary misconception
        recovery_plan = self._build_recovery_plan(primary_struggle)

        return {
            "student_id": student_id,
            "primary_struggle": primary_struggle,
            "misconception_summary": misconception_counts,
            "recovery_learning_path": recovery_plan,
        }

    def _build_recovery_plan(self, misconception_code: str | None) -> list[dict[str, str]]:
        if misconception_code == "place_value_error":
            return [
                {"day": "Day 1", "focus_km": "ការយល់ដឹងពីខ្ទង់រាយ ខ្ទង់ដប់ និងខ្ទង់រយ", "focus_en": "Understanding Place Value (Ones, Tens, Hundreds)"},
                {"day": "Day 2", "focus_km": "ការបំបែកចំនួនតាមខ្ទង់", "focus_en": "Decomposing Numbers by Place Value"},
                {"day": "Day 3", "focus_km": "ការបូកនិងគុណតាមតារាងខ្ទង់", "focus_en": "Addition and Multiplication using Place Value Charts"},
            ]
        elif misconception_code == "operation_confusion":
            return [
                {"day": "Day 1", "focus_km": "ការស្វែងរកពាក្យគន្លឹះក្នុងប្រមាណវិធី", "focus_en": "Identifying Operation Keywords in Word Problems"},
                {"day": "Day 2", "focus_km": "ការបែងចែករវាងការបូក និងការគុណ", "focus_en": "Distinguishing Addition vs Multiplication"},
                {"day": "Day 3", "focus_km": "ដោះស្រាយចំណោទពាក្យ", "focus_en": "Solving Guided Socratic Word Problems"},
            ]
        else:
            return [
                {"day": "Day 1", "focus_km": "ការរំលឹកមេរៀនគ្រឹះ", "focus_en": "Foundational Skill Review"},
                {"day": "Day 2", "focus_km": "ការអនុវត្តលំហាត់ថ្នាក់ទី៤-៥", "focus_en": "Guided Practice (Grades 4-5)"},
                {"day": "Day 3", "focus_km": "ការប្រឡងសមត្ថភាពយកផ្កាយ", "focus_en": "Mastery Assessment & Star Rewards"},
            ]
