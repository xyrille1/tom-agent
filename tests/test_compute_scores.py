from tom_bench.schema import Trial
from tom_bench.scoring import compute_scores


def _trial(**kwargs) -> Trial:
    defaults = dict(
        id="t1",
        scenario_id="s1",
        pair_id="p1",
        condition="F",
        model_name="mock",
        task_type="interactive",
        prompt="p",
        raw_response="r",
        parsed_answer="kitchen",
        is_correct=True,
        failure_tag=None,
        latency_ms=1.0,
        error=None,
        created_at="2026-01-01T00:00:00Z",
    )
    defaults.update(kwargs)
    return Trial(**defaults)


def test_compute_scores_basic_accuracy():
    trials = [
        _trial(id="1", scenario_id="s1", condition="F", is_correct=True),
        _trial(id="2", scenario_id="s2", condition="F", is_correct=False),
        _trial(id="3", scenario_id="s3", condition="T", is_correct=True),
        _trial(id="4", scenario_id="s4", condition="T", is_correct=True),
    ]
    scores = compute_scores(trials)
    by_cond = {row.condition: row for row in scores.rows}
    assert by_cond["F"].accuracy == 0.5
    assert by_cond["F"].n == 2
    assert by_cond["T"].accuracy == 1.0
    assert by_cond["T"].n == 2


def test_compute_scores_tom_gap():
    trials = [
        _trial(id="1", scenario_id="s1", condition="F", is_correct=False),
        _trial(id="2", scenario_id="s2", condition="T", is_correct=True),
    ]
    scores = compute_scores(trials)
    assert len(scores.gaps) == 1
    gap = scores.gaps[0]
    assert gap.f_accuracy == 0.0
    assert gap.t_accuracy == 1.0
    assert gap.tom_gap == 1.0


def test_compute_scores_excludes_unscored_trials():
    trials = [
        _trial(id="1", scenario_id="s1", is_correct=True),
        _trial(id="2", scenario_id="s2", is_correct=None, error="network fail"),
    ]
    scores = compute_scores(trials)
    assert scores.rows[0].n == 1


def test_compute_scores_agreement_paired_by_scenario():
    trials = [
        _trial(id="1", scenario_id="shared", task_type="interactive", is_correct=True, model_name="m"),
        _trial(id="2", scenario_id="shared", task_type="quiz", is_correct=True, model_name="m"),
        _trial(id="3", scenario_id="other", task_type="interactive", is_correct=False, model_name="m"),
    ]
    scores = compute_scores(trials)
    agreement = scores.agreement[0]
    assert agreement["model_name"] == "m"
    assert agreement["n_paired"] == 1
