"""Tier-1 scenario engine: generates matched (False-belief, True-belief) pairs.

Both scenarios in a pair share the same world, the same target object, and
the same move event. They differ in exactly one way: whether the Seeker
witnesses (T) or never learns of (F) the move -- which is what the PRD calls
"only the Seeker's awareness differs." Everything else (room count, object
count, number of narrated events) is held constant so the F/T gap measures
belief-modeling, not scenario complexity.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from .pools import (
    CONTAINERS,
    DISTRACTOR_TEMPLATES,
    FILLER_TEMPLATES,
    MOVE_TEMPLATES,
    NAMES,
    OBJECTS,
    PLACE_TEMPLATES,
    ROOMS,
    SEEKER_LEAVES_TEMPLATES,
    TOLD_TEMPLATES,
)
from .schema import Event, Room, Scenario


def _build_world(rng: random.Random) -> tuple[list[str], dict[str, list[str]], list[str]]:
    # 3-4 distinct rooms (not the PRD's full 2-4 range): guarantees a decoy
    # room genuinely distinct from both the true and believed locations,
    # which the quiz task's 3-way multiple choice needs to stay meaningful.
    n_rooms = rng.randint(3, 4)
    rooms = rng.sample(ROOMS, n_rooms)
    room_containers: dict[str, list[str]] = {}
    for room in rooms:
        k = rng.randint(1, 3)
        room_containers[room] = rng.sample(CONTAINERS, k)
    room_order = rooms[:]
    rng.shuffle(room_order)
    return rooms, room_containers, room_order


def generate_pair(seed: int, tier: int = 1) -> tuple[Scenario, Scenario]:
    """Generate a matched (F, T) scenario pair from a single seed.

    Reproducible: the same seed always yields the same world, event log,
    and ground truth (FR1, FR2, NFR "Reproducibility").
    """
    if tier != 1:
        raise NotImplementedError("Only Tier 1 is implemented in the MVP.")

    rng = random.Random(seed)
    rooms, room_containers, room_order = _build_world(rng)

    seeker = rng.choice(NAMES)
    target_obj = rng.choice(OBJECTS)

    initial_loc, away_room = rng.sample(rooms, 2)
    other_rooms = [r for r in rooms if r != initial_loc]
    final_loc = rng.choice(other_rooms)

    container_initial = rng.choice(room_containers[initial_loc])
    container_final = rng.choice(room_containers[final_loc])

    decoy_candidates = [r for r in rooms if r not in (initial_loc, final_loc)]
    decoy_room = rng.choice(decoy_candidates) if decoy_candidates else away_room

    has_distractor = rng.random() < 0.4

    events: list[Event] = []
    idx = 0

    place_text = rng.choice(PLACE_TEMPLATES).format(
        seeker=seeker, obj=target_obj, container=container_initial, room=initial_loc
    )
    events.append(
        Event(
            index=idx,
            type="place",
            text=place_text,
            actor=seeker,
            object=target_obj,
            from_loc=None,
            to_loc=initial_loc,
            seeker_present=True,
        )
    )
    idx += 1

    leave_text = rng.choice(SEEKER_LEAVES_TEMPLATES).format(seeker=seeker, room=away_room)
    events.append(
        Event(
            index=idx,
            type="seeker_leaves",
            text=leave_text,
            actor=seeker,
            object=None,
            from_loc=initial_loc,
            to_loc=away_room,
            seeker_present=False,
        )
    )
    idx += 1

    if has_distractor:
        distractor_rooms = [r for r in rooms if r not in (initial_loc, final_loc)] or rooms
        d_room = rng.choice(distractor_rooms)
        d_containers = room_containers[d_room]
        if len(d_containers) >= 2:
            c3, c4 = rng.sample(d_containers, 2)
        else:
            c3 = c4 = d_containers[0]
        obj2 = rng.choice([o for o in OBJECTS if o != target_obj])
        d_text = rng.choice(DISTRACTOR_TEMPLATES).format(
            container3=c3, distractor_room=d_room, obj2=obj2, container4=c4
        )
        events.append(
            Event(
                index=idx,
                type="distractor_move",
                text=d_text,
                actor=None,
                object=obj2,
                from_loc=d_room,
                to_loc=d_room,
                seeker_present=False,
            )
        )
        idx += 1

    move_text = rng.choice(MOVE_TEMPLATES).format(
        seeker=seeker,
        obj=target_obj,
        container=container_initial,
        container2=container_final,
        from_room=initial_loc,
        to_room=final_loc,
    )
    move_event = Event(
        index=idx,
        type="move",
        text=move_text,
        actor=None,
        object=target_obj,
        from_loc=initial_loc,
        to_loc=final_loc,
        seeker_present=False,
    )
    idx += 1

    filler_text = rng.choice(FILLER_TEMPLATES).format(seeker=seeker, room=away_room)
    filler_event = Event(
        index=idx,
        type="filler",
        text=filler_text,
        actor=seeker,
        object=None,
        from_loc=None,
        to_loc=away_room,
        seeker_present=False,
    )

    told_text = rng.choice(TOLD_TEMPLATES).format(
        seeker=seeker, obj=target_obj, room=away_room, container2=container_final, to_room=final_loc
    )
    told_event = Event(
        index=idx,
        type="told",
        text=told_text,
        actor=seeker,
        object=target_obj,
        from_loc=None,
        to_loc=final_loc,
        seeker_present=True,
    )

    now = datetime.now(timezone.utc).isoformat()
    pair_id = f"pair-{seed}"
    room_models = [Room(name=r, containers=room_containers[r]) for r in rooms]

    def build(condition: str, tail_event: Event) -> Scenario:
        full_log = events + [move_event, tail_event]
        belief = initial_loc if condition == "F" else final_loc
        return Scenario(
            id=f"{pair_id}-{condition}",
            pair_id=pair_id,
            condition=condition,  # type: ignore[arg-type]
            tier=tier,
            seed=seed,
            seeker_name=seeker,
            target_object=target_obj,
            rooms=room_models,
            room_order=room_order,
            initial_location=initial_loc,
            seeker_away_room=away_room,
            final_location=final_loc,
            event_log=[e.model_copy(update={"index": i}) for i, e in enumerate(full_log)],
            ground_truth_belief_location=belief,
            decoy_room=decoy_room,
            has_distractor=has_distractor,
            created_at=now,
        )

    return build("F", filler_event), build("T", told_event)


def narrative_text(scenario: Scenario) -> str:
    """Full narrative as a single string, used by the novelty check."""
    return " ".join(e.text for e in scenario.event_log)
