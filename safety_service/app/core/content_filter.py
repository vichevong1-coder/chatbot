"""Layered bilingual (Khmer/English) content filter — pure logic, no FastAPI.

Design (plan P1.6):

1. Normalize: NFC, casefold, strip zero-width characters, collapse whitespace,
   and collapse letter-spacing evasion ("k i l l" -> "kill").
2. Category rules: each rule combines English word-boundary regexes and Khmer
   substring keywords with *guards* — safe-context patterns that are removed
   from the text before the rule is evaluated, so "shooting percentage" never
   trips the violence rule and math vocabulary ("subtract negative numbers",
   "minus", "divide") never trips anything.
3. Only genuinely unsafe content is flagged. Greetings, feelings about school,
   and off-topic-but-harmless chatter are SAFE — routing them is the
   orchestrator's job, not a safety block.

Never echo or log the text being checked — this is children's data.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Reason codes (stable machine codes — the orchestrator switches on these)
# --------------------------------------------------------------------------

SELF_HARM = "self_harm"
VIOLENCE = "violence"
SEXUAL = "sexual"
DRUGS = "drugs"
HATE = "hate"
PII_REQUEST = "pii_request"
CHEATING = "cheating"
AGE_INAPPROPRIATE = "age_inappropriate"

# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

# Zero-width / invisible characters (note: U+200B is also the Khmer word
# separator — removing it is fine because Khmer keywords are matched as
# substrings on a whitespace-free form).
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))

# A run of 3+ single letters separated by spaces/dots/dashes ("k i l l").
_SPACED_LETTERS = re.compile(r"\b(?:[a-z][\s.\-_*]){2,}[a-z]\b")


def normalize(text: str) -> tuple[str, str]:
    """Return (norm, squashed).

    norm     — casefolded, zero-width stripped, whitespace collapsed, and
               letter-spacing evasion collapsed. English rules match this.
    squashed — norm with ALL whitespace removed. Khmer keywords match this,
               since Khmer script does not use spaces between words.
    """
    t = unicodedata.normalize("NFC", text)
    t = t.translate(_ZERO_WIDTH)
    t = t.casefold()
    t = re.sub(r"\s+", " ", t).strip()
    t = _SPACED_LETTERS.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), t)
    squashed = re.sub(r"\s+", "", t)
    return t, squashed


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rule:
    """One safety category: English regexes + Khmer keywords + guards.

    Guards are safe-context patterns; every guard match is deleted from the
    text before the rule's own patterns run, so an innocent phrase cannot
    trigger the rule, while genuinely unsafe text elsewhere still can.
    """

    category: str
    patterns: tuple[str, ...] = ()  # English, matched on `norm` (regex)
    khmer: tuple[str, ...] = ()  # Khmer, substring-matched on `squashed`
    guards: tuple[str, ...] = ()  # regex, removed from both forms first
    _compiled: list = field(default_factory=list, compare=False)

    def __post_init__(self) -> None:
        self._compiled.append(
            [re.compile(p) for p in self.patterns]
        )
        self._compiled.append([re.compile(g) for g in self.guards])

    def matches(self, norm: str, squashed: str) -> bool:
        compiled_patterns, compiled_guards = self._compiled
        for g in compiled_guards:
            norm = g.sub(" ", norm)
            squashed = g.sub("", squashed)
        if any(p.search(norm) for p in compiled_patterns):
            return True
        return any(kw in squashed for kw in self.khmer)


# Order matters: self-harm is checked before violence so "kill myself"
# gets the gentle self-harm refusal, not the violence one.
BASE_RULES: tuple[Rule, ...] = (
    Rule(
        category=SELF_HARM,
        patterns=(
            r"\bkill (?:myself|himself|herself|themselves)\b",
            r"\b(?:hurt|cut|cutting) myself\b",
            r"\bsuicide\b",
            r"\bself[- ]?harm\b",
            r"\bwant to die\b",
            r"\bend my life\b",
        ),
        khmer=(
            "សម្លាប់ខ្លួន",  # kill oneself
            "ធ្វើបាបខ្លួនឯង",  # hurt oneself
            "ចង់ស្លាប់",  # want to die
            "អត្តឃាត",  # suicide
        ),
    ),
    Rule(
        category=VIOLENCE,
        patterns=(
            r"\bkill(?:s|ed|ing)?\b",
            r"\bmurder\w*\b",
            r"\bstab(?:s|bed|bing)?\b",
            r"\bguns?\b",
            r"\bbombs?\b",
            r"\bgrenades?\b",
            r"\bweapons?\b",
            r"\bshoot(?:s|ing)?\b",
            r"\bshot\b",
            r"\bfight(?:s|ing)?\b",
            r"\bbeat (?:him|her|them|someone|\w+ )?up\b",
            r"\bhurt (?:him|her|them|someone)\b",
        ),
        khmer=(
            "សម្លាប់",  # kill
            "កាំភ្លើង",  # gun
            "គ្រាប់បែក",  # bomb
            "អាវុធ",  # weapon
            "វាយគ្នា",  # fight each other
            "បាញ់",  # shoot
        ),
        guards=(
            # sports & photography, not violence
            r"shooting percentage",
            r"shoot(?:s|ing)? (?:a |the )?(?:ball|basket|hoops?|goals?|free throws?)",
            r"photo ?shoot",
            r"troubleshoot\w*",
            r"បាញ់បាល់",  # shoot a ball (sports)
        ),
    ),
    Rule(
        category=SEXUAL,
        patterns=(
            r"\bsex\b",
            r"\bsexy\b",
            r"\bsexual\b",
            r"\bporn\w*\b",
            r"\bnaked\b",
            r"\bnudes?\b",
        ),
        khmer=(
            "រួមភេទ",  # sex
            "អាសអាភាស",  # obscene / pornographic
        ),
    ),
    Rule(
        category=DRUGS,
        patterns=(
            r"\bdrugs?\b",
            r"\bcocaine\b",
            r"\bheroin\b",
            r"\bmeth\b",
            r"\bmarijuana\b",
            r"\bsmoke (?:weed|cigarettes?)\b",
            r"\bget (?:drunk|high)\b",
            r"\bbeer\b",
            r"\bvodka\b",
            r"\bwhisk(?:e)?y\b",
            r"\bcigarettes?\b",
            r"\bvap(?:e|ing)\b",
        ),
        khmer=(
            "គ្រឿងញៀន",  # narcotics
            "កញ្ឆា",  # marijuana
            "ស្រាបៀរ",  # beer
            "ផឹកស្រា",  # drink alcohol
            "ជក់បារី",  # smoke cigarettes
            "ហេរ៉ូអ៊ីន",  # heroin
        ),
    ),
    Rule(
        category=HATE,
        patterns=(
            r"\b(?:i )?hate (?:all )?(?:khmer|thai|vietnamese|chinese|muslim|christian|black|white)s?(?: people)?\b",
            r"\ball \w+ (?:people )?(?:should|deserve to) die\b",
            r"\bnazis?\b",
        ),
        khmer=(
            "ស្អប់ជនជាតិ",  # hate <ethnicity>
            "ស្អប់ពួក",  # hate <group>
        ),
    ),
    Rule(
        category=PII_REQUEST,
        patterns=(
            r"\b(?:your|my) (?:home )?address\b",
            r"\bwhere do you live\b",
            r"\bphone number\b",
            r"\bmeet (?:me|up)\b",
            r"\blet'?s meet\b",
            r"\bsend (?:me )?(?:a )?(?:photo|picture|pic) of (?:you|yourself)\b",
            r"\bare you (?:home )?alone\b",
        ),
        khmer=(
            "អាសយដ្ឋាន",  # address
            "លេខទូរស័ព្ទ",  # phone number
            "ណាត់ជួប",  # arrange to meet up
            "រស់នៅឯណា",  # where do you live
            "នៅផ្ទះម្នាក់ឯង",  # home alone
        ),
    ),
    Rule(
        category=CHEATING,
        patterns=(
            r"\b(?:give|send|tell|show) me (?:all )?the answers\b",
            r"\ball the answers (?:to|for)\b",
            r"\banswers? (?:to|for) the (?:test|exam|quiz)\b",
            r"\bdo my (?:test|exam|homework|assignment) for me\b",
            r"\btake (?:my|the) (?:test|exam) for me\b",
            r"\bwrite my essay for me\b",
        ),
        khmer=(
            "ចម្លើយទាំងអស់",  # all the answers
            "ចម្លើយប្រឡង",  # exam answers
            "ចម្លើយតេស្ត",  # test answers
            "ប្រឡងជំនួស",  # take the exam instead (of me)
            "ធ្វើលំហាត់ជំនួស",  # do the homework instead (of me)
        ),
    ),
)

# --------------------------------------------------------------------------
# Refusals — authored content, therefore ALWAYS bilingual (contracts.md §3).
# Warm, non-judgmental, Tunsay's rabbit voice; never repeats the input.
# --------------------------------------------------------------------------

_GENERIC_REFUSAL = (
    "🛡️ ខ្ញុំនៅទីនេះដើម្បីជួយសិក្សា និងធ្វើលំហាត់ដោយសុវត្ថិភាព។ តោះត្រឡប់ទៅមើលលំហាត់វិញណា! 🐰",
    "I am here to help with safe and educational topics. Let's go back to your homework! 🐰",
)

REFUSALS: dict[str, tuple[str, str]] = {
    SELF_HARM: (
        "💛 ខ្ញុំយល់ថា ពេលខ្លះយើងមានអារម្មណ៍មិនស្រួលក្នុងចិត្ត។ សូមនិយាយជាមួយមនុស្សធំដែលអ្នកទុកចិត្ត "
        "ដូចជាឪពុកម្តាយ ឬលោកគ្រូអ្នកគ្រូណា។ ខ្ញុំនៅទីនេះជាមួយអ្នកជានិច្ច! 🐰",
        "💛 I care about you, friend. When we feel sad or upset inside, it really helps to talk "
        "to a trusted adult, like a parent or your teacher. I am always here to learn with you! 🐰",
    ),
    CHEATING: (
        "🛡️ ខ្ញុំមិនអាចធ្វើលំហាត់ ឬប្រឡងជំនួសអ្នកបានទេ ប៉ុន្តែខ្ញុំអាចជួយអ្នកឱ្យយល់ដោយខ្លួនឯង! "
        "តោះរៀនជាមួយគ្នាម្តងមួយជំហានណា! 🐰",
        "🛡️ I can't do the test or homework for you, but I can help you understand it yourself! "
        "Let's work through it together, one step at a time! 🐰",
    ),
    PII_REQUEST: (
        "🛡️ ដើម្បីសុវត្ថិភាព យើងមិនចែករំលែកព័ត៌មានផ្ទាល់ខ្លួនទេណា។ តោះត្រឡប់ទៅរៀនវិញ! 🐰",
        "🛡️ To stay safe, we keep personal information private. Let's get back to learning! 🐰",
    ),
}


def refusal_for(reason: str | None) -> tuple[str, str]:
    """Return (refusal_khmer, refusal_eng) for a reason code. Always bilingual."""
    if reason is None:
        return _GENERIC_REFUSAL
    return REFUSALS.get(reason, _GENERIC_REFUSAL)


# --------------------------------------------------------------------------
# Verdict + entry point
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    is_safe: bool
    reason: str | None = None


def check(text: str, rules: tuple[Rule, ...] = BASE_RULES) -> Verdict:
    """Check text against the given rules. First matching category wins."""
    norm, squashed = normalize(text)
    for rule in rules:
        if rule.matches(norm, squashed):
            return Verdict(is_safe=False, reason=rule.category)
    return Verdict(is_safe=True, reason=None)
