"""Write the RQ3 table and figure from run files.

Usage:
    uv run python scripts/rq3_report.py [--runs runs] [--model llama] [--mediator none]
        [--label primary|secondary] [--out docs/rq3.md] [--figure docs/rq3.png]
        [--seed 20261119] [--n-boot 1000]

Reads every finished run under ``--runs/<cell id>/`` (optionally only one model and/or mediator)
and writes a Markdown report and a figure. Only finished runs are used, so it can run while a
batch is going; on a batch that is still early it may refuse because a label has too few
positives. Pointing it at ``runs/pilot`` is a check of the pipeline, not a result. Every number
comes from the files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from privilege_drift.analysis.predictors import build_rq3, plot_importance, render_markdown
from privilege_drift.analysis.reproduce import finished_runs
from privilege_drift.telemetry import load_calls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--model")
    parser.add_argument("--mediator")
    parser.add_argument("--label", choices=["primary", "secondary"], default="primary")
    parser.add_argument("--out", type=Path, default=Path("docs/rq3.md"))
    parser.add_argument("--figure", type=Path, default=Path("docs/rq3.png"))
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--n-boot", type=int, default=1_000)
    args = parser.parse_args()

    paths = finished_runs(args.runs)
    if not paths:
        parser.error(f"no finished runs under {args.runs}")
    calls = load_calls(paths)
    if args.model:
        calls = calls[calls["model"] == args.model]
    if args.mediator:
        calls = calls[calls["mediator"] == args.mediator]
    if calls.empty:
        parser.error("no calls left after filtering")
    report = build_rq3(calls, seed=args.seed, label=args.label, n_boot=args.n_boot)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report))
    plot_importance(report, args.figure)
    print(f"{len(paths)} runs, {len(calls)} calls -> {args.out}, {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
