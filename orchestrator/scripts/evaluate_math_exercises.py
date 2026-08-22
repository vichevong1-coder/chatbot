"""Interactive evaluation of real-world Cambodian MoEYS math exercises."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.graph.builder import build_graph
from app.infrastructure.service_clients import ServiceClients
from tests.conftest import (
    FakeAuthClient,
    FakeContentClient,
    FakeGradingClient,
    FakePedagogyClient,
    FakeProfileClient,
    FakeSafetyClient,
    FakeSolverClient,
)


async def run_evaluation():
    clients = ServiceClients(
        safety=FakeSafetyClient(),
        solver=FakeSolverClient(),
        content=FakeContentClient(),
        pedagogy=FakePedagogyClient(),
        auth=FakeAuthClient(),
        grading=FakeGradingClient(),
        profile=FakeProfileClient(),
    )
    graph = build_graph(clients)

    test_cases = [
        {
            "name": "Case 1: Grade 4 Multi-step Money Problem (Khmer)",
            "prompt": "សុខាមានប្រាក់ ២០ ០០០ រៀល។ គាត់ទិញសៀវភៅ ៣ ក្បាល ដោយមួយក្បាលតម្លៃ ៤ ០០០ រៀល និងប៊ិចមួយដើមតម្លៃ ២ ០០០ រៀល។ តើសុខានៅសល់ប្រាក់ប៉ុន្មាន?",
            "language": "km",
            "mode": "student",
        },
        {
            "name": "Case 2: Grade 4 Multi-step Money Problem (English)",
            "prompt": "Sokha has 20,000 Riels. She buys 3 notebooks at 4,000 Riels each and one pen for 2,000 Riels. How much money does Sokha have left?",
            "language": "en",
            "mode": "student",
        },
        {
            "name": "Case 3: Grade 5 Fraction Addition (Khmer)",
            "prompt": "បូរ៉ាផឹកទឹកដោះគោ ១/២ កែវនៅពេលព្រឹក និង ១/៤ កែវនៅពេលល្ងាច។ តើបូរ៉ាផឹកទឹកដោះគោសរុបប៉ុន្មានកែវ?",
            "language": "km",
            "mode": "student",
        },
        {
            "name": "Case 4: Grade 3 Rectangle Perimeter (Khmer)",
            "prompt": "សួនផ្កាមួយមានរាងចតុកោណកែង ដែលមានបណ្តោយ ៨ ម៉ែត្រ និងទទឹង ៥ ម៉ែត្រ។ ចូរបរិមាត្រនៃសួនផ្កានេះ។",
            "language": "km",
            "mode": "student",
        },
        {
            "name": "Case 5: Student Partial Attempt / Misconception (Khmer)",
            "prompt": "ខ្ញុំគិតថា ២០ ០០០ - ៤ ០០០ = ១៦ ០០០ គឺចប់ហើយមែនទេ?",
            "language": "km",
            "mode": "student",
        },
        {
            "name": "Case 6: Parent Asking for Teaching Method (English)",
            "prompt": "How can I explain adding fractions with different denominators to my 4th grader?",
            "language": "en",
            "mode": "parent",
        },
    ]

    print("================================================================================")
    print("EVALUATING REAL MATH EXERCISES AGAINST TUNSAY ORCHESTRATOR")
    print("================================================================================\n")

    for tc in test_cases:
        state = {
            "student_id": "eval-student",
            "session_id": "eval-session",
            "language": tc["language"],
            "mode": tc["mode"],
            "prompt": tc["prompt"],
            "transcript": [],
        }
        res = await graph.ainvoke(state)
        print(f"--- {tc['name']} ---")
        print(f"Prompt: {tc['prompt']}")
        print(f"Detected Intent: {res.get('intent')}")
        print(f"Response (Khmer): {res.get('text_khmer')}")
        print(f"Response (English): {res.get('text_eng')}")
        print(f"Is Parent Help: {res.get('is_parent_help')}")
        print(f"Suggested Next: {res.get('suggested_next')}\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
