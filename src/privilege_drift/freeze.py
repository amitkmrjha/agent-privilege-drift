"""Render the frozen experiment inputs (subset, seed schedule, hashes) as text.

Shared by ``scripts/make_subsets.py`` and the tests, so "the committed files equal a fresh
regeneration" is checked with the same code that wrote them.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from privilege_drift.data import DataError, load_toolprivbench
from privilege_drift.data.toolprivbench import BENCHMARK_SHA256, REVISION
from privilege_drift.subsets import (
    MASTER_SEED,
    Subset,
    build_seed_schedule,
    build_subset,
    hashes_text,
    to_canonical_json,
)


def render_frozen_inputs(data_path: Path, prereg: Path) -> dict[str, str]:
    """Every output file as ``{path: text}``, including ``HASHES.txt``.

    Raises ``DataError`` if the data file is not the pinned ToolPrivBench revision.
    """
    actual = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if actual != BENCHMARK_SHA256:
        raise DataError(f"{data_path} does not match the pinned data ({actual}); run `make data`")
    subset = build_subset(
        load_toolprivbench(data_path),
        source="toolprivbench",
        dataset_revision=REVISION,
        data_sha256=actual,
    )
    schedule = build_seed_schedule(subset.scenario_ids)
    files = {
        str(prereg / "subsets" / "toolprivbench_50.json"): to_canonical_json(subset),
        str(prereg / "seed_schedule.json"): to_canonical_json(schedule),
    }
    files[str(prereg / "subsets" / "HASHES.txt")] = hashes_text(files)
    return files


# The pilot uses its own seed and scenarios, so it never reuses the experiment's draws.
PILOT_MASTER_SEED = MASTER_SEED + 1
PILOT_SIZE = 10
PILOT_CELLS = 9  # 1 model x 3 failure rates x 3 mediators


def render_pilot_inputs(data_path: Path, pilot_dir: Path, prereg: Path) -> dict[str, str]:
    """The pilot's scenarios and seeds as ``{path: text}``.

    The 10 scenarios are drawn from those NOT in the frozen experiment subset, so what the pilot
    teaches us (prompt fixes, step cap, window size) is never tuned on the experiment's own test
    items. The same hash-ranked method as the frozen subset (D21) is used, with a different seed.
    """
    actual = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if actual != BENCHMARK_SHA256:
        raise DataError(f"{data_path} does not match the pinned data ({actual}); run `make data`")
    frozen = _frozen_ids(prereg)
    candidates = [s for s in load_toolprivbench(data_path) if s.id not in frozen]
    subset = build_subset(
        candidates,
        source="toolprivbench",
        dataset_revision=REVISION,
        data_sha256=actual,
        total=PILOT_SIZE,
        master_seed=PILOT_MASTER_SEED,
    )
    schedule = build_seed_schedule(
        subset.scenario_ids, n_cells=PILOT_CELLS, master_seed=PILOT_MASTER_SEED
    )
    return {
        str(pilot_dir / "subset_10.json"): to_canonical_json(subset),
        str(pilot_dir / "seed_schedule.json"): to_canonical_json(schedule),
    }


def _frozen_ids(prereg: Path) -> set[str]:
    subset = Subset.model_validate_json((prereg / "subsets" / "toolprivbench_50.json").read_text())
    return set(subset.scenario_ids)
