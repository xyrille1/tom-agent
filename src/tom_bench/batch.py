"""Batch runner (FR9): N scenarios x M models x 2 conditions x 2 task types,
paced to respect free-tier rate limits, with retries + backoff on 429s, and
incremental resumable writes so a run can pause and resume across days if a
daily quota is hit.

Resumability model: a trial is only ever written to disk once its call to
the provider actually succeeded (even if the response was unparseable --
that's still real data). A trial whose call failed outright (network error,
non-2xx after retries exhausted) is *not* written, so the next invocation
of run_batch will simply retry it -- this is what makes a daily-quota-cutoff
run resumable without a separate "retry queue" concept.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .clients.base import ModelClient
from .runner import run_single_trial, trial_id
from .schema import Scenario, TaskType, Trial

DEFAULT_TRIALS_DIR = Path(__file__).resolve().parents[2] / "data" / "trials"

RETRYABLE_MARKERS = ("429", "503", "Server disconnected", "timeout", "Timeout")


@dataclass
class BatchPlan:
    n_calls_by_model: dict[str, int]
    total_calls: int
    already_done: int


def plan_batch(
    scenario_pairs: list[tuple[Scenario, Scenario]],
    clients: dict[str, ModelClient],
    task_types: list[TaskType],
    trials_dir: Path = DEFAULT_TRIALS_DIR,
) -> BatchPlan:
    n_calls_by_model = {name: 0 for name in clients}
    already_done = 0
    for f_scenario, t_scenario in scenario_pairs:
        for scenario in (f_scenario, t_scenario):
            for model_name, client in clients.items():
                for task_type in task_types:
                    tid = trial_id(scenario, model_name, task_type)
                    if (trials_dir / f"{tid}.json").exists():
                        already_done += 1
                        continue
                    n_calls_by_model[model_name] += 1
    return BatchPlan(
        n_calls_by_model=n_calls_by_model,
        total_calls=sum(n_calls_by_model.values()),
        already_done=already_done,
    )


def _save_trial(trial: Trial, trials_dir: Path) -> None:
    trials_dir.mkdir(parents=True, exist_ok=True)
    (trials_dir / f"{trial.id}.json").write_text(trial.model_dump_json(indent=2), encoding="utf-8")


def _run_with_retries(scenario: Scenario, client: ModelClient, task_type: TaskType, max_retries: int) -> Trial:
    backoff = 2.0
    attempt = 0
    while True:
        trial = run_single_trial(scenario, client, task_type)
        if trial.error is None:
            return trial
        retryable = any(marker in trial.error for marker in RETRYABLE_MARKERS)
        attempt += 1
        if not retryable or attempt > max_retries:
            return trial
        time.sleep(backoff)
        backoff *= 2


def run_batch(
    scenario_pairs: list[tuple[Scenario, Scenario]],
    clients: dict[str, ModelClient],
    task_types: list[TaskType],
    trials_dir: Path = DEFAULT_TRIALS_DIR,
    max_retries: int = 3,
    dry_run: bool = False,
    on_trial: Callable[[Trial], None] | None = None,
) -> BatchPlan:
    plan = plan_batch(scenario_pairs, clients, task_types, trials_dir)
    if dry_run:
        return plan

    last_call_at: dict[str, float] = {}

    for f_scenario, t_scenario in scenario_pairs:
        for scenario in (f_scenario, t_scenario):
            for model_name, client in clients.items():
                for task_type in task_types:
                    tid = trial_id(scenario, model_name, task_type)
                    path = trials_dir / f"{tid}.json"
                    if path.exists():
                        continue

                    min_interval = getattr(client, "min_interval_seconds", 0.0)
                    prev = last_call_at.get(model_name)
                    if prev is not None and min_interval > 0:
                        elapsed = time.monotonic() - prev
                        if elapsed < min_interval:
                            time.sleep(min_interval - elapsed)

                    trial = _run_with_retries(scenario, client, task_type, max_retries)
                    last_call_at[model_name] = time.monotonic()

                    if trial.raw_response is not None:
                        _save_trial(trial, trials_dir)
                    if on_trial:
                        on_trial(trial)
    return plan
