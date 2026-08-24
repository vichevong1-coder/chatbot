"""Unit tests for DiagnosticAgent."""

from __future__ import annotations

import pytest
from app.core.diagnostic_agent import DiagnosticAgent


def test_diagnostic_agent_identifies_place_value_struggle():
    agent = DiagnosticAgent()
    history = [
        {"misconception_code": "place_value_error"},
        {"misconception_code": "place_value_error"},
        {"misconception_code": "calculation_error"},
    ]
    diag = agent.diagnose_student_struggles(
        student_id="test-student-1",
        attempt_history=history,
        mastery_levels={"math-g4-apples": 0.4},
    )
    assert diag["student_id"] == "test-student-1"
    assert diag["primary_struggle"] == "place_value_error"
    assert len(diag["recovery_learning_path"]) == 3
    assert "Place Value" in diag["recovery_learning_path"][0]["focus_en"]
