"""Runs a single trial: build the prompt for a task type, call the model,
parse + score the answer, return a Trial record (FR8)."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from .clients.base import ModelClient
from .prompts import build_interactive_prompt, build_quiz_prompt
from .schema import Scenario, TaskType, Trial
from .scoring import score_interactive, score_quiz


def trial_id(scenario: Scenario, model_name: str, task_type: str) -> str:
    safe_model = model_name.replace("/", "_").replace(":", "_")
    return f"{scenario.id}__{safe_model}__{task_type}"


def build_prompt(scenario: Scenario, task_type: TaskType) -> str:
    if task_type == "interactive":
        return build_interactive_prompt(scenario)
    if task_type == "quiz":
        return build_quiz_prompt(scenario)
    raise ValueError(f"Unknown task_type: {task_type}")


def score_answer(scenario: Scenario, task_type: TaskType, raw_response: str):
    if task_type == "interactive":
        return score_interactive(scenario, raw_response)
    if task_type == "quiz":
        return score_quiz(scenario, raw_response)
    raise ValueError(f"Unknown task_type: {task_type}")


def run_single_trial(scenario: Scenario, client: ModelClient, task_type: TaskType) -> Trial:
    prompt = build_prompt(scenario, task_type)
    tid = trial_id(scenario, client.name, task_type)
    started = time.monotonic()
    try:
        raw = client.generate(prompt)
        if not isinstance(raw, str):
            raise TypeError(
                f"{client.name}.generate() must return str, got {type(raw).__name__}: {raw!r:.300}"
            )
    except Exception as exc:
        latency_ms = (time.monotonic() - started) * 1000
        return Trial(
            id=tid,
            scenario_id=scenario.id,
            pair_id=scenario.pair_id,
            condition=scenario.condition,
            model_name=client.name,
            task_type=task_type,
            prompt=prompt,
            raw_response=None,
            parsed_answer=None,
            is_correct=None,
            failure_tag=None,
            latency_ms=latency_ms,
            error=str(exc),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    latency_ms = (time.monotonic() - started) * 1000
    parsed, is_correct, failure_tag = score_answer(scenario, task_type, raw)
    return Trial(
        id=tid,
        scenario_id=scenario.id,
        pair_id=scenario.pair_id,
        condition=scenario.condition,
        model_name=client.name,
        task_type=task_type,
        prompt=prompt,
        raw_response=raw,
        parsed_answer=parsed,
        is_correct=is_correct,
        failure_tag=failure_tag,
        latency_ms=latency_ms,
        error=None,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
