"""The three checks a cell must pass before any analysis uses it (plan section 7.8, decision D25).

1. **all_runs_present**: every planned run (50 scenarios x 3 seeds = 150) has a valid result file,
   and no other result files are there.
2. **injection_replay**: every call's ``injected`` flag equals what the failure injector's draw
   says it must be. The draws are a fixed function of (master seed, cell, scenario, seed index,
   call number), so the check recomputes them and compares call by call. This replaces the
   plan's "empirical rate within +/-3 points of p": with a few hundred draws that band is under
   two standard deviations wide, so a correct cell would fail it by chance about one time in ten.
   The empirical rate is still reported.
3. **tier_attribution**: each call's tier, the scenario's minimum tier and the violation flag
   match the ground truth in the scenario, and each summary's violation count matches its calls.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from privilege_drift.failure import DrawKey, unit_draw
from privilege_drift.runner.batch import INFRA_LOG_NAME, is_finished
from privilege_drift.runner.grid import Cell, WorkItem
from privilege_drift.schema import Scenario
from privilege_drift.telemetry import read_run, run_path

_SHOWN = 5  # how many offending items a message lists


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    detail: str


class IntegrityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_id: str
    checks: tuple[CheckResult, ...]
    draws: int  # calls that reached the injector
    empirical_rate: float | None  # injected / draws, for information

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)


def _listed(items: Sequence[str]) -> str:
    shown = ", ".join(items[:_SHOWN])
    return shown + (f" (+{len(items) - _SHOWN} more)" if len(items) > _SHOWN else "")


def _check_present(
    directory: Path, items: Sequence[WorkItem]
) -> tuple[CheckResult, list[WorkItem]]:
    planned = {i.run_id for i in items}
    present = [i for i in items if is_finished(directory, i.run_id)]
    missing = sorted(planned - {i.run_id for i in present})
    on_disk = {
        p.name.removesuffix(".jsonl")
        for p in directory.glob("*.jsonl")
        if not p.name.endswith(".raw.jsonl") and p.name != INFRA_LOG_NAME
    }
    unexpected = sorted(on_disk - planned)
    problems = []
    if missing:
        problems.append(f"missing or invalid: {_listed(missing)}")
    if unexpected:
        problems.append(f"unexpected files: {_listed(unexpected)}")
    detail = f"{len(present)} of {len(planned)} runs present"
    return CheckResult(
        name="all_runs_present", passed=not problems, detail="; ".join([detail, *problems])
    ), present


def _check_injection(
    directory: Path, cell: Cell, present: Sequence[WorkItem], master_seed: int
) -> tuple[CheckResult, int, int]:
    wrong: list[str] = []
    draws = injected = 0
    for item in present:
        key = DrawKey(
            master_seed=master_seed,
            cell_idx=cell.idx,
            scenario_id=item.scenario_id,
            seed_idx=item.seed_idx,
        )
        n = 0  # index of the next draw: only allowed calls reach the injector (D03)
        for call in read_run(run_path(directory, item.run_id)).calls:
            expected = False
            if call.allowed:
                expected = unit_draw(key, n) < cell.p
                n += 1
                draws += 1
                injected += call.injected
            if call.injected != expected or (call.injected and call.http_code != 503):
                wrong.append(f"{item.run_id} step {call.step_idx}")
    rate = f"{injected / draws:.3f}" if draws else "n/a"
    detail = f"{draws} draws, empirical rate {rate} (p = {cell.p:g})"
    if wrong:
        detail += f"; calls that differ from the replay: {_listed(wrong)}"
    return CheckResult(name="injection_replay", passed=not wrong, detail=detail), draws, injected


def _check_tiers(
    directory: Path, present: Sequence[WorkItem], scenarios: Mapping[str, Scenario]
) -> CheckResult:
    wrong: list[str] = []
    for item in present:
        scenario = scenarios[item.scenario_id]
        run = read_run(run_path(directory, item.run_id))
        for call in run.calls:
            tool = scenario.tool(call.tool_name)
            if (
                tool is None
                or call.proposed_tier != int(tool.tier)
                or call.min_tier != int(scenario.min_tier)
                or call.is_violation != (int(tool.tier) > int(scenario.min_tier))
            ):
                wrong.append(f"{item.run_id} step {call.step_idx}")
        if run.summary.violations != sum(c.is_violation for c in run.calls):
            wrong.append(f"{item.run_id} summary")
    detail = "tiers match the ground truth" if not wrong else f"mismatches: {_listed(wrong)}"
    return CheckResult(name="tier_attribution", passed=not wrong, detail=detail)


def check_cell(
    cell: Cell,
    items: Sequence[WorkItem],
    directory: Path,
    scenarios: Mapping[str, Scenario],
    master_seed: int,
) -> IntegrityReport:
    """Run the three checks on a cell's result files."""
    present_check, present = _check_present(directory, items)
    try:
        injection, draws, injected = _check_injection(directory, cell, present, master_seed)
        tiers = _check_tiers(directory, present, scenarios)
    except (ValidationError, ValueError, OSError) as exc:
        broken = CheckResult(name="readable", passed=False, detail=f"cannot read results: {exc}")
        return IntegrityReport(
            cell_id=cell.cell_id, checks=(present_check, broken), draws=0, empirical_rate=None
        )
    return IntegrityReport(
        cell_id=cell.cell_id,
        checks=(present_check, injection, tiers),
        draws=draws,
        empirical_rate=injected / draws if draws else None,
    )
