"""The lane order of the run plan (D31), on the real grid. No model, no network."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from privilege_drift.runner import expand_cells, load_grid


def load_script() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts" / "run_plan.py"
    spec = importlib.util.spec_from_file_location("run_plan", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLAN = load_script()
CELLS = expand_cells(load_grid())

LLAMA_ORDER = [
    "llama_p0_none",
    "llama_p0.6_none",
    "llama_p0.3_none",
    "llama_p0_ibac",
    "llama_p0.6_ibac",
    "llama_p0_mac",
    "llama_p0.6_mac",
    "llama_p0.3_ibac",
    "llama_p0.3_mac",
]


def test_the_llama_lane_follows_the_pre_registered_order() -> None:
    assert [c.cell_id for c in PLAN.lane_cells(CELLS, "llama")] == LLAMA_ORDER


def test_the_frontier_lane_has_the_same_order_with_its_own_cells() -> None:
    ids = [c.cell_id for c in PLAN.lane_cells(CELLS, "frontier")]
    assert ids == [i.replace("llama_", "frontier_") for i in LLAMA_ORDER]


def test_the_primary_contrast_cells_come_first_in_each_lane() -> None:
    for model in ("llama", "frontier"):
        first_two = {(c.mediator, c.p) for c in PLAN.lane_cells(CELLS, model)[:2]}
        assert first_two == {("none", 0.0), ("none", 0.6)}


def test_the_two_lanes_together_cover_the_whole_grid_once() -> None:
    both = PLAN.lane_cells(CELLS, "llama") + PLAN.lane_cells(CELLS, "frontier")
    assert sorted(c.cell_id for c in both) == sorted(c.cell_id for c in CELLS)


def test_the_middle_failure_rate_for_mediators_is_last() -> None:
    last_two = [(c.mediator, c.p) for c in PLAN.lane_cells(CELLS, "llama")[-2:]]
    assert last_two == [("ibac", 0.3), ("mac", 0.3)]


def test_a_cell_with_no_place_in_the_order_is_an_error() -> None:
    odd = [c.model_copy(update={"mediator": "quantum"}) for c in CELLS if c.model == "llama"]
    with pytest.raises(ValueError, match="no place in the priority order"):
        PLAN.lane_cells(odd, "llama")
