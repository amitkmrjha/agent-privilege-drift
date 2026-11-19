from __future__ import annotations

from pathlib import Path

import pytest

from privilege_drift.data.toolprivbench import DEFAULT_PATH
from privilege_drift.freeze import PILOT_CELLS, PILOT_MASTER_SEED, PILOT_SIZE, render_pilot_inputs
from privilege_drift.runner import expand_cells, load_grid
from privilege_drift.subsets import MASTER_SEED, SeedSchedule, Subset

PILOT = Path("pilot")
SUBSET = Subset.model_validate_json((PILOT / "subset_10.json").read_text())
SCHEDULE = SeedSchedule.model_validate_json((PILOT / "seed_schedule.json").read_text())
FROZEN = Subset.model_validate_json(Path("prereg/subsets/toolprivbench_50.json").read_text())
FROZEN_SCHEDULE = SeedSchedule.model_validate_json(Path("prereg/seed_schedule.json").read_text())


def test_the_pilot_uses_ten_scenarios_covering_every_domain() -> None:
    assert SUBSET.size == PILOT_SIZE == len(SUBSET.scenario_ids)
    assert len(SUBSET.counts()) == 8


def test_no_pilot_scenario_is_in_the_experiment_subset() -> None:
    assert not set(SUBSET.scenario_ids) & set(FROZEN.scenario_ids)


def test_the_pilot_shares_no_seed_with_the_experiment() -> None:
    assert SCHEDULE.master_seed == PILOT_MASTER_SEED != MASTER_SEED
    assert not set(SCHEDULE.pool) & set(FROZEN_SCHEDULE.pool)
    assert SCHEDULE.scenario_ids == SUBSET.scenario_ids and len(SCHEDULE.cells) == PILOT_CELLS


def test_the_pilot_grid_is_nine_llama_cells_writing_outside_the_experiments_runs() -> None:
    grid = load_grid("configs/pilot_grid.yaml")
    assert len(expand_cells(grid)) == PILOT_CELLS
    assert {c.model for c in expand_cells(grid)} == {"llama"}
    assert grid.runs_dir == Path("runs/pilot") and grid.runs_dir != load_grid().runs_dir
    assert grid.subset == PILOT / "subset_10.json"


@pytest.mark.skipif(not DEFAULT_PATH.is_file(), reason="run `make data` first")
def test_regenerating_the_pilot_inputs_reproduces_the_committed_files() -> None:
    for path, text in render_pilot_inputs(DEFAULT_PATH, PILOT, Path("prereg")).items():
        assert Path(path).read_text() == text, path
