#!/usr/bin/env python
"""Generate N matched (F, T) Tier-1 scenario pairs, running each through the
novelty check and skipping/regenerating on collision (FR1-FR3, FR5).

Usage:
    python scripts/generate_scenarios.py --n 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tom_bench.generator import generate_pair, narrative_text  # noqa: E402
from tom_bench.io_utils import SCENARIOS_DIR, save_scenario  # noqa: E402
from tom_bench.novelty import load_reference_corpus, novelty_check  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate matched (F, T) Tier-1 scenario pairs.")
    parser.add_argument("--n", type=int, default=50, help="Number of matched pairs to generate.")
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=SCENARIOS_DIR)
    args = parser.parse_args()

    corpus = load_reference_corpus()
    seed = args.start_seed
    produced = 0
    rejected = 0
    max_attempts = args.n * 50 + 100

    while produced < args.n:
        if seed - args.start_seed > max_attempts:
            raise SystemExit(
                f"Aborting: {rejected} seeds rejected by the novelty check without reaching "
                f"{args.n} pairs. This should not happen with the default reference corpus -- "
                "check pools.py / novelty.py for a regression."
            )
        f, t = generate_pair(seed)
        ok_f, score_f, _ = novelty_check(narrative_text(f), corpus)
        ok_t, score_t, _ = novelty_check(narrative_text(t), corpus)
        if ok_f and ok_t:
            save_scenario(f, args.out_dir)
            save_scenario(t, args.out_dir)
            produced += 1
        else:
            rejected += 1
        seed += 1

    print(f"Generated {produced} scenario pairs ({produced * 2} scenarios) into {args.out_dir}")
    print(f"Rejected {rejected} seed(s) for insufficient novelty margin (100% of published scenarios pass)")


if __name__ == "__main__":
    main()
