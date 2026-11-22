"""Load the frozen inputs a grid refers to: the scenarios of the subset and the seed schedule."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pydantic import ValidationError

from privilege_drift.data import DataError, load_toolprivbench
from privilege_drift.runner.grid import GridConfig
from privilege_drift.schema import Scenario
from privilege_drift.subsets import SeedSchedule, Subset


@dataclass(frozen=True)
class PlanInputs:
    scenarios: dict[str, Scenario]  # only the scenarios in the frozen subset
    schedule: SeedSchedule

    @property
    def scenario_ids(self) -> list[str]:
        return sorted(self.scenarios)


def load_plan_inputs(grid: GridConfig) -> PlanInputs:
    """Read the subset, schedule and data; check the data is what the subset was drawn from."""
    try:
        subset = Subset.model_validate_json(grid.subset.read_text())
        schedule = SeedSchedule.model_validate_json(grid.seed_schedule.read_text())
        data_hash = hashlib.sha256(grid.data.read_bytes()).hexdigest()
    except (OSError, ValidationError) as exc:
        raise DataError(f"cannot load the frozen inputs: {exc}") from exc
    if data_hash != subset.data_sha256:
        raise DataError(
            f"{grid.data} is not the data the subset was drawn from "
            f"(hash {data_hash[:12]} vs {subset.data_sha256[:12]}); run `make data`"
        )
    if list(schedule.scenario_ids) != list(subset.scenario_ids):
        raise DataError("the seed schedule and the subset list different scenarios")
    by_id = {s.id: s for s in load_toolprivbench(grid.data)}
    return PlanInputs(scenarios={sid: by_id[sid] for sid in subset.scenario_ids}, schedule=schedule)
