"""
Multi-turn evaluation test suite for Grade 9 scenarios.
"""
import pytest
from multiturn_harness import load_scenarios_for_grade, run_scenario_test

scenarios = load_scenarios_for_grade(9)

@pytest.mark.parametrize("scenario", scenarios, ids=lambda s: s["id"])
def test_grade9_multiturn(scenario, dry_run):
    run_scenario_test(scenario, dry_run)
