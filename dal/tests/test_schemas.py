"""P1.1 verification.

The seed corpus is the fixture: these schemas were derived from working UI code, so the
real content is the only honest test of whether they match it.
"""

from __future__ import annotations

import glob
import os

import pytest
import yaml
from pydantic import ValidationError

from dal.models import Base, Problem, Step, User
from dal.schemas import (
    ChatMessage,
    ChatResponse,
    HomeworkProblem,
    InputFormat,
    LoginRequest,
    RegisterRequest,
    UserMode,
    UserProfile,
    set_supported_grades,
    supported_grades,
)

SEED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "content_service",
    "seed_data",
)

# science-g4-water has a known authoring defect: sci-step-1 declares total_steps=3 on a
# 2-step problem. Documented in .claude/contracts.md section 6. The schema is *supposed*
# to reject it, so it is quarantined here rather than silently tolerated.
KNOWN_BAD = {"science-g4-water"}


def _seed_files() -> list[str]:
    files = sorted(glob.glob(os.path.join(SEED_DIR, "*.yaml")))
    assert files, f"no seed files found in {SEED_DIR}"
    return files


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(autouse=True)
def _reset_grade_policy():
    """Grade policy is process-global; keep tests from leaking into each other."""
    set_supported_grades(None)
    yield
    set_supported_grades(None)


# --------------------------------------------------------------------------- round-trip


@pytest.mark.parametrize("path", _seed_files(), ids=lambda p: os.path.basename(p))
def test_seed_problem_round_trips(path: str) -> None:
    """Every seed problem parses and survives a dump/reload with no field loss."""
    raw = _load(path)
    if raw["id"] in KNOWN_BAD:
        pytest.xfail(f"{raw['id']}: known authoring defect, see contracts.md section 6")

    problem = HomeworkProblem.model_validate(raw)
    again = HomeworkProblem.model_validate(problem.model_dump())
    assert again == problem

    # exclude_none because the schema materialises `options: None` on non-mcq steps,
    # where the YAML simply omits the key. That is a serialisation default, not data
    # loss — every value present in the source must still come back identical.
    assert again.model_dump(exclude_none=True) == raw, "round-trip changed the data"


def test_known_defect_is_actually_caught() -> None:
    """The xfail above must be a real rejection, not a parse that happens to pass."""
    raw = _load(os.path.join(SEED_DIR, "science-g4-water.yaml"))
    with pytest.raises(ValidationError, match="total_steps"):
        HomeworkProblem.model_validate(raw)


def test_khmer_survives_the_round_trip() -> None:
    """Khmer script and Khmer numerals must come back byte-identical."""
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml"))
    problem = HomeworkProblem.model_validate(raw)
    assert problem.problem_statement_khmer == raw["problem_statement_khmer"]
    assert "៥" in problem.problem_statement_khmer  # Khmer numeral 5, not ASCII "5"
    assert problem.model_dump()["problem_statement_khmer"] == raw["problem_statement_khmer"]


def test_camel_case_aliases_match_the_frontend() -> None:
    """by_alias must produce exactly the keys types.ts declares."""
    problem = HomeworkProblem.model_validate(_load(os.path.join(SEED_DIR, "math-g4-apples.yaml")))
    dumped = problem.model_dump(by_alias=True)

    assert {"titleKhmer", "titleEng", "problemStatementKhmer", "imageUri"} <= dumped.keys()
    assert "title_khmer" not in dumped

    step = dumped["steps"][0]
    assert {"stepNumber", "totalSteps", "inputFormat", "correctAnswer", "explainDifferently"} <= step.keys()
    assert {"titleKhmer", "exampleKhmer"} <= step["hint3"].keys()
    assert "analogyType" in step["explainDifferently"]

    # and the camelCase form must parse straight back in
    assert HomeworkProblem.model_validate(dumped) == problem


# ------------------------------------------------------------------------------- grades


def test_grade_outside_the_supported_set_is_rejected() -> None:
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"grade": 7}
    with pytest.raises(ValidationError, match="not currently supported"):
        HomeworkProblem.model_validate(raw)


def test_grade_outside_the_product_range_is_rejected() -> None:
    set_supported_grades({1, 2, 3, 4, 5, 6})
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"grade": 13}
    with pytest.raises(ValidationError, match="outside the product range"):
        HomeworkProblem.model_validate(raw)


def test_widening_the_grade_set_is_config_not_a_schema_edit() -> None:
    """The plan's requirement: supporting grade 9 must not need a code change."""
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"grade": 9}
    with pytest.raises(ValidationError):
        HomeworkProblem.model_validate(raw)

    set_supported_grades({4, 5, 6, 9})
    assert HomeworkProblem.model_validate(raw).grade == 9


def test_default_supported_set_covers_the_shipped_corpus() -> None:
    """Guards the decision in dal/schemas/grades.py: the corpus contains grade 3
    problems, so defaulting to the 4-6 focus band would reject shipped content."""
    assert {3, 4, 5} <= supported_grades()


def test_grade_set_is_read_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("TUNSAY_SUPPORTED_GRADES", "1-3,9")
    assert supported_grades() == frozenset({1, 2, 3, 9})


# -------------------------------------------------------------------------------- steps


def _first_step(problem_id: str = "math-g4-apples") -> dict:
    return _load(os.path.join(SEED_DIR, f"{problem_id}.yaml"))["steps"][0]


def test_mcq_step_without_options_is_rejected() -> None:
    raw = _load(os.path.join(SEED_DIR, "english-g4-grammar.yaml"))
    mcq = next(s for s in raw["steps"] if s["input_format"] == "mcq")
    mcq.pop("options")
    with pytest.raises(ValidationError, match="options is empty"):
        HomeworkProblem.model_validate(raw)


def test_non_mcq_step_with_options_is_rejected() -> None:
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml"))
    numeric = next(s for s in raw["steps"] if s["input_format"] != "mcq")
    numeric["options"] = ["1", "2"]
    with pytest.raises(ValidationError, match="only valid when input_format is 'mcq'"):
        HomeworkProblem.model_validate(raw)


def test_mcq_answer_must_be_one_of_its_own_options() -> None:
    raw = _load(os.path.join(SEED_DIR, "english-g4-grammar.yaml"))
    mcq = next(s for s in raw["steps"] if s["input_format"] == "mcq")
    mcq["correct_answer"] = "definitely-not-an-option"
    with pytest.raises(ValidationError, match="not one of its own options"):
        HomeworkProblem.model_validate(raw)


def test_numeric_answer_stays_a_string() -> None:
    """YAML turns `correct_answer: 40` into an int; it must not deserialize as one."""
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml"))
    raw["steps"][0]["correct_answer"] = 40
    problem = HomeworkProblem.model_validate(raw)
    assert problem.steps[0].correct_answer == "40"
    assert isinstance(problem.steps[0].correct_answer, str)


def test_out_of_order_step_numbers_are_rejected() -> None:
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml"))
    raw["steps"][0]["step_number"] = 3
    with pytest.raises(ValidationError, match="step_number must run"):
        HomeworkProblem.model_validate(raw)


def test_problem_with_no_steps_is_rejected() -> None:
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"steps": []}
    with pytest.raises(ValidationError):
        HomeworkProblem.model_validate(raw)


def test_blank_authored_field_is_rejected() -> None:
    """The bilingual rule: authored content must carry both languages, non-empty."""
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"title_khmer": ""}
    with pytest.raises(ValidationError):
        HomeworkProblem.model_validate(raw)


def test_unknown_field_is_rejected() -> None:
    """extra='forbid' catches a camelCase/snake_case slip instead of dropping data."""
    raw = _load(os.path.join(SEED_DIR, "math-g4-apples.yaml")) | {"titleKhmerr": "x"}
    with pytest.raises(ValidationError):
        HomeworkProblem.model_validate(raw)


# ------------------------------------------------------------------- answer-key leakage


def test_to_public_strips_every_correct_answer() -> None:
    """The hole this closes: today ChatView.tsx grades client-side, so the answer key
    ships to the browser (.claude/contracts.md section 4)."""
    problem = HomeworkProblem.model_validate(_load(os.path.join(SEED_DIR, "math-g4-apples.yaml")))
    public = problem.to_public()

    assert len(public.steps) == len(problem.steps)
    for step in public.steps:
        assert not hasattr(step, "correct_answer")

    blob = public.model_dump_json(by_alias=True)
    assert "correctAnswer" not in blob and "correct_answer" not in blob

    # Field-level is the only sound check here. Scanning for the answer *value* would be
    # wrong twice over: step 1's answer is "5" and the statement legitimately reads
    # "There are 5 boxes" (that is the step — read the number out of the question), and
    # mcq answers are necessarily visible inside `options`. Neither is a leak; both are
    # why grading has to happen server-side rather than by hiding the key.
    assert InputFormat.MCQ in {s.input_format for s in problem.steps}


def test_public_problem_keeps_the_teaching_content() -> None:
    """Stripping answers must not strip the hints — that would gut the product."""
    problem = HomeworkProblem.model_validate(_load(os.path.join(SEED_DIR, "math-g4-apples.yaml")))
    step = problem.to_public().steps[0]
    assert step.hint1.khmer and step.hint2.khmer
    assert step.hint3.example_khmer
    assert step.explain_differently.analogy_type


# ---------------------------------------------------------------------------- chat/user


def test_chat_response_may_be_single_language() -> None:
    """Generated content fills one side and leaves the other "" — not None, because
    ChatView.tsx falls back with `textKhmer || textEng`."""
    res = ChatResponse(text_khmer="សួស្តី", text_eng="", session_id="s1")
    assert res.text_eng == ""
    assert res.model_dump(by_alias=True)["textKhmer"] == "សួស្តី"


def test_chat_response_with_no_language_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatResponse(text_khmer="", text_eng="", session_id="s1")


def test_chat_message_render_flags_default_off() -> None:
    msg = ChatMessage(id="m1", sender="sayo", text_eng="hi", timestamp="12:00")
    assert msg.is_safety_refusal is False and msg.is_parent_help is False
    assert "isSafetyRefusal" in msg.model_dump(by_alias=True)


def test_user_profile_accepts_the_khmer_display_name() -> None:
    profile = UserProfile(name="សុជា (Sochea)", grade=4)
    assert profile.model_dump(by_alias=True)["completedProblemsCount"] == 0


def test_register_needs_school_code_or_grade() -> None:
    with pytest.raises(ValidationError, match="school_code"):
        RegisterRequest(student_name="សុជា (Sochea)")
    assert RegisterRequest(student_name="សុជា (Sochea)", school_code="TUNSAY-G4-DEMO")
    assert RegisterRequest(student_name="សុជា (Sochea)", grade=4)


def test_pin_must_be_four_digits() -> None:
    for bad in ("123", "12345", "abcd"):
        with pytest.raises(ValidationError):
            RegisterRequest(student_name="x", grade=4, pin=bad)
    assert RegisterRequest(student_name="x", grade=4, pin="1234").pin == "1234"


def test_login_needs_an_identifier() -> None:
    with pytest.raises(ValidationError, match="student_name or school_code"):
        LoginRequest(pin="1234")


# ------------------------------------------------------------------------------- models


def test_orm_models_map_cleanly() -> None:
    """Catches mapper errors (bad relationship, missing FK) without a live database."""
    from sqlalchemy.orm import configure_mappers

    configure_mappers()
    tables = set(Base.metadata.tables)
    assert {"users", "schools", "problems", "steps", "attempts", "sessions"} <= tables


def test_there_is_exactly_one_role() -> None:
    """Every account is a student: no role column, no account-type enum, no link table.

    Guards against someone reintroducing roles "for completeness" — the frontend has no
    account-type picker and never sends one.
    """
    import dal.schemas as schemas

    assert not hasattr(schemas, "Role")
    assert "role" not in User.__table__.columns
    assert "parent_student_link" not in Base.metadata.tables
    assert "role" not in RegisterRequest.model_fields


def test_user_mode_is_a_toggle_not_an_identity() -> None:
    """UserMode survives the role cull: parent mode is a per-session UI toggle on a
    student account, and P2.5 depends on it."""
    assert {m.value for m in UserMode} == {"student", "parent"}
    assert "mode" in UserProfile.model_fields
    assert UserProfile(name="សុជា (Sochea)", grade=4).mode is UserMode.STUDENT


def test_orm_schema_covers_the_pydantic_problem_fields() -> None:
    """Guards against the two drifting apart silently."""
    schema_fields = set(HomeworkProblem.model_fields) - {"steps"}
    assert schema_fields <= set(Problem.__table__.columns.keys())

    step_fields = set(HomeworkProblem.model_fields["steps"].annotation.__args__[0].model_fields)
    assert step_fields <= set(Step.__table__.columns.keys())


def test_student_name_is_not_globally_unique() -> None:
    """Two children at different schools may share a Khmer display name."""
    name_col = User.__table__.columns["student_name"]
    assert not name_col.unique
    constraints = {tuple(sorted(c.columns.keys())) for c in User.__table__.constraints if hasattr(c, "columns")}
    assert ("school_code", "student_name") in constraints
