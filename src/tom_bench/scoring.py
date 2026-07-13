"""Parsing, scoring, failure tagging, and aggregate metrics (FR10-FR12)."""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone

from .prompts import quiz_option_map
from .schema import ModelGapRow, Scenario, ScoreRow, ScoresFile, Trial

FAILURE_UNPARSEABLE = "unparseable"
FAILURE_TRUE_STATE = "used_true_state_instead_of_belief"
FAILURE_NEITHER = "picked_neither_location"
FAILURE_WRONG_BELIEF = "wrong_belief_location"


def _extract_json_obj(text: str) -> dict | None:
    text = text.strip()
    candidates = [text]
    m = re.search(r"\{.*?\}", text, re.S)
    if m:
        candidates.append(m.group(0))
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def parse_interactive_answer(raw: str, valid_rooms: list[str]) -> str | None:
    obj = _extract_json_obj(raw)
    if obj is not None:
        loc = obj.get("assist_location")
        if isinstance(loc, str):
            loc = loc.strip()
            for room in valid_rooms:
                if loc.lower() == room.lower():
                    return room
    lower = raw.lower()
    mentioned = [room for room in valid_rooms if room.lower() in lower]
    if len(mentioned) == 1:
        return mentioned[0]
    return None


def parse_quiz_answer(raw: str, option_map: dict[str, str]) -> str | None:
    obj = _extract_json_obj(raw)
    if obj is not None:
        ans = obj.get("answer")
        if isinstance(ans, str):
            letter = ans.strip().upper().rstrip(")").lstrip("(")
            if letter in option_map:
                return option_map[letter]
            for room in option_map.values():
                if ans.strip().lower() == room.lower():
                    return room
    lower = raw.lower()
    mentioned = [room for room in option_map.values() if room.lower() in lower]
    if len(mentioned) == 1:
        return mentioned[0]
    return None


def _tag_failure(scenario: Scenario, parsed: str) -> str:
    if scenario.condition == "F" and parsed == scenario.final_location:
        return FAILURE_TRUE_STATE
    if parsed not in (scenario.initial_location, scenario.final_location):
        return FAILURE_NEITHER
    return FAILURE_WRONG_BELIEF


def score_interactive(scenario: Scenario, raw_response: str) -> tuple[str | None, bool | None, str | None]:
    valid_rooms = [r.name for r in scenario.rooms]
    parsed = parse_interactive_answer(raw_response, valid_rooms)
    if parsed is None:
        return None, None, FAILURE_UNPARSEABLE
    is_correct = parsed == scenario.ground_truth_belief_location
    failure_tag = None if is_correct else _tag_failure(scenario, parsed)
    return parsed, is_correct, failure_tag


def score_quiz(scenario: Scenario, raw_response: str) -> tuple[str | None, bool | None, str | None]:
    option_map = quiz_option_map(scenario)
    parsed = parse_quiz_answer(raw_response, option_map)
    if parsed is None:
        return None, None, FAILURE_UNPARSEABLE
    is_correct = parsed == scenario.ground_truth_belief_location
    failure_tag = None if is_correct else _tag_failure(scenario, parsed)
    return parsed, is_correct, failure_tag


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion. More reliable
    than the normal approximation at small n / extreme accuracy."""
    if n == 0:
        return (0.0, 0.0)
    phat = successes / n
    denom = 1 + z**2 / n
    center = phat + z**2 / (2 * n)
    margin = z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))
    low = (center - margin) / denom
    high = (center + margin) / denom
    return max(0.0, low), min(1.0, high)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / math.sqrt(vx * vy)


def compute_scores(trials: list[Trial]) -> ScoresFile:
    """Aggregate raw trials into the leaderboard summary (FR10, FR11)."""
    groups: dict[tuple[str, str, str], list[Trial]] = defaultdict(list)
    for t in trials:
        if t.is_correct is None:
            continue
        groups[(t.model_name, t.task_type, t.condition)].append(t)

    rows: list[ScoreRow] = []
    for (model, task_type, condition), group in sorted(groups.items()):
        n = len(group)
        successes = sum(1 for t in group if t.is_correct)
        acc = successes / n if n else 0.0
        lo, hi = wilson_ci(successes, n)
        rows.append(
            ScoreRow(
                model_name=model,
                task_type=task_type,  # type: ignore[arg-type]
                condition=condition,  # type: ignore[arg-type]
                accuracy=acc,
                ci_low=lo,
                ci_high=hi,
                n=n,
            )
        )

    gaps: list[ModelGapRow] = []
    by_model_task: dict[tuple[str, str], dict[str, ScoreRow]] = defaultdict(dict)
    for row in rows:
        by_model_task[(row.model_name, row.task_type)][row.condition] = row
    for (model, task_type), by_cond in sorted(by_model_task.items()):
        if "F" in by_cond and "T" in by_cond:
            f_row, t_row = by_cond["F"], by_cond["T"]
            gaps.append(
                ModelGapRow(
                    model_name=model,
                    task_type=task_type,  # type: ignore[arg-type]
                    f_accuracy=f_row.accuracy,
                    t_accuracy=t_row.accuracy,
                    tom_gap=t_row.accuracy - f_row.accuracy,
                    n_f=f_row.n,
                    n_t=t_row.n,
                )
            )

    # FR11: interactive vs quiz agreement per model, using trials paired by
    # scenario_id (a model answered the same scenario under both task types).
    agreement: list[dict] = []
    by_model: dict[str, dict[str, dict[str, Trial]]] = defaultdict(lambda: defaultdict(dict))
    for t in trials:
        if t.is_correct is None:
            continue
        by_model[t.model_name][t.task_type][t.scenario_id] = t

    for model, by_task in sorted(by_model.items()):
        interactive = by_task.get("interactive", {})
        quiz = by_task.get("quiz", {})
        shared_ids = sorted(set(interactive) & set(quiz))
        interactive_acc = (
            sum(1 for t in interactive.values() if t.is_correct) / len(interactive) if interactive else None
        )
        quiz_acc = sum(1 for t in quiz.values() if t.is_correct) / len(quiz) if quiz else None
        pearson = None
        if len(shared_ids) >= 2:
            xs = [1.0 if interactive[sid].is_correct else 0.0 for sid in shared_ids]
            ys = [1.0 if quiz[sid].is_correct else 0.0 for sid in shared_ids]
            pearson = _pearson(xs, ys)
        point_diff = (
            (interactive_acc - quiz_acc) if interactive_acc is not None and quiz_acc is not None else None
        )
        agreement.append(
            {
                "model_name": model,
                "interactive_accuracy": interactive_acc,
                "quiz_accuracy": quiz_acc,
                "point_difference": point_diff,
                "pearson_r": pearson,
                "n_paired": len(shared_ids),
            }
        )

    return ScoresFile(
        generated_at=datetime.now(timezone.utc).isoformat(),
        rows=rows,
        gaps=gaps,
        agreement=agreement,
    )
