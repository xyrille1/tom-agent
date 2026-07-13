from tom_bench.generator import generate_pair, narrative_text
from tom_bench.novelty import load_reference_corpus, novelty_check


def test_reproducibility_same_seed_same_output():
    f1, t1 = generate_pair(seed=42)
    f2, t2 = generate_pair(seed=42)
    assert f1.model_dump() == f2.model_dump()
    assert t1.model_dump() == t2.model_dump()


def test_different_seeds_differ():
    f1, _ = generate_pair(seed=1)
    f2, _ = generate_pair(seed=2)
    assert f1.model_dump() != f2.model_dump()


def test_pair_matches_on_world_complexity():
    f, t = generate_pair(seed=7)
    assert len(f.rooms) == len(t.rooms)
    assert {r.name for r in f.rooms} == {r.name for r in t.rooms}
    assert len(f.event_log) == len(t.event_log)
    assert f.target_object == t.target_object
    assert f.seeker_name == t.seeker_name
    assert f.initial_location == t.initial_location
    assert f.final_location == t.final_location


def test_pair_differs_only_in_seeker_awareness():
    f, t = generate_pair(seed=99)
    # ground truth belief location is the one place they must differ
    assert f.ground_truth_belief_location == f.initial_location
    assert t.ground_truth_belief_location == t.final_location
    assert f.ground_truth_belief_location != t.ground_truth_belief_location

    # every other event up to (not including) the final event is identical
    for e_f, e_t in zip(f.event_log[:-1], t.event_log[:-1]):
        assert e_f.text == e_t.text
        assert e_f.type == e_t.type


def test_f_condition_correct_answer_is_not_true_state():
    f, _ = generate_pair(seed=123)
    assert f.ground_truth_belief_location != f.final_location


def test_seed_across_wide_range_always_produces_valid_pair():
    for seed in range(200):
        f, t = generate_pair(seed=seed)
        assert f.initial_location != f.final_location
        assert f.pair_id == t.pair_id
        assert len(f.rooms) in (3, 4)


def test_novelty_check_flags_inserted_classic_vignette():
    corpus = load_reference_corpus()
    classic = (
        "Sally puts her marble in a basket. Sally leaves the room. While Sally is away, "
        "Anne moves the marble from the basket to a box. Sally comes back into the room. "
        "Where will Sally look for her marble first?"
    )
    is_novel, score, _ = novelty_check(classic, corpus)
    assert not is_novel
    assert score > 0.5


def test_novelty_check_passes_generated_scenarios():
    corpus = load_reference_corpus()
    for seed in range(30):
        f, t = generate_pair(seed=seed)
        for scenario in (f, t):
            is_novel, score, _ = novelty_check(narrative_text(scenario), corpus)
            assert is_novel, f"seed={seed} condition={scenario.condition} scored {score}"
