#!/usr/bin/env python
"""Aggregate all trials in data/trials into data/scores.json -- the single
file the static demo site reads for the leaderboard (FR10, FR11).

Usage:
    python scripts/compute_scores.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tom_bench.io_utils import (  # noqa: E402
    SCORES_PATH,
    TRIALS_DIR,
    TRIALS_INDEX_PATH,
    load_all_trials,
    save_scores,
    save_trials_index,
)
from tom_bench.scoring import compute_scores  # noqa: E402


def main() -> None:
    trials = load_all_trials(TRIALS_DIR)
    if not trials:
        raise SystemExit(f"No trials found in {TRIALS_DIR}. Run scripts/run_batch.py first.")

    scores = compute_scores(trials)
    path = save_scores(scores, SCORES_PATH)
    index_path = save_trials_index(trials, TRIALS_INDEX_PATH)

    print(f"Computed scores from {len(trials)} trials -> {path}")
    print(f"Wrote trial browse index -> {index_path}")
    for row in scores.rows:
        print(
            f"  {row.model_name} | {row.task_type} | {row.condition}: "
            f"acc={row.accuracy:.2f} (n={row.n}, CI=[{row.ci_low:.2f}, {row.ci_high:.2f}])"
        )
    for gap in scores.gaps:
        print(
            f"  ToM gap [{gap.model_name} / {gap.task_type}]: {gap.tom_gap:+.2f} "
            f"(F={gap.f_accuracy:.2f}, T={gap.t_accuracy:.2f})"
        )
    for agreement in scores.agreement:
        print(
            f"  Agreement [{agreement['model_name']}]: interactive={agreement['interactive_accuracy']}, "
            f"quiz={agreement['quiz_accuracy']}, pearson_r={agreement['pearson_r']}, "
            f"n_paired={agreement['n_paired']}"
        )


if __name__ == "__main__":
    main()
