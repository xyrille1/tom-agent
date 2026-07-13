#!/usr/bin/env python
"""Batch runner CLI (FR9). Reads scenario pairs from data/scenarios, runs
them against configured (or mock) models, writes trials incrementally to
data/trials so the run is resumable across sessions/days.

Usage:
    python scripts/run_batch.py --dry-run              # see the call-count estimate first, always
    python scripts/run_batch.py --mock                 # exercise the full pipeline at zero cost, no keys needed
    python scripts/run_batch.py --limit-pairs 5         # small pilot batch against real free-tier APIs
    python scripts/run_batch.py                         # full run against every configured model
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from tom_bench.batch import run_batch  # noqa: E402
from tom_bench.clients.mock import MockClient  # noqa: E402
from tom_bench.clients.registry import get_configured_clients  # noqa: E402
from tom_bench.io_utils import SCENARIOS_DIR, TRIALS_DIR, load_scenario_pairs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the trial batch against configured models.")
    parser.add_argument("--dry-run", action="store_true", help="Estimate call counts without calling any API.")
    parser.add_argument(
        "--mock", action="store_true", help="Use a MockClient instead of real APIs (no cost, no keys needed)."
    )
    parser.add_argument(
        "--task-types", nargs="+", default=["interactive", "quiz"], choices=["interactive", "quiz"]
    )
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--scenarios-dir", type=Path, default=SCENARIOS_DIR)
    parser.add_argument("--trials-dir", type=Path, default=TRIALS_DIR)
    parser.add_argument(
        "--limit-pairs", type=int, default=None, help="Only run the first N scenario pairs (for a pilot batch)."
    )
    args = parser.parse_args()

    pairs = load_scenario_pairs(args.scenarios_dir)
    if not pairs:
        raise SystemExit(f"No scenario pairs found in {args.scenarios_dir}. Run scripts/generate_scenarios.py first.")
    if args.limit_pairs:
        pairs = pairs[: args.limit_pairs]

    if args.mock:
        clients = {"mock-model": MockClient(name="mock-model")}
    else:
        clients = get_configured_clients()
        if not clients:
            raise SystemExit(
                "No model API keys configured. Copy .env.example to .env and fill in at least one "
                "free-tier key, or pass --mock to exercise the pipeline at zero cost."
            )

    plan = run_batch(
        pairs,
        clients,
        args.task_types,
        trials_dir=args.trials_dir,
        max_retries=args.max_retries,
        dry_run=args.dry_run,
    )

    print(f"Scenario pairs: {len(pairs)}")
    print(f"Already-completed trials on disk: {plan.already_done}")
    verb = "Would call" if args.dry_run else "Called"
    print(f"{verb} model APIs {plan.total_calls} time(s) total:")
    for model_name, count in plan.n_calls_by_model.items():
        print(f"  {model_name}: {count}")
    if args.dry_run:
        print("\nDry run only -- no API calls were made. Re-run without --dry-run to execute.")


if __name__ == "__main__":
    main()
