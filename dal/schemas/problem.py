"""HomeworkProblem and its step decomposition.

This is the shape the product is built around: a problem is never a question/answer pair,
it is an ordered walk through StepItems, each carrying its own three-rung hint ladder and
an "explain differently" analogy. See .claude/claude.md section 2.

Mirrors frontend_tunsay/src/types.ts field-for-field.
"""

from __future__ import annotations

from typing import Annotated
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from pydantic import Field, field_validator, model_validator

from dal.schemas.base import BilingualText, TunsayModel
from dal.schemas.enums import AnalogyType, InputFormat, Subject
from dal.schemas.grades import validate_grade

NonBlank = Annotated[str, Field(min_length=1)]


class Hint3(TunsayModel):
    """The third and final hint rung: a *worked analogous example*.

    Never the answer to this problem — it teaches the method on a different instance so
    the child still completes the step themselves.
    """

    title_khmer: NonBlank
    title_eng: NonBlank
    example_khmer: NonBlank
    example_eng: NonBlank


class ExplainDifferently(TunsayModel):
    """The "I still don't get it" path: a plain restatement plus a concrete analogy."""

    simple_khmer: NonBlank
    simple_eng: NonBlank
    analogy_title: NonBlank
    """One field, not a bilingual pair: carries Khmer with a parenthesised English gloss,
    e.g. "ប្រអប់ផ្លែឈើ (Fruit Boxes)". See .claude/contracts.md section 2."""
    analogy_khmer: NonBlank
    analogy_eng: NonBlank
    analogy_type: AnalogyType


class StepItem(TunsayModel):
    """One step of a problem. ``step_number`` is 1-indexed."""

    id: NonBlank
    step_number: int = Field(ge=1)
    total_steps: int = Field(ge=1)
    question_khmer: NonBlank
    question_eng: NonBlank
    input_format: InputFormat
    options: list[str] | None = None
    correct_answer: NonBlank
    """Always a string, even for ``number`` steps: "40", never 40. Grading normalises
    before comparing (see grading_service), so the stored form stays as authored."""
    hint1: BilingualText
    hint2: BilingualText
    hint3: Hint3
    explain_differently: ExplainDifferently

    @field_validator("correct_answer", mode="before")
    @classmethod
    def _coerce_answer_to_str(cls, v: object) -> object:
        """YAML happily turns `correct_answer: 40` into an int. Keep it a string rather
        than failing ingest on a formatting slip in authored content."""
        return str(v) if isinstance(v, (int, float)) else v

    @model_validator(mode="after")
    def _check_options_match_format(self) -> Self:
        """``options`` is required for mcq steps and forbidden otherwise."""
        if self.input_format is InputFormat.MCQ:
            if not self.options:
                raise ValueError(
                    f"step {self.id!r}: input_format is 'mcq' but options is empty"
                )
            if self.correct_answer not in self.options:
                raise ValueError(
                    f"step {self.id!r}: correct_answer {self.correct_answer!r} "
                    f"is not one of its own options {self.options!r}"
                )
        elif self.options:
            raise ValueError(
                f"step {self.id!r}: options is only valid when input_format is 'mcq' "
                f"(got {self.input_format.value!r})"
            )
        return self


class HomeworkProblem(TunsayModel):
    """A full problem, as authored and as stored.

    Never send this to a browser — it carries ``correct_answer`` on every step. Use
    :meth:`to_public` instead (.claude/contracts.md section 4).
    """

    id: NonBlank
    title_khmer: NonBlank
    title_eng: NonBlank
    grade: int
    subject: Subject
    problem_statement_khmer: NonBlank
    problem_statement_eng: NonBlank
    image_uri: str | None = None
    steps: list[StepItem] = Field(min_length=1)

    _validate_grade = field_validator("grade")(lambda cls, v: validate_grade(v))

    @model_validator(mode="after")
    def _check_step_consistency(self) -> Self:
        """Catches the authoring slip already present in the corpus: science-g4-water
        declares total_steps=3 on a 2-step problem (.claude/contracts.md section 6)."""
        n = len(self.steps)

        wrong_total = [s.id for s in self.steps if s.total_steps != n]
        if wrong_total:
            raise ValueError(
                f"problem {self.id!r} has {n} steps but these declare a different "
                f"total_steps: {wrong_total}"
            )

        expected = list(range(1, n + 1))
        actual = [s.step_number for s in self.steps]
        if actual != expected:
            raise ValueError(
                f"problem {self.id!r}: step_number must run {expected}, got {actual}"
            )

        ids = [s.id for s in self.steps]
        if len(set(ids)) != n:
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            raise ValueError(f"problem {self.id!r}: duplicate step ids {dupes}")

        return self

    def to_public(self) -> "PublicHomeworkProblem":
        """Strip every ``correct_answer`` before the problem leaves the backend.

        Today ChatView.tsx compares answers client-side, which means the answer key ships
        to the browser. P2.1 moves grading server-side; this is the serialiser that closes
        the hole.

        Goes through ``model_validate`` rather than ``model_construct`` on purpose: the
        nested hint rungs and analogy card have to be rebuilt as models, not left as bare
        dicts, or every downstream ``step.hint1.khmer`` breaks and serialisation emits
        garbage. Revalidating a few hundred bytes is not the bottleneck.
        """
        return PublicHomeworkProblem.model_validate(
            {
                **self.model_dump(exclude={"steps"}),
                "steps": [s.model_dump(exclude={"correct_answer"}) for s in self.steps],
            }
        )


class PublicStepItem(TunsayModel):
    """A step as the browser may see it: no ``correct_answer``."""

    id: str
    step_number: int
    total_steps: int
    question_khmer: str
    question_eng: str
    input_format: InputFormat
    options: list[str] | None = None
    hint1: BilingualText
    hint2: BilingualText
    hint3: Hint3
    explain_differently: ExplainDifferently


class PublicHomeworkProblem(TunsayModel):
    """A problem as the browser may see it. Serve this from GET /problems/{id}."""

    id: str
    title_khmer: str
    title_eng: str
    grade: int
    subject: Subject
    problem_statement_khmer: str
    problem_statement_eng: str
    image_uri: str | None = None
    steps: list[PublicStepItem]
