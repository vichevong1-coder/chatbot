"""POST /chat behaviour — every service faked, sessions in memory (plan.md P1.7)."""

from __future__ import annotations

import json

from conftest import (
    PEDAGOGY_ENG,
    PEDAGOGY_KHMER,
    REFUSAL_ENG,
    REFUSAL_KHMER,
    post_chat,
    post_answer,
)


# ---------------------------------------------------------------------------
# Health + wire format
# ---------------------------------------------------------------------------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "orchestrator"}


def test_response_is_snake_case_on_the_wire(client):
    """FastAPI's by_alias default would leak camelCase — regression guard."""
    response = post_chat(client, "why do I multiply?")
    assert response.status_code == 200
    assert "text_khmer" in response.text
    assert "textKhmer" not in response.text
    assert "is_safety_refusal" in response.text
    assert "isSafetyRefusal" not in response.text


# ---------------------------------------------------------------------------
# Greeting — canned, zero service calls, zero tokens
# ---------------------------------------------------------------------------


def test_greeting_khmer_is_canned_with_zero_client_calls(client, fakes):
    response = post_chat(client, "សួស្តី")
    body = response.json()
    assert "ទន្សាយ" in body["text_khmer"]  # Tunsay introduces itself, in Khmer
    assert body["text_eng"] == ""
    assert body["is_safety_refusal"] is False
    # Zero calls anywhere — not even the safety service.
    assert fakes.safety.calls == []
    assert fakes.solver.calls == []
    assert fakes.content.calls == []
    assert fakes.pedagogy.calls == []


def test_greeting_english(client, fakes):
    body = post_chat(client, "hello!", language="en").json()
    assert "Tunsay" in body["text_eng"]
    assert body["text_khmer"] == ""
    assert fakes.pedagogy.calls == []


# ---------------------------------------------------------------------------
# Solve path — bare arithmetic, Tunsay-voiced, no LLM
# ---------------------------------------------------------------------------


def test_bare_arithmetic_goes_to_solver(client, fakes):
    body = post_chat(client, "5*8", language="en", mode="student").json()
    assert body["text_eng"] != ""
    assert fakes.solver.calls == ["5*8"]
    assert len(fakes.pedagogy.calls) == 1  # Socratic LLM explanation requested


def test_bare_arithmetic_parent_mode_reveals_solution(client, fakes):
    body = post_chat(client, "5*8", language="en", mode="parent").json()
    assert "40" in body["text_eng"]
    assert "The answer is 40! 🐰" in body["text_eng"]


def test_khmer_numerals_are_normalized_for_the_solver(client, fakes):
    body = post_chat(client, "៥*៨", language="km", mode="student").json()
    assert body["text_khmer"] != ""
    assert body["text_eng"] == ""
    assert fakes.solver.calls == ["5*8"]  # ០-៩ → ASCII before the solver sees it


def test_solver_steps_are_included_one_per_line(client, fakes):
    body = post_chat(client, "5*8", language="en", mode="parent").json()
    lines = body["text_eng"].split("\n")
    assert "The answer is 40! 🐰" in lines[-1]


# ---------------------------------------------------------------------------
# Explain path
# ---------------------------------------------------------------------------


def test_word_question_routes_to_pedagogy(client, fakes):
    body = post_chat(client, "why do I multiply?").json()
    assert body["text_khmer"] == PEDAGOGY_KHMER
    assert fakes.solver.calls == []
    assert len(fakes.pedagogy.calls) == 1
    assert fakes.pedagogy.calls[0]["prompt"] == "why do I multiply?"
    assert fakes.pedagogy.calls[0]["grade"] == 4  # default with no problem


def test_problem_context_is_fetched_and_passed_without_correct_answer(client, fakes):
    post_chat(
        client,
        "ហេតុអ្វីត្រូវចែក?",
        problem_id="math-g4-apples",
        active_step_index=0,
    )
    assert fakes.content.calls == ["math-g4-apples"]
    call = fakes.pedagogy.calls[0]
    assert "ចែកផ្លែប៉ោម" in call["context"]  # title reached pedagogy
    assert "ផ្លែប៉ោម ២៤" in call["context"]  # statement too
    assert "ប្រមាណវិធី" in call["context"]  # current step question
    # Phase 1: the answer must never reach pedagogy in any form.
    assert "correct_answer" not in json.dumps(fakes.pedagogy.calls)
    assert call["grade"] == 4  # grade came from the problem


def test_unknown_problem_id_still_explains_without_context(client, fakes):
    body = post_chat(client, "help me", problem_id="no-such-problem").json()
    assert body["text_khmer"] == PEDAGOGY_KHMER
    assert fakes.pedagogy.calls[0]["context"] is None


def test_content_service_down_explains_without_context(client, fakes):
    fakes.content.down = True
    body = post_chat(client, "help me", problem_id="math-g4-apples").json()
    assert body["text_khmer"] == PEDAGOGY_KHMER
    assert fakes.pedagogy.calls[0]["context"] is None


def test_parent_mode_sets_is_parent_help(client):
    body = post_chat(client, "how do I explain fractions?", mode="parent").json()
    assert body["is_parent_help"] is True


def test_student_mode_does_not_set_is_parent_help(client):
    body = post_chat(client, "why do I multiply?").json()
    assert body["is_parent_help"] is False


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


def test_unsafe_prompt_is_refused_and_pedagogy_never_called(client, fakes):
    fakes.safety.unsafe = True
    body = post_chat(client, "how do I fight my classmate?").json()
    assert body["is_safety_refusal"] is True
    assert body["text_khmer"] == REFUSAL_KHMER
    assert body["text_eng"] == ""  # single-language rule
    assert fakes.pedagogy.calls == []
    assert fakes.solver.calls == []


def test_unsafe_prompt_english_gets_english_refusal(client, fakes):
    fakes.safety.unsafe = True
    body = post_chat(client, "how do I fight?", language="en").json()
    assert body["is_safety_refusal"] is True
    assert body["text_eng"] == REFUSAL_ENG
    assert body["text_khmer"] == ""


def test_safety_service_down_fails_closed_without_500(client, fakes):
    fakes.safety.down = True
    response = post_chat(client, "why do I multiply?")
    assert response.status_code == 200  # soft failure, never a 500 at the child
    body = response.json()
    assert body["is_safety_refusal"] is True
    assert body["text_khmer"] != ""  # generic Khmer refusal
    assert body["text_eng"] == ""
    assert fakes.pedagogy.calls == []  # unchecked text never reached the LLM
    assert fakes.solver.calls == []


# ---------------------------------------------------------------------------
# Downstream failures stay child-safe
# ---------------------------------------------------------------------------


def test_pedagogy_down_returns_generic_fallback_not_500(client, fakes):
    fakes.pedagogy.down = True
    response = post_chat(client, "why do I multiply?")
    assert response.status_code == 200
    body = response.json()
    assert "🐰" in body["text_khmer"]  # Tunsay-voiced fallback
    assert body["text_eng"] == ""
    assert body["is_safety_refusal"] is False


def test_unparseable_arithmetic_falls_through_to_explain(client, fakes):
    """Looks like arithmetic, solver says 422 → explain path, not an error."""
    body = post_chat(client, "5**8((").json()
    assert fakes.solver.calls == ["5**8(("]
    assert len(fakes.pedagogy.calls) == 1
    assert body["text_khmer"] == PEDAGOGY_KHMER


def test_what_is_love_never_reaches_the_solver(client, fakes):
    """'what is love' style input is routed to explain by the heuristics."""
    body = post_chat(client, "what is love?", language="en").json()
    assert fakes.solver.calls == []
    assert body["text_eng"] == PEDAGOGY_ENG


def test_solver_down_falls_through_to_explain(client, fakes):
    fakes.solver.down = True
    body = post_chat(client, "5*8").json()
    assert len(fakes.pedagogy.calls) == 1
    assert body["text_khmer"] == PEDAGOGY_KHMER


# ---------------------------------------------------------------------------
# Single-language rule (contracts.md §3)
# ---------------------------------------------------------------------------


def test_khmer_request_fills_khmer_only(client):
    body = post_chat(client, "why do I multiply?", language="km").json()
    assert body["text_khmer"] != ""
    assert body["text_eng"] == ""


def test_english_request_fills_english_only(client):
    body = post_chat(client, "why do I multiply?", language="en").json()
    assert body["text_eng"] != ""
    assert body["text_khmer"] == ""


# ---------------------------------------------------------------------------
# Session transcript
# ---------------------------------------------------------------------------


def test_transcript_grows_by_two_per_turn_and_survives(client, store):
    post_chat(client, "why do I multiply?", session_id="sess-42")
    assert len(store.sessions["sess-42"]) == 2

    post_chat(client, "5*8", session_id="sess-42")
    transcript = store.sessions["sess-42"]
    assert len(transcript) == 4

    senders = [message["sender"] for message in transcript]
    assert senders == ["user", "sayo", "user", "sayo"]
    assert transcript[3]["text_khmer"] != ""
    # Other sessions are untouched.
    assert "sess-1" not in store.sessions


def test_session_id_round_trips_in_the_response(client):
    body = post_chat(client, "hello", session_id="sess-echo").json()
    assert body["session_id"] == "sess-echo"


def test_record_attempt_called_on_answer_check(client, fakes):
    response = post_answer(
        client,
        student_answer="5",
        student_id="stu-grad",
        problem_id="math-g4-apples",
        step_id="apples-step-1"
    )
    assert response.status_code == 200
    # Grading check happened (correct answer in APPLES_PROBLEM step 1 is "+" not "5")
    assert len(fakes.profile.calls) == 1
    call = fakes.profile.calls[0]
    assert call["student_id"] == "stu-grad"
    assert call["problem_id"] == "math-g4-apples"
    assert call["step_id"] == "apples-step-1"
    assert call["is_correct"] is False  # "5" is incorrect for "+" MCQ


def test_transcript_summarization_on_long_session(client, fakes, store):
    session_id = "long-session-42"
    # Pre-populate session with 8 turns (16 messages)
    store.sessions[session_id] = [
        {"sender": "user", "text_khmer": "hi", "text_eng": "", "id": "1", "timestamp": "now"},
        {"sender": "sayo", "text_khmer": "hello", "text_eng": "", "id": "2", "timestamp": "now"},
    ] * 8

    # Query chat — explain node should trigger and use the summarizer
    post_chat(client, "why do I multiply?", session_id=session_id)

    # Verify that the pedagogy client received a context string containing
    # the transcript summary
    assert len(fakes.pedagogy.calls) == 1
    pedagogy_context = fakes.pedagogy.calls[0]["context"]
    assert "ការសន្ទនាមុន" in pedagogy_context or "Earlier conversation" in pedagogy_context


# ---------------------------------------------------------------------------
# Clarify path
# ---------------------------------------------------------------------------


def test_clarify_question_student_khmer(client, fakes):
    body = post_chat(client, "?", language="km").json()
    assert "ទន្សាយ" in body["text_khmer"]
    assert body["text_eng"] == ""
    assert body["is_parent_help"] is False
    assert fakes.pedagogy.calls == []
    assert fakes.solver.calls == []


def test_clarify_question_student_english(client, fakes):
    body = post_chat(client, "what", language="en").json()
    assert "help" in body["text_eng"].lower()
    assert body["text_khmer"] == ""
    assert body["is_parent_help"] is False
    assert fakes.pedagogy.calls == []


def test_clarify_question_parent_mode(client, fakes):
    body = post_chat(client, "math", language="km", mode="parent").json()
    assert body["is_parent_help"] is True
    assert "បង្រៀនកូន" in body["text_khmer"]


# ---------------------------------------------------------------------------
# Explanation Cache
# ---------------------------------------------------------------------------


def test_explanation_cache_memoizes_identical_queries(client, fakes):
    # First query with a problem_id
    post_chat(client, "explain this problem", problem_id="math-g4-apples", active_step_index=0)
    assert len(fakes.pedagogy.calls) == 1

    # Second identical query
    post_chat(client, "explain this problem again", problem_id="math-g4-apples", active_step_index=0)
    # Pedagogy should NOT be called again because result is cached
    assert len(fakes.pedagogy.calls) == 1


