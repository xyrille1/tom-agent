"""Deterministic Seeker NPC. Pure functions only -- no LLM, no randomness,
no I/O. Given a belief state, its search behavior is 100% predictable,
which is what makes the Fetch Assist task's ground truth unambiguous.

Rule (per PRD §4.1): search the last location the Seeker personally
observed the target object being placed in; if not found there, fall back
to a fixed room-order sweep.
"""
from __future__ import annotations


def first_search_location(belief_location: str) -> str:
    """The room the Seeker checks first -- this is what the Helper is scored
    against."""
    return belief_location


def full_search_order(belief_location: str, room_order: list[str]) -> list[str]:
    """Full search sequence: believed location first, then the fixed
    room-order sweep (skipping the believed location if it reappears)."""
    order = [belief_location]
    for room in room_order:
        if room not in order:
            order.append(room)
    return order
