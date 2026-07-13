"""Prompt contract for the Subject Agent (the model under test).

Both task types are emitted from the same Scenario object (FR4) so there is
no drift between what the interactive task and the quiz task describe.
"""
from __future__ import annotations

import hashlib
import random

from .schema import Scenario

INTERACTIVE_SYSTEM = (
    "You are the Helper in a household task. You will be given a complete, "
    "chronological event log -- including things one character did not "
    "personally witness. Reason about what that character actually knows, "
    "then answer using only the required JSON format."
)

QUIZ_SYSTEM = (
    "You will be given a complete, chronological event log -- including "
    "things one character did not personally witness. Answer the question "
    "about what that character believes, using only the required JSON format."
)


def _narrative(scenario: Scenario) -> str:
    return "\n".join(f"{i + 1}. {e.text}" for i, e in enumerate(scenario.event_log))


def build_interactive_prompt(scenario: Scenario) -> str:
    narrative = _narrative(scenario)
    rooms = ", ".join(r.name for r in scenario.rooms)
    return (
        f"{INTERACTIVE_SYSTEM}\n\n"
        f"Event log:\n{narrative}\n\n"
        f"{scenario.seeker_name} is about to go looking for the {scenario.target_object} "
        f"and will check exactly one location first. Place a helpful marker at the "
        f"location where {scenario.seeker_name} will look FIRST -- based on what "
        f"{scenario.seeker_name} personally knows, not necessarily where the "
        f"{scenario.target_object} actually is right now.\n\n"
        f"Valid locations: {rooms}\n\n"
        'Respond with ONLY a JSON object of the form {"assist_location": "<one of the valid locations>"}. '
        "No other text, no explanation."
    )


def _quiz_options(scenario: Scenario) -> list[str]:
    """Three options: the true (current) location, the believed (last-seen)
    location, and a decoy room -- deduplicated, order shuffled per-scenario
    so correctness never correlates with option position."""
    seen: list[str] = []
    for room in (scenario.final_location, scenario.initial_location, scenario.decoy_room):
        if room not in seen:
            seen.append(room)
    h = int(hashlib.sha256(scenario.id.encode()).hexdigest(), 16)
    random.Random(h).shuffle(seen)
    return seen


def build_quiz_prompt(scenario: Scenario) -> str:
    narrative = _narrative(scenario)
    options = _quiz_options(scenario)
    letters = "ABC"[: len(options)]
    option_lines = "\n".join(f"{letter}) {room}" for letter, room in zip(letters, options))
    return (
        f"{QUIZ_SYSTEM}\n\n"
        f"Event log:\n{narrative}\n\n"
        f"Question: Where will {scenario.seeker_name} look for the {scenario.target_object} FIRST?\n\n"
        f"{option_lines}\n\n"
        'Respond with ONLY a JSON object of the form {"answer": "<letter>"}. No other text, no explanation.'
    )


def quiz_option_map(scenario: Scenario) -> dict[str, str]:
    """Letter -> room name, matching the options rendered by build_quiz_prompt."""
    options = _quiz_options(scenario)
    letters = "ABC"[: len(options)]
    return dict(zip(letters, options))
