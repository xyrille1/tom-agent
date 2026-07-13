"""Load/save helpers for the repo-as-database layout (FR5, FR16)."""
from __future__ import annotations

from pathlib import Path

from .schema import Scenario, ScoresFile, Trial

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "data" / "scenarios"
TRIALS_DIR = REPO_ROOT / "data" / "trials"
SCORES_PATH = REPO_ROOT / "data" / "scores.json"


def save_scenario(scenario: Scenario, directory: Path = SCENARIOS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scenario.id}.json"
    path.write_text(scenario.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_scenario(path: Path) -> Scenario:
    return Scenario.model_validate_json(path.read_text(encoding="utf-8"))


def load_all_scenarios(directory: Path = SCENARIOS_DIR) -> list[Scenario]:
    if not directory.exists():
        return []
    return [load_scenario(p) for p in sorted(directory.glob("*.json"))]


def load_scenario_pairs(directory: Path = SCENARIOS_DIR) -> list[tuple[Scenario, Scenario]]:
    scenarios = load_all_scenarios(directory)
    by_pair: dict[str, dict[str, Scenario]] = {}
    for s in scenarios:
        by_pair.setdefault(s.pair_id, {})[s.condition] = s
    pairs = []
    for pair_id in sorted(by_pair):
        by_cond = by_pair[pair_id]
        if "F" in by_cond and "T" in by_cond:
            pairs.append((by_cond["F"], by_cond["T"]))
    return pairs


def load_all_trials(directory: Path = TRIALS_DIR) -> list[Trial]:
    if not directory.exists():
        return []
    trials = []
    for p in sorted(directory.glob("*.json")):
        trials.append(Trial.model_validate_json(p.read_text(encoding="utf-8")))
    return trials


def save_scores(scores: ScoresFile, path: Path = SCORES_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(scores.model_dump_json(indent=2), encoding="utf-8")
    return path
