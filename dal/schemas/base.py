"""Base model shared by every Tunsay schema.

Field names are ``snake_case`` everywhere in Python and on the wire between services.
The frontend speaks ``camelCase``, so every model also carries a camelCase alias:

    problem.model_dump()                 -> {"title_khmer": ...}   service-to-service
    problem.model_dump(by_alias=True)    -> {"titleKhmer": ...}    gateway -> browser

Validation accepts either spelling (``populate_by_name``), so a payload coming back from
the frontend does not need translating before it is parsed. The gateway is the only place
that should be emitting ``by_alias=True`` — see .claude/claude.md section 5.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TunsayModel(BaseModel):
    """Common config for all Tunsay schemas."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


class BilingualText(TunsayModel):
    """An authored string that must exist in both languages.

    Used for the hint rungs, whose inner keys are ``khmer``/``eng`` in the source data.
    Per .claude/contracts.md section 3, *authored* content is always bilingual, so both
    sides are required and neither may be blank. Generated LLM turns use the single-language
    rule instead and are modelled on ChatMessage, not here.
    """

    khmer: str
    eng: str

    def for_language(self, language: str) -> str:
        """Return the requested language, falling back the way ChatView.tsx does."""
        if language == "km":
            return self.khmer or self.eng
        return self.eng or self.khmer
