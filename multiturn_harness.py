"""
Shared multi-turn test harness module for Tunsay.

Provides helper functions and execution logic for grade-separated test suites.
"""

import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
ORCHESTRATOR_DIR = ROOT_DIR / "orchestrator"
FIXTURES_PATH = ROOT_DIR / "tunsay_multiturn_fixtures.json"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

_IN_PROCESS_SESSION_STORE = None
_IN_PROCESS_GRAPH = None


def _get_explanation_generator():
    import importlib.util

    pedagogy_dir = ROOT_DIR / "pedagogy_service"

    spec_pm = importlib.util.spec_from_file_location(
        "pedagogy_pm", str(pedagogy_dir / "app" / "core" / "prompt_manager.py")
    )
    mod_pm = importlib.util.module_from_spec(spec_pm)
    sys.modules["pedagogy_pm"] = mod_pm
    sys.modules["app.core.prompt_manager"] = mod_pm
    spec_pm.loader.exec_module(mod_pm)

    spec_eg = importlib.util.spec_from_file_location(
        "pedagogy_eg", str(pedagogy_dir / "app" / "core" / "explanation_generator.py")
    )
    mod_eg = importlib.util.module_from_spec(spec_eg)
    sys.modules["pedagogy_eg"] = mod_eg
    sys.modules["app.core.explanation_generator"] = mod_eg
    spec_eg.loader.exec_module(mod_eg)

    return mod_eg.ExplanationGenerator()


def _get_in_process_graph_and_store():
    global _IN_PROCESS_SESSION_STORE, _IN_PROCESS_GRAPH
    if _IN_PROCESS_GRAPH is not None:
        return _IN_PROCESS_GRAPH, _IN_PROCESS_SESSION_STORE

    from orchestrator.app.core.graph.builder import build_graph
    from orchestrator.app.infrastructure.service_clients import ServiceClients
    from orchestrator.app.session_store.redis_store import InMemorySessionStore

    class InProcessPedagogyClient:
        def __init__(self):
            self._gen = _get_explanation_generator()

        async def explain(
            self,
            *,
            prompt: str,
            grade: int,
            language: str,
            mode: str,
            context: str | None = None,
            misconception_code: str | None = None,
        ):
            return await self._gen.explain(
                prompt=prompt,
                grade=grade,
                language=language,
                mode=mode,
                context=context,
                misconception_code=misconception_code,
            )

        async def translate(
            self, *, text: str, target_language: str, source_language: str | None = None
        ):
            return {
                "translated_text": text,
                "target_language": target_language,
                "from_fallback": False,
            }

    class DummyClient:
        async def check(self, text, language, direction="input"):
            return {
                "is_safe": True,
                "reason": None,
                "refusal_khmer": "",
                "refusal_eng": "",
            }

        async def solve(self, expression):
            return {"expression": expression, "answer": "", "steps": []}

        async def get_problem(self, problem_id):
            return None

        async def get_profile(self, student_id):
            return {"grade": 4}

    clients = ServiceClients(
        safety=DummyClient(),
        solver=DummyClient(),
        content=DummyClient(),
        pedagogy=InProcessPedagogyClient(),
        auth=DummyClient(),
        grading=DummyClient(),
        profile=DummyClient(),
        stt=DummyClient(),
        ocr=DummyClient(),
        retrieval=DummyClient(),
    )

    _IN_PROCESS_SESSION_STORE = InMemorySessionStore()
    _IN_PROCESS_GRAPH = build_graph(clients)
    return _IN_PROCESS_GRAPH, _IN_PROCESS_SESSION_STORE


async def _run_in_process_turn(session_id: str, message: str, grade: int = 4) -> str:
    graph, store = _get_in_process_graph_and_store()

    if await store.get_session_meta(session_id) is None:
        await store.init_session(
            session_id, student_id="multiturn_tester", grade=grade, language="en"
        )

    transcript = await store.get(session_id)

    state = {
        "student_id": "multiturn_tester",
        "session_id": session_id,
        "language": "en",
        "mode": "student",
        "grade": grade,
        "problem_id": None,
        "active_step_index": None,
        "prompt": message,
        "transcript": transcript,
    }

    result = await graph.ainvoke(state)
    text_khmer = result.get("text_khmer", "")
    text_eng = result.get("text_eng", "")

    from datetime import datetime, timezone

    from dal.schemas import ChatMessage

    now_iso = datetime.now(timezone.utc).isoformat()

    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        sender="user",
        text_khmer="",
        text_eng=message,
        timestamp=now_iso,
    ).model_dump(mode="json")

    bot_msg = ChatMessage(
        id=str(uuid.uuid4()),
        sender="sayo",
        text_khmer=text_khmer,
        text_eng=text_eng,
        timestamp=now_iso,
    ).model_dump(mode="json")

    await store.append(session_id, user_msg, bot_msg)

    return text_eng or text_khmer


def call_tunsay(session_id: str, message: str, grade: int = 4) -> str:
    """Send one student message to Tunsay and return the bot's reply text."""
    import requests

    for url in [
        "http://localhost:8000/chat",
        "http://127.0.0.1:8000/chat",
        "http://localhost:9001/chat",
    ]:
        try:
            resp = requests.post(
                url,
                json={
                    "session_id": session_id,
                    "student_id": "multiturn_tester",
                    "prompt": message,
                    "language": "en",
                    "mode": "student",
                    "grade": grade,
                },
                timeout=0.2,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("text_eng") or data.get("text_khmer") or ""
        except Exception:
            pass

    import asyncio

    return asyncio.run(_run_in_process_turn(session_id, message, grade=grade))


def llm_judge(expected: str, actual: str, question_context: str) -> dict:
    """Evaluates turn quality using Anthropic or heuristic fallback."""
    try:
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("no api key")

        client = anthropic.Anthropic()
        prompt = f"""You are grading a tutoring chatbot's single turn.

Original student question: {question_context}
Expected bot turn (reference, wording may differ): {expected}
Actual bot turn (to grade): {actual}

Answer strictly as JSON with keys:
- on_topic (bool): does the actual turn address the same teaching sub-step as the expected turn?
- leaks_answer (bool): does the actual turn give away the final answer instead of asking a guiding question?
- single_step (bool): does the actual turn ask about ONE sub-step only (not multiple stacked questions)?
- reasoning (short string)

Return ONLY the JSON object, nothing else."""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)

    except Exception:
        question_marks = actual.count("?")
        return {
            "on_topic": True,
            "leaks_answer": False,
            "single_step": question_marks <= 1,
            "reasoning": "heuristic fallback (no LLM judge available)",
        }


def load_scenarios():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scenarios_for_grade(grade: int):
    all_scenarios = load_scenarios()
    return [s for s in all_scenarios if s.get("grade") == grade]


def run_scenario_test(scenario: dict, dry_run: bool):
    session_id = str(uuid.uuid4())
    turns = scenario["turns"]
    question_context = turns[0]["text"]

    failures = []

    for i, turn in enumerate(turns):
        if turn["role"] != "student":
            continue

        expected_bot_turn = turns[i + 1]["text"] if i + 1 < len(turns) else None
        if expected_bot_turn is None:
            continue

        if dry_run:
            actual = expected_bot_turn
        else:
            actual = call_tunsay(
                session_id, turn["text"], grade=scenario.get("grade", 4)
            )

        verdict = llm_judge(expected_bot_turn, actual, question_context)

        if verdict.get("leaks_answer"):
            failures.append(
                f"[turn {i}] answer leaked early. actual={actual!r} reasoning={verdict.get('reasoning')}"
            )
        if not verdict.get("single_step", True):
            failures.append(
                f"[turn {i}] multiple sub-steps asked at once. actual={actual!r}"
            )
        if not verdict.get("on_topic", True):
            failures.append(
                f"[turn {i}] off-topic vs expected step. expected={expected_bot_turn!r} actual={actual!r} "
                f"reasoning={verdict.get('reasoning')}"
            )

    assert not failures, (
        f"Scenario {scenario['id']} (Grade {scenario['grade']}, {scenario['subject']}) failed:\n"
        + "\n".join(failures)
    )
