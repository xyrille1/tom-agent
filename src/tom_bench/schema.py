"""Core data schema for the Theory-of-Mind benchmark.

Scenario == one procedurally generated trial world + event log + ground truth.
Every scenario belongs to a `pair_id` that links its False-belief (F) and
matched True-belief control (T) counterpart, generated from the same
underlying world so the two differ only in the Seeker's awareness of the
belief-inducing move event.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Condition = Literal["F", "T"]
TaskType = Literal["interactive", "quiz"]
EventType = Literal["place", "seeker_leaves", "move", "told", "filler", "distractor_move"]


class Room(BaseModel):
    name: str
    containers: list[str]


class Event(BaseModel):
    index: int
    type: EventType
    text: str
    actor: str | None = None
    object: str | None = None
    from_loc: str | None = None
    to_loc: str | None = None
    seeker_present: bool


class Scenario(BaseModel):
    id: str
    pair_id: str
    condition: Condition
    tier: int = 1
    seed: int
    seeker_name: str
    target_object: str
    rooms: list[Room]
    room_order: list[str]
    initial_location: str
    seeker_away_room: str
    final_location: str
    event_log: list[Event]
    ground_truth_belief_location: str
    decoy_room: str
    has_distractor: bool = False
    created_at: str


class Trial(BaseModel):
    id: str
    scenario_id: str
    pair_id: str
    condition: Condition
    model_name: str
    task_type: TaskType
    prompt: str
    raw_response: str | None = None
    parsed_answer: str | None = None
    is_correct: bool | None = None
    failure_tag: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    created_at: str


class ScoreRow(BaseModel):
    model_name: str
    task_type: TaskType
    condition: Condition
    accuracy: float
    ci_low: float
    ci_high: float
    n: int


class ModelGapRow(BaseModel):
    model_name: str
    task_type: TaskType
    f_accuracy: float
    t_accuracy: float
    tom_gap: float
    n_f: int
    n_t: int


class ScoresFile(BaseModel):
    generated_at: str
    rows: list[ScoreRow] = Field(default_factory=list)
    gaps: list[ModelGapRow] = Field(default_factory=list)
    agreement: list[dict] = Field(default_factory=list)
