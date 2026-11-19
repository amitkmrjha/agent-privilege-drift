"""Command line: list the cells, run one, check one.

    uv run privilege-drift list-cells
    uv run privilege-drift run-cell llama_p0.3_none [--limit 5]
    uv run privilege-drift check-cell llama_p0.3_none

``run-cell`` calls the model and can take hours for a whole cell. Use ``--limit`` for a small
trial. Re-running a cell only does the runs that have no valid result yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from privilege_drift.data import DataError
from privilege_drift.llm import LLMClient, LLMError, load_models_config
from privilege_drift.runner.batch import run_cell
from privilege_drift.runner.execute import RunDeps
from privilege_drift.runner.grid import (
    DEFAULT_GRID_PATH,
    expand_cells,
    find_cell,
    load_grid,
    plan_cell,
)
from privilege_drift.runner.inputs import load_plan_inputs
from privilege_drift.runner.integrity import check_cell
from privilege_drift.runner.manifest import CellStatus

app = typer.Typer(no_args_is_help=True, add_completion=False, help=__doc__)
GridOption = Annotated[Path, typer.Option("--grid", help="Path to the grid file.")]


def _fail(message: str) -> typer.Exit:
    typer.echo(f"error: {message}", err=True)
    return typer.Exit(2)


@app.command("list-cells")
def list_cells(grid_path: GridOption = DEFAULT_GRID_PATH) -> None:
    """Show every cell with its number and id."""
    try:
        for cell in expand_cells(load_grid(grid_path)):
            typer.echo(f"{cell.idx:>2}  {cell.cell_id}")
    except DataError as exc:
        raise _fail(str(exc)) from exc


@app.command("run-cell")
def run_cell_command(
    cell_id: str,
    grid_path: GridOption = DEFAULT_GRID_PATH,
    limit: Annotated[
        int | None, typer.Option(help="Run at most this many unfinished runs.")
    ] = None,
) -> None:
    """Run the unfinished runs of one cell, then write its manifest."""
    try:
        grid = load_grid(grid_path)
        cell = find_cell(grid, cell_id)
        inputs = load_plan_inputs(grid)
        items = plan_cell(grid, cell, inputs.scenario_ids, inputs.schedule)
        deps = RunDeps(
            llm=LLMClient(load_models_config()),
            scenarios=inputs.scenarios,
            master_seed=inputs.schedule.master_seed,
            max_steps=grid.max_steps,
            window_k=grid.window_k,
        )
        report = run_cell(
            grid,
            cell,
            items,
            deps,
            limit=limit,
            on_item=lambda item, state: typer.echo(f"{state:<7} {item.run_id}"),
        )
    except (DataError, LLMError, KeyError) as exc:
        raise _fail(str(exc)) from exc
    typer.echo(
        f"{report.cell_id}: {report.completed} run now, {report.skipped} already done, "
        f"{len(report.failed)} failed, status {report.status.value}"
    )
    if report.status is not CellStatus.COMPLETE:
        raise typer.Exit(1)


@app.command("check-cell")
def check_cell_command(cell_id: str, grid_path: GridOption = DEFAULT_GRID_PATH) -> None:
    """Run the three integrity checks on a cell's results."""
    try:
        grid = load_grid(grid_path)
        cell = find_cell(grid, cell_id)
        inputs = load_plan_inputs(grid)
        items = plan_cell(grid, cell, inputs.scenario_ids, inputs.schedule)
    except DataError as exc:
        raise _fail(str(exc)) from exc
    report = check_cell(
        cell, items, grid.runs_dir / cell.cell_id, inputs.scenarios, inputs.schedule.master_seed
    )
    for check in report.checks:
        typer.echo(f"{'PASS' if check.passed else 'FAIL'}  {check.name}: {check.detail}")
    if not report.ok:
        raise typer.Exit(1)
