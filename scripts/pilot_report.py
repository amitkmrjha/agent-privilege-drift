"""Write docs/pilot.md from the pilot's results: throughput, health checks, extrapolation.

Usage:
    uv run python scripts/pilot_report.py [--out docs/pilot.md]

Reads runs/pilot/ (see configs/pilot_grid.yaml). Every number is computed from the result files,
never typed by hand. Only finished runs are counted, so it can be run while the pilot is going.
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from privilege_drift.analysis.reproduce import finished_runs
from privilege_drift.analysis.rq2 import classifier_accuracy
from privilege_drift.data import DataError
from privilege_drift.data.toolprivbench import DEFAULT_PATH as BENCHMARK_PATH
from privilege_drift.data.toolprivbench import load_toolprivbench
from privilege_drift.llm import load_models_config
from privilege_drift.runner import expand_cells, is_finished, load_grid, read_manifest
from privilege_drift.runner.grid import Cell, GridConfig
from privilege_drift.subsets import Subset
from privilege_drift.telemetry import load_calls, load_summaries, run_path

PILOT_GRID = Path("configs/pilot_grid.yaml")
FRONTIER_RUNS = Path(
    "runs/pilot_frontier"
)  # the small frontier test (configs/pilot_frontier_grid.yaml)
THRESHOLD = (
    0.05  # the plan's "roughly 5 %" for parse errors, max-steps hits and classifier failures
)
PUBLISHED_P0_VIOLATION_RATE = 0.35  # ToolPrivBench paper; the plan asks us to compare at p = 0

THROUGHPUT_HEADER = [
    "Cell", "Runs", "Model s/run", "Model calls/run", "Tool calls/run", "Tokens in", "Tokens out",
]  # fmt: skip
HEALTH_HEADER = [
    "Cell",
    "Parse errors",
    "Max-steps hit",
    "Format error (run lost)",
    "Classifier failed",
]
BEHAVIOUR_HEADER = [
    "Cell", "Violation rate", "Violations", "Executed violations", "Blocked calls", "Injected",
    "Task success",
]  # fmt: skip
EXTRAP_HEADER = ["Cell", "Runs", "Model s/run", "Estimated time"]


def load_cell(grid: GridConfig, cell: Cell) -> pd.DataFrame:
    directory = grid.runs_dir / cell.cell_id
    ids = sorted(
        p.name.removesuffix(".jsonl")
        for p in directory.glob("*.jsonl")
        if not p.name.endswith(".raw.jsonl") and "infrastructure" not in p.name
    )
    done = [i for i in ids if is_finished(directory, i)]
    return load_summaries([run_path(directory, i) for i in done])


def table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def pct(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{100 * x:.1f} %"


def hours(seconds: float) -> str:
    return f"{seconds / 3600:.1f} h"


def frontier_section(directory: Path, runs_per_cell: int, llama_calls: float) -> str:
    """The frontier arm's time, from the small separate test if its results are present."""
    paths = finished_runs(directory) if directory.is_dir() else []
    if not paths:
        return (
            "**Frontier arm: not measured here.** The small frontier test results "
            f"(`{directory}`) were not found. As a rough guide only, Llama makes {llama_calls:.1f} "
            "model calls per run on average in this pilot (decision D09)."
        )
    df = load_summaries(paths)
    secs = float(df["latency_s_total"].mean())
    one_cell, nine_cells = 3 * runs_per_cell, 9 * runs_per_cell
    return (
        f"**Frontier arm (first small test: {len(df)} runs of one easy scenario, no mediator, "
        f"`{directory}`):** {df['llm_calls'].mean():.1f} model calls and {secs:.1f} s of model "
        f"time per run on average. At that rate the model time is about "
        f"{hours(one_cell * secs)} for the 3 no-mediator cells ({one_cell} runs) and "
        f"{hours(nine_cells * secs)} for all 9 cells ({nine_cells} runs). **This is model time "
        "only.** The real limit is the provider's quota: the test hit `429` rate-limit errors "
        "and the quota is unknown (decision D09), so elapsed time could be many times longer. "
        f"The sample is too small, and its scenario too easy, to extrapolate calls per run "
        f"(Llama averages {llama_calls:.1f} in this pilot)."
    )


def model_and_steps_section(grid: GridConfig, cells: Sequence[Cell], pooled: pd.DataFrame) -> str:
    """The model's identity, the context margin, step usage and the IBAC classifier's accuracy.

    These feed the pending decisions D07 (step cap), D27 (classifier) and the method notes.
    """
    calls = load_calls(finished_runs(grid.runs_dir))
    digests: set[str] = set()
    commits: set[str] = set()
    for cell in cells:
        try:
            manifest = read_manifest(grid.runs_dir / cell.cell_id)
        except (OSError, ValueError):
            continue
        digests.update(manifest.model_fingerprints)
        commits.add((manifest.git_sha or "unknown")[:8])
    num_ctx = load_models_config().spec("llama").num_ctx
    flagged = int(calls["possible_truncation"].sum()) if not calls.empty else 0
    largest = int(calls["tokens_in"].max()) if not calls.empty else 0
    stops = ", ".join(f"{k} {v}" for k, v in sorted(pooled["stop_reason"].value_counts().items()))
    long_runs = int((pooled["llm_calls"] > 10).sum())
    try:
        domains = {s.id: s.domain for s in load_toolprivbench(BENCHMARK_PATH)}
    except DataError:
        domains = {}
    accuracy = classifier_accuracy(pooled, domains)
    if accuracy is None:
        classifier = "Classifier accuracy: not computed (the benchmark file is not downloaded)."
    else:
        classifier = (
            f"IBAC classifier: {accuracy['correct']} of {accuracy['n_scored']} pilot scenarios "
            f"classified into the benchmark's own domain ({pct(float(accuracy['accuracy']))}), "
            f"{accuracy['failed']} unreadable."
        )
    return f"""## Model, context and step usage

- Model digest(s) in the manifests: {", ".join(f"`{d}`" for d in sorted(digests)) or "none"}.
  Code commit(s): {", ".join(f"`{c}`" for c in sorted(commits)) or "unknown"}.
- Context: `num_ctx` {num_ctx}. The largest prompt on any call was {largest:,} tokens;
  {flagged} of {len(calls):,} calls were flagged as possibly truncated.
- Step cap (D07): {grid.max_steps} steps. How the {len(pooled)} runs ended: {stops}.
  Model calls per run: mean {pooled["llm_calls"].mean():.1f}, 95th percentile
  {pooled["llm_calls"].quantile(0.95):.1f}, maximum {int(pooled["llm_calls"].max())};
  {long_runs} runs used more than 10.
- {classifier}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--out", type=Path, default=Path("docs/pilot.md"))
    args = parser.parse_args()

    grid = load_grid(PILOT_GRID)
    main_grid = load_grid()
    full_runs_per_cell = (
        len(Subset.model_validate_json(main_grid.subset.read_text()).scenario_ids)
        * main_grid.seeds_per_scenario
    )
    cells = expand_cells(grid)
    data = {c.cell_id: load_cell(grid, c) for c in cells}

    throughput, health, behaviour, extrap = [], [], [], []
    total_seconds = 0.0
    pooled = pd.concat(data.values(), ignore_index=True) if data else pd.DataFrame()
    for cell in cells:
        df = data[cell.cell_id]
        if df.empty:
            continue
        n = len(df)
        secs = df["latency_s_total"].mean()
        throughput.append(
            [
                cell.cell_id, n, f"{secs:.1f}", f"{df['llm_calls'].mean():.1f}",
                f"{df['total_calls'].mean():.1f}", f"{df['tokens_in_total'].mean():.0f}",
                f"{df['tokens_out_total'].mean():.0f}",
            ]
        )  # fmt: skip
        health.append(
            [
                cell.cell_id, pct(df["parse_errors"].sum() / df["llm_calls"].sum()),
                pct(df["max_steps_hit"].mean()), pct(df["format_error"].mean()),
                pct(df["classifier_failed"].mean()) if cell.mediator == "ibac" else "n/a",
            ]
        )  # fmt: skip
        reached_injector = df["total_calls"].sum() - df["blocked_calls"].sum()
        behaviour.append(
            [
                cell.cell_id, pct(df["violation_rate"].mean()), f"{df['violations'].sum()}",
                f"{df['executed_violations'].sum()}", f"{df['blocked_calls'].sum()}",
                pct(df["injected_calls"].sum() / max(1, reached_injector)),
                pct(df["task_success"].mean()),
            ]
        )  # fmt: skip
        cell_seconds = full_runs_per_cell * secs
        total_seconds += cell_seconds
        extrap.append([cell.cell_id, f"{full_runs_per_cell}", f"{secs:.1f}", hours(cell_seconds)])

    runs_done = sum(len(d) for d in data.values())
    planned = len(cells) * 10 * grid.seeds_per_scenario
    wall = []
    for cell in cells:
        try:
            m = read_manifest(grid.runs_dir / cell.cell_id)
        except (OSError, ValueError):
            continue
        wall.append(
            [cell.cell_id, m.status.value, f"{(m.finished_at - m.started_at).total_seconds():.0f}"]
        )

    base = data[next(c.cell_id for c in cells if c.p == 0.0 and c.mediator == "none")]
    base_rate = base["violation_rate"].mean() if not base.empty else float("nan")
    calls_per_run = pooled["llm_calls"].mean() if runs_done else float("nan")
    model_text = model_and_steps_section(grid, cells, pooled) if runs_done else ""
    frontier_text = frontier_section(FRONTIER_RUNS, full_runs_per_cell, calls_per_run)

    text = f"""# Pilot

Generated by `scripts/pilot_report.py`. Do not edit by hand.

Local Llama (`llama3.1:8b-instruct-q4_K_M`) on {10} ToolPrivBench scenarios that are **not** in the
experiment's frozen subset, {grid.seeds_per_scenario} seeds each, 3 failure rates, 3 mediators
(`configs/pilot_grid.yaml`, results in `runs/pilot/`). **{runs_done} of {planned} runs finished.**
The frontier model is not part of this pilot (decision D20). A first small test of it, in a separate
grid (`configs/pilot_frontier_grid.yaml`), is summarised in decision D09.

## Throughput (per run, means)

Model time is the summed latency of the agent's model calls. It leaves out the IBAC classifier,
which makes about one short call per distinct task.

{table(THROUGHPUT_HEADER, throughput)}

## Health checks (the plan wants each under about {int(THRESHOLD * 100)} %)

Parse errors are unreadable replies per model call; the other columns are per run.

{table(HEALTH_HEADER, health)}

## What the agent did (diagnostic only, not a result)

Violation rate is the per-run fraction of proposed calls above the minimum tier (D11), averaged over
runs. "Injected" is the share of calls that reached the injector and got a 503.

{table(BEHAVIOUR_HEADER, behaviour)}

At p = 0 with no mediator the violation rate is **{pct(base_rate)}** on {len(base)} runs; the
ToolPrivBench paper reports about {pct(PUBLISHED_P0_VIOLATION_RATE)}. With few runs this is a rough
check only; a large gap would mean the scoring needs checking.

{model_text}
## Extrapolation to the full Llama grid

Each cell is {full_runs_per_cell} runs (50 scenarios x {main_grid.seeds_per_scenario} seeds).
Estimate = pilot mean model seconds per run for the same failure rate and mediator, times
{full_runs_per_cell}. Wall-clock will be a little longer.

{table(EXTRAP_HEADER, extrap)}

**Total for the 9 Llama cells: {hours(total_seconds)}.**

{frontier_text}

**AgentDojo arm: not measured.** The integration (#23) is not built and may be dropped, so there is
nothing to time. The plan expects it to be the largest Llama cost (long prompts), so if it is kept
it needs its own small test first.

## Wall-clock per cell in the pilot (seconds, from the manifests)

{table(["Cell", "Status", "Seconds"], wall)}
"""
    args.out.write_text(text)
    print(f"wrote {args.out} ({runs_done} of {planned} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
