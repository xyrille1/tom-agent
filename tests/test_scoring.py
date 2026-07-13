import pytest

from tom_bench.generator import generate_pair
from tom_bench.prompts import quiz_option_map
from tom_bench.scoring import (
    FAILURE_NEITHER,
    FAILURE_TRUE_STATE,
    FAILURE_UNPARSEABLE,
    score_interactive,
    score_quiz,
    wilson_ci,
)


@pytest.fixture
def f_scenario():
    f, _ = generate_pair(seed=11)
    return f


@pytest.fixture
def t_scenario():
    _, t = generate_pair(seed=11)
    return t


def test_score_interactive_correct(f_scenario):
    raw = f'{{"assist_location": "{f_scenario.ground_truth_belief_location}"}}'
    parsed, correct, tag = score_interactive(f_scenario, raw)
    assert parsed == f_scenario.ground_truth_belief_location
    assert correct is True
    assert tag is None


def test_score_interactive_true_state_failure(f_scenario):
    raw = f'{{"assist_location": "{f_scenario.final_location}"}}'
    parsed, correct, tag = score_interactive(f_scenario, raw)
    assert correct is False
    assert tag == FAILURE_TRUE_STATE


def test_score_interactive_neither_location(f_scenario):
    raw = f'{{"assist_location": "{f_scenario.decoy_room}"}}'
    parsed, correct, tag = score_interactive(f_scenario, raw)
    assert correct is False
    assert tag in (FAILURE_NEITHER, "wrong_belief_location")


def test_score_interactive_unparseable(f_scenario):
    parsed, correct, tag = score_interactive(f_scenario, "I think it's probably somewhere safe.")
    assert parsed is None
    assert correct is None
    assert tag == FAILURE_UNPARSEABLE


def test_score_interactive_handles_extra_text_around_json(f_scenario):
    raw = f'Sure! {{"assist_location": "{f_scenario.ground_truth_belief_location}"}} Hope that helps.'
    parsed, correct, tag = score_interactive(f_scenario, raw)
    assert correct is True


def test_score_quiz_correct(t_scenario):
    option_map = quiz_option_map(t_scenario)
    correct_letter = next(l for l, room in option_map.items() if room == t_scenario.ground_truth_belief_location)
    raw = f'{{"answer": "{correct_letter}"}}'
    parsed, correct, tag = score_quiz(t_scenario, raw)
    assert correct is True
    assert parsed == t_scenario.ground_truth_belief_location


def test_score_quiz_unparseable(t_scenario):
    parsed, correct, tag = score_quiz(t_scenario, "not valid json at all")
    assert parsed is None
    assert correct is None
    assert tag == FAILURE_UNPARSEABLE


def test_wilson_ci_bounds():
    lo, hi = wilson_ci(5, 10)
    assert 0.0 <= lo <= 0.5 <= hi <= 1.0


def test_wilson_ci_zero_n():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_wilson_ci_perfect_score_lower_bound_below_one():
    # Wilson's upper bound at phat=1 resolves to exactly 1.0; the informative
    # bound in this case is the lower bound, which stays honestly < 1.0.
    lo, hi = wilson_ci(10, 10)
    assert hi == pytest.approx(1.0)
    assert 0.5 < lo < 1.0
