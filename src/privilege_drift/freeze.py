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
