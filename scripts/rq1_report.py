"""Write the RQ1 tables and figure from run files.

Usage:
    uv run python scripts/rq1_report.py [--runs runs] [--out docs/rq1.md] [--figure docs/rq1.png]
                                        [--seed 20261119] [--n-boot 10000]

Reads every finished run under ``--runs/<cell id>/`` and writes a Markdown report and a figure.
Only finished runs are used, so it can run while a batch is still going. Pointing it at
``runs/pilot`` is a sanity check of the pipeline, not a result: the pilot has only the open model
and ten scenarios, so there is no primary contrast. Every number comes from the files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from privilege_drift.analysis.reproduce import finished_runs
from privilege_drift.analysis.rq1 import build_rq1, plot_rates, render_markdown
from privilege_drift.telemetry import load_summaries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--out", type=Path, default=Path("docs/rq1.md"))
    parser.add_argument("--figure", type=Path, default=Path("docs/rq1.png"))
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--n-boot", type=int, default=10_000)
    args = parser.parse_args()

    paths = finished_runs(args.runs)
    if not paths:
        parser.error(f"no finished runs under {args.runs}")
    report = build_rq1(load_summaries(paths), seed=args.seed, n_boot=args.n_boot)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report))
    plot_rates(report.rates, args.figure)
    print(f"{len(paths)} runs -> {args.out}, {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
