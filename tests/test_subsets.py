from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from privilege_drift.data import load_toolprivbench
from privilege_drift.data.toolprivbench import BENCHMARK_SHA256, DEFAULT_PATH
from privilege_drift.freeze import render_frozen_inputs
from privilege_drift.subsets import (
    MASTER_SEED,
    N_CELLS,
    SEEDS_PER_SCENARIO,
    SUBSET_SIZE,
    SeedSchedule,
    Subset,
    build_seed_schedule,
    hashes_text,
    make_seed_pool,
    select_stratified,
    stratum_sizes,
    to_canonical_json,
)

PREREG = Path("prereg")
SUBSET_FILE = PREREG / "subsets" / "toolprivbench_50.json"
SCHEDULE_FILE = PREREG / "seed_schedule.json"
HASHES_FILE = PREREG / "subsets" / "HASHES.txt"

DOMAINS = [f"D{i}" for i in range(8)]
IDS = {d: [f"{d}-{n:03d}" for n in range(1, 61)] for d in DOMAINS}

needs_data = pytest.mark.skipif(not DEFAULT_PATH.is_file(), reason="run `make data` first")


# --- selection ---------------------------------------------------------------------------------


def test_fifty_over_eight_domains_is_six_or_seven_with_exactly_two_sevens() -> None:
    sizes = stratum_sizes(DOMAINS, 50, MASTER_SEED)
    assert sorted(sizes.values()) == [6, 6, 6, 6, 6, 6, 7, 7]


def test_even_split_has_no_remainder() -> None:
    assert set(stratum_sizes(DOMAINS, 48, MASTER_SEED).values()) == {6}


@pytest.mark.parametrize(("domains", "total"), [([], 5), (["a", "b", "c"], 2)])
def test_impossible_quota_is_rejected(domains: list[str], total: int) -> None:
    with pytest.raises(ValueError):
        stratum_sizes(domains, total, MASTER_SEED)


def test_selection_is_deterministic_and_ignores_input_order() -> None:
    first = select_stratified(IDS, 50, MASTER_SEED)
    shuffled = {d: list(reversed(ids)) for d, ids in reversed(list(IDS.items()))}
    assert select_stratified(shuffled, 50, MASTER_SEED) == first
    assert sum(len(v) for v in first.values()) == 50


def test_selection_changes_with_the_master_seed() -> None:
    assert select_stratified(IDS, 50, 1) != select_stratified(IDS, 50, 2)


def test_selected_ids_belong_to_their_domain_and_are_unique() -> None:
    chosen = select_stratified(IDS, 50, MASTER_SEED)
    flat = [i for ids in chosen.values() for i in ids]
    assert len(set(flat)) == 50
    assert all(i.startswith(d) for d, ids in chosen.items() for i in ids)


def test_a_domain_with_too_few_scenarios_is_rejected() -> None:
    small = {**IDS, "D0": IDS["D0"][:3]}
    with pytest.raises(ValueError, match="D0"):
        select_stratified(small, 50, MASTER_SEED)


# --- seeds -------------------------------------------------------------------------------------


def test_seed_pool_is_distinct_in_range_and_prefix_stable() -> None:
    pool = make_seed_pool(MASTER_SEED, 250)
    assert len(set(pool)) == 250 and all(0 <= s < 2**31 - 1 for s in pool)
    assert make_seed_pool(MASTER_SEED, 40) == pool[:40]


def test_schedule_uses_the_whole_pool_once_per_cell() -> None:
    ids = [f"S{i:02d}" for i in range(50)]
    schedule = build_seed_schedule(ids)
    assert len(schedule.cells) == N_CELLS
    for cell in schedule.cells:
        flat = [s for seeds in cell.values() for s in seeds]
        assert len(flat) == len(set(flat)) == 50 * SEEDS_PER_SCENARIO
        assert set(flat) == set(schedule.pool)


def test_cells_deal_the_pool_differently() -> None:
    schedule = build_seed_schedule([f"S{i:02d}" for i in range(50)])
    assert len({tuple(sorted(c.items())) for c in schedule.cells}) == N_CELLS


def test_three_seed_grid_is_a_prefix_of_the_five_seed_grid() -> None:
    schedule = build_seed_schedule([f"S{i:02d}" for i in range(10)])
    assert schedule.seeds_for(2, "S03", 3) == schedule.seeds_for(2, "S03")[:3]
    assert len(schedule.seeds_for(2, "S03")) == SEEDS_PER_SCENARIO


def test_schedule_rejects_a_repeated_seed() -> None:
    good = build_seed_schedule(["a", "b"], n_cells=1, seeds_per_scenario=2)
    cell = {k: v for k, v in good.cells[0].items()}
    cell["b"] = (cell["a"][0], cell["b"][1])
    with pytest.raises(ValidationError, match="repeat"):
        SeedSchedule(**{**good.model_dump(), "cells": (cell,)})


def test_subset_rejects_an_unbalanced_domain_split() -> None:
    domains = {f"A{i}": "A" for i in range(10)} | {"B0": "B", "C0": "C"}
    with pytest.raises(ValidationError, match="quota"):
        Subset(
            source="x", dataset_revision="r", data_sha256="h", master_seed=1, method="m",
            size=12, domains=domains,
        )  # fmt: skip


def test_canonical_json_is_stable_and_compact() -> None:
    schedule = build_seed_schedule(["a", "b"], n_cells=1, seeds_per_scenario=2)
    text = to_canonical_json(schedule)
    assert text == to_canonical_json(schedule) and text.endswith("}\n")
    assert json.loads(text) == json.loads(json.dumps(schedule.model_dump(mode="json")))
    assert '"pool": [' in text and "\n    " not in text.split('"pool": [')[1].split("]")[0]


# --- the committed, frozen files ---------------------------------------------------------------


def test_committed_subset_is_stratified_and_complete() -> None:
    subset = Subset.model_validate_json(SUBSET_FILE.read_text())
    assert subset.size == SUBSET_SIZE == len(subset.scenario_ids)
    assert sorted(subset.counts().values()) == [6, 6, 6, 6, 6, 6, 7, 7]
    assert len(subset.counts()) == 8
    assert (subset.master_seed, subset.data_sha256) == (MASTER_SEED, BENCHMARK_SHA256)


def test_committed_schedule_has_five_distinct_seeds_per_scenario_in_every_cell() -> None:
    subset = Subset.model_validate_json(SUBSET_FILE.read_text())
    schedule = SeedSchedule.model_validate_json(SCHEDULE_FILE.read_text())
    assert schedule.scenario_ids == subset.scenario_ids
    assert len(schedule.cells) == N_CELLS and schedule.seeds_per_scenario == 5
    assert len(set(schedule.pool)) == 250


def test_committed_hashes_match_the_committed_files() -> None:
    for line in HASHES_FILE.read_text().splitlines():
        digest, path = line.split("  ", 1)
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
    assert hashes_text({"x": "y"}).startswith(hashlib.sha256(b"y").hexdigest() + "  x")


@needs_data
def test_regenerating_from_the_data_reproduces_the_committed_files_exactly() -> None:
    for path, text in render_frozen_inputs(DEFAULT_PATH, PREREG).items():
        assert Path(path).read_text() == text, path


@needs_data
def test_subset_domains_agree_with_the_data() -> None:
    subset = Subset.model_validate_json(SUBSET_FILE.read_text())
    by_id = {s.id: s.domain for s in load_toolprivbench(DEFAULT_PATH)}
    assert {i: by_id[i] for i in subset.scenario_ids} == subset.domains
