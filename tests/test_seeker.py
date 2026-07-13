from tom_bench.generator import generate_pair
from tom_bench.seeker import first_search_location, full_search_order


def test_first_search_location_is_belief_location():
    assert first_search_location("kitchen") == "kitchen"


def test_full_search_order_starts_with_belief_then_sweep():
    order = full_search_order("garage", ["kitchen", "garage", "attic"])
    assert order == ["garage", "kitchen", "attic"]


def test_full_search_order_dedupes_belief_room_in_sweep():
    order = full_search_order("kitchen", ["kitchen", "garage", "attic"])
    assert order == ["kitchen", "garage", "attic"]


def test_object_never_moved_case():
    # If Seeker never left (no move event witnessed as absent), belief == last
    # placement location. We approximate this with the F condition's initial
    # placement: the Seeker's belief is always where it last saw the object.
    f, _ = generate_pair(seed=5)
    assert first_search_location(f.ground_truth_belief_location) == f.initial_location


def test_true_belief_condition_seeker_checks_true_location():
    _, t = generate_pair(seed=5)
    assert first_search_location(t.ground_truth_belief_location) == t.final_location


def test_seeker_applied_to_generated_scenario_matches_room_order_fallback():
    f, _ = generate_pair(seed=17)
    order = full_search_order(f.ground_truth_belief_location, f.room_order)
    assert order[0] == f.initial_location
    assert set(order) == {r.name for r in f.rooms}
