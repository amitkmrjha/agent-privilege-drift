"""Run the power analysis from the pilot's noise and write docs/power.md (issue #27).

Usage:
    uv run python scripts/power_analysis.py [--runs runs/pilot] [--out docs/power.md]
                                            [--seed N] [--n-rep 10000] [--mde-rep 2000]

Reads the finished pilot runs, estimates the noise at no failure injection, simulates the study,
and writes the report. The estimates rest on the 10 pilot scenarios and are rough, which the report
says. Takes about a minute at the default settings.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from privilege_drift.analysis.power import build_report, estimate_noise, write_report
from privilege_drift.analysis.reproduce import finished_runs
from privilege_drift.subsets import MASTER_SEED
from privilege_drift.telemetry import load_summaries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs/pilot"))
    parser.add_argument("--out", type=Path, default=Path("docs/power.md"))
    parser.add_argument("--seed", type=int, default=MASTER_SEED)
    parser.add_argument("--n-rep", type=int, default=10_000)
    parser.add_argument("--mde-rep", type=int, default=2_000)
    args = parser.parse_args()

    paths = finished_runs(args.runs)
    if not paths:
        parser.error(f"no finished runs under {args.runs}")
    try:
        noise = estimate_noise(load_summaries(paths))
    except ValueError as exc:
        parser.error(str(exc))
    report = build_report(noise, seed=args.seed, n_rep=args.n_rep, mde_rep=args.mde_rep)
    write_report(report, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
