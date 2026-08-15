"""Direct unit tests for the pure key-case translation module."""

from __future__ import annotations

from app.core.case_translate import (
    camel_to_snake,
    snake_to_camel,
    to_camel_keys,
    to_snake_keys,
)

KHMER = "សុជា (Sochea) — ចែកផ្លែប៉ោម ១២ គ្រាប់"


class TestKeyFunctions:
    def test_camel_to_snake(self):
        assert camel_to_snake("textKhmer") == "text_khmer"
        assert camel_to_snake("activeStepIndex") == "active_step_index"
        assert camel_to_snake("isSafetyRefusal") == "is_safety_refusal"

    def test_snake_to_camel(self):
        assert snake_to_camel("text_khmer") == "textKhmer"
        assert snake_to_camel("active_step_index") == "activeStepIndex"
        assert snake_to_camel("hint1") == "hint1"

    def test_already_snake_keys_unchanged_by_camel_to_snake(self):
        assert camel_to_snake("text_khmer") == "text_khmer"
        assert camel_to_snake("prompt") == "prompt"

    def test_already_camel_keys_unchanged_by_snake_to_camel(self):
        assert snake_to_camel("textKhmer") == "textKhmer"
        assert snake_to_camel("prompt") == "prompt"


class TestRecursiveTranslation:
    def test_nested_dicts_and_lists(self):
        camel = {
            "problemId": "math-g4-apples",
            "steps": [
                {
                    "stepNumber": 1,
                    "explainDifferently": {"simpleKhmer": "ក", "analogyType": "apples"},
                    "options": ["1", "2"],
                }
            ],
        }
        snake = to_snake_keys(camel)
        assert snake == {
            "problem_id": "math-g4-apples",
            "steps": [
                {
                    "step_number": 1,
                    "explain_differently": {"simple_khmer": "ក", "analogy_type": "apples"},
                    "options": ["1", "2"],
                }
            ],
        }
        assert to_camel_keys(snake) == camel

    def test_top_level_list(self):
        assert to_camel_keys([{"text_eng": "hi"}]) == [{"textEng": "hi"}]

    def test_keys_already_snake_pass_through_inbound(self):
        assert to_snake_keys({"session_id": "s", "mode": "student"}) == {
            "session_id": "s",
            "mode": "student",
        }

    def test_values_never_transformed(self):
        obj = {"someKey": "someValueWithCaps_and_snakes", "n": 5, "f": 1.5, "b": True, "x": None}
        snake = to_snake_keys(obj)
        assert snake["some_key"] == "someValueWithCaps_and_snakes"
        assert (snake["n"], snake["f"], snake["b"], snake["x"]) == (5, 1.5, True, None)

    def test_khmer_values_byte_identical_both_directions(self):
        camel = {"textKhmer": KHMER, "nested": [{"titleKhmer": KHMER}]}
        snake = to_snake_keys(camel)
        assert snake["text_khmer"].encode("utf-8") == KHMER.encode("utf-8")
        back = to_camel_keys(snake)
        assert back["textKhmer"].encode("utf-8") == KHMER.encode("utf-8")
        assert back["nested"][0]["titleKhmer"].encode("utf-8") == KHMER.encode("utf-8")
