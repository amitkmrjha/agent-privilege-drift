"""Expand ``configs/grid.yaml`` into cells and work items with fixed, deterministic names."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from privilege_drift.data import DataError
from privilege_drift.subsets import SeedSchedule

DEFAULT_GRID_PATH = Path("configs/grid.yaml")


class GridConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmark: str
    models: tuple[str, ...]
    rates: tuple[float, ...]
    mediators: tuple[str, ...]
    seeds_per_scenario: int
    max_steps: int
    window_k: int
    data: Path
    subset: Path
    seed_schedule: Path
    runs_dir: Path

    @field_validator("models", "rates", "mediators")
    @classmethod
    def _non_empty_and_unique(cls, value: tuple[object, ...]) -> tuple[object, ...]:
        if not value or len(set(value)) != len(value):
            raise ValueError("must be a non-empty list without repeats")
        return value

    @field_validator("rates")
    @classmethod
    def _rates_are_probabilities(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if any(not 0.0 <= r <= 1.0 for r in value):
            raise ValueError("each rate must be between 0 and 1")
        return value

    @field_validator("seeds_per_scenario", "max_steps", "window_k")
    @classmethod
    def _positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    def config_hash(self) -> str:
        """Identifies the settings a result was produced under (stored in each manifest)."""
        text = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(text.encode()).hexdigest()


class Cell(BaseModel):
    """One factor combination: a model, a failure rate and a mediator."""

    model_config = ConfigDict(frozen=True)

    idx: int
    model: str
    p: float
    mediator: str

    @property
    def cell_id(self) -> str:
        return f"{self.model}_p{self.p:g}_{self.mediator}"


class WorkItem(BaseModel):
    """One run: a scenario, played once with one seed, in one cell."""

    model_config = ConfigDict(frozen=True)

    cell: Cell
    scenario_id: str
    seed_idx: int
    seed: int

    @property
    def run_id(self) -> str:
        return f"{self.cell.cell_id}__{self.scenario_id}__s{self.seed_idx}"


def load_grid(path: Path | str = DEFAULT_GRID_PATH) -> GridConfig:
    try:
        return GridConfig.model_validate(yaml.safe_load(Path(path).read_text()))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise DataError(f"cannot load grid {path}: {exc}") from exc


def expand_cells(grid: GridConfig) -> list[Cell]:
    """All cells, numbered in the documented order (models outermost, mediators innermost)."""
    cells = [
        Cell(idx=0, model=model, p=p, mediator=mediator)
        for model in grid.models
        for p in grid.rates
        for mediator in grid.mediators
    ]
    return [c.model_copy(update={"idx": i}) for i, c in enumerate(cells)]


def find_cell(grid: GridConfig, cell_id: str) -> Cell:
    for cell in expand_cells(grid):
        if cell.cell_id == cell_id:
            return cell
    known = ", ".join(c.cell_id for c in expand_cells(grid))
    raise DataError(f"unknown cell {cell_id!r}; known cells: {known}")


def plan_cell(
    grid: GridConfig, cell: Cell, scenario_ids: Sequence[str], schedule: SeedSchedule
) -> list[WorkItem]:
    """The runs of one cell, ordered by scenario id then seed index."""
    if cell.idx >= len(schedule.cells):
        raise DataError(
            f"cell {cell.idx} is outside the seed schedule ({len(schedule.cells)} cells)"
        )
    if grid.seeds_per_scenario > schedule.seeds_per_scenario:
        raise DataError("grid asks for more seeds per scenario than the schedule holds")
    missing = set(scenario_ids) - set(schedule.scenario_ids)
    if missing:
        raise DataError(f"scenarios missing from the seed schedule: {sorted(missing)[:3]}")
    return [
        WorkItem(
            cell=cell,
            scenario_id=sid,
            seed_idx=k,
            seed=schedule.seeds_for(cell.idx, sid, grid.seeds_per_scenario)[k],
        )
        for sid in sorted(scenario_ids)
        for k in range(grid.seeds_per_scenario)
    ]


def plan_all(
    grid: GridConfig, scenario_ids: Sequence[str], schedule: SeedSchedule
) -> list[WorkItem]:
    return [
        item
        for cell in expand_cells(grid)
        for item in plan_cell(grid, cell, scenario_ids, schedule)
    ]
