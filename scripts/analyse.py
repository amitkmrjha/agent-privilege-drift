"""Regenerate every analysis number, table and figure from the finished runs.

Usage (or `make analyse`):
    uv run python scripts/analyse.py [--runs runs] [--out results] [--seed N]
                                     [--n-boot-rq1 10000] [--n-boot-rq3 1000]

Writes results/numbers.json, results/tables/*.csv, results/figures/*.png and the readable
reports. Re-running on the same run files gives byte-identical output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from privilege_drift.analysis.reproduce import DEFAULT_OUT, DEFAULT_RUNS, run_analysis
from privilege_drift.subsets import MASTER_SEED


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=MASTER_SEED)
    parser.add_argument("--n-boot-rq1", type=int, default=10_000)
    parser.add_argument("--n-boot-rq3", type=int, default=1_000)
    args = parser.parse_args()
    try:
        numbers = run_analysis(
            args.runs,
            args.out,
            seed=args.seed,
            n_boot_rq1=args.n_boot_rq1,
            n_boot_rq3=args.n_boot_rq3,
        )
    except ValueError as exc:
        parser.error(str(exc))
    inputs = numbers["inputs"]
    print(f"{inputs['n_runs']} runs, {inputs['n_calls']} calls -> {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
