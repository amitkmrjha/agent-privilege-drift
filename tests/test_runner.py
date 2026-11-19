from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from privilege_drift.cli import app
from privilege_drift.data import DataError
from privilege_drift.llm import (
    ChatMessage,
    LLMCallError,
    LLMResult,
    LLMTimeoutError,
    MissingCredentialError,
)
from privilege_drift.runner import (
    Cell,
    CellStatus,
    GridConfig,
    RetryPolicy,
    RunDeps,
    WorkItem,
    check_cell,
    expand_cells,
    is_finished,
    load_grid,
    plan_all,
    plan_cell,
    read_manifest,
    run_cell,
    run_item,
)
from privilege_drift.schema import Scenario
from privilege_drift.subsets import SeedSchedule, Subset, build_seed_schedule
from test_react_agent import FINAL, SCENARIOS, act

MASTER = 20261119
IDS = sorted(s.id for s in SCENARIOS)
BY_ID = {s.id: s for s in SCENARIOS}
SCHEDULE = build_seed_schedule(IDS, n_cells=3, seeds_per_scenario=3, master_seed=MASTER)
NO_WAIT = RetryPolicy(attempts=3, wait_s=0.0)


def make_grid(tmp_path: Path, **over: Any) -> GridConfig:
    fields: dict[str, Any] = {
        "benchmark": "toolprivbench",
        "models": ("llama",),
        "rates": (0.0, 0.5, 1.0),
        "mediators": ("none",),
        "seeds_per_scenario": 2,
        "max_steps": 15,
        "window_k": 5,
        "data": tmp_path / "unused.jsonl",
        "subset": tmp_path / "unused-subset.json",
        "seed_schedule": tmp_path / "unused-schedule.json",
        "runs_dir": tmp_path / "runs",
    }
    return GridConfig(**{**fields, **over})


class AutoLLM:
    """Plays every scenario: one tool call, then a final answer. Can be told to misbehave."""

    def __init__(
        self, *, fail_first: int = 0, interrupt_after: int | None = None,
        error: Exception | None = None,
    ) -> None:  # fmt: skip
        self.calls = 0
        self.fail_first = fail_first
        self.interrupt_after = interrupt_after
        self.error = error

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        self.calls += 1
        if self.error is not None:
            raise self.error
        if self.interrupt_after is not None and self.calls > self.interrupt_after:
            raise KeyboardInterrupt
        if self.fail_first > 0:
            self.fail_first -= 1
            raise LLMTimeoutError("too slow", model_key=model_key, model="fake")
        if messages[-1]["content"].startswith("Observation:"):
            text = FINAL
        else:
            scenario = next(
                s for s in SCENARIOS if messages[1]["content"] == f"Task: {s.user_task}"
            )
            text = act(scenario.min_tools[0])
        return LLMResult(
            text=text, tokens_in=10, tokens_out=5, latency_s=0.01, model_key=model_key,
            model="fake", model_fingerprint="digest-1", seed=seed, finish_reason="stop", raw={},
        )  # fmt: skip


def deps(llm: AutoLLM, scenarios: dict[str, Scenario] = BY_ID) -> RunDeps:
    return RunDeps(llm=llm, scenarios=scenarios, master_seed=MASTER, max_steps=15, window_k=5)


@dataclass
class Setup:
    grid: GridConfig
    cell_idx: int

    @property
    def cell(self) -> Cell:
        return expand_cells(self.grid)[self.cell_idx]

    @property
    def items(self) -> list[WorkItem]:
        return plan_cell(self.grid, self.cell, IDS, SCHEDULE)

    @property
    def directory(self) -> Path:
        return self.grid.runs_dir / self.cell.cell_id


@pytest.fixture
def mid(tmp_path: Path) -> Setup:
    """The p = 0.5 cell: some calls fail, some do not."""
    return Setup(make_grid(tmp_path), cell_idx=1)


def go(setup: Setup, llm: AutoLLM, **kw: Any) -> Any:
    kw.setdefault("retry", NO_WAIT)
    return run_cell(setup.grid, setup.cell, setup.items, deps(llm), **kw)


# --- planning ------------------------------------------------------------------------------


def test_the_real_grid_has_18_cells_numbered_in_the_documented_order() -> None:
    grid = load_grid()
    cells = expand_cells(grid)
    assert len(cells) == 18
    assert [c.idx for c in cells] == list(range(18))
    assert cells[0].cell_id == "llama_p0_none" and cells[17].cell_id == "frontier_p0.6_ibac"
    for c in cells:
        m, r, k = (
            grid.models.index(c.model),
            grid.rates.index(c.p),
            grid.mediators.index(c.mediator),
        )
        assert c.idx == (m * len(grid.rates) + r) * len(grid.mediators) + k


def test_the_real_plan_is_2700_unique_runs_with_the_frozen_seeds() -> None:
    grid = load_grid()
    subset = Subset.model_validate_json(grid.subset.read_text())
    schedule = SeedSchedule.model_validate_json(grid.seed_schedule.read_text())
    items = plan_all(grid, subset.scenario_ids, schedule)
    assert len(items) == 2700 == len({i.run_id for i in items})
    assert all(i.seed == schedule.seeds_for(i.cell.idx, i.scenario_id)[i.seed_idx] for i in items)
    assert plan_all(grid, subset.scenario_ids, schedule) == items  # deterministic


def test_run_ids_are_stable_and_filesystem_safe(mid: Setup) -> None:
    first = mid.items[0]
    assert first.run_id == f"llama_p0.5_none__{IDS[0]}__s0"
    assert all(
        set(i.run_id) <= set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        for i in mid.items
    )
    assert [i.seed_idx for i in mid.items[:2]] == [0, 1]


@pytest.mark.parametrize(
    "bad",
    [{"rates": (0.0, 1.5)}, {"models": ()}, {"mediators": ("none", "none")}, {"max_steps": 0}],
)
def test_a_bad_grid_is_rejected(tmp_path: Path, bad: dict[str, Any]) -> None:
    path = tmp_path / "grid.yaml"
    good = make_grid(tmp_path).model_dump(mode="json")
    path.write_text(yaml.safe_dump({**good, **bad}))
    with pytest.raises(DataError, match="cannot load grid"):
        load_grid(path)


def test_planning_rejects_inputs_the_schedule_cannot_serve(tmp_path: Path) -> None:
    grid = make_grid(tmp_path)
    cell = expand_cells(grid)[0]
    with pytest.raises(DataError, match="more seeds"):
        plan_cell(make_grid(tmp_path, seeds_per_scenario=4), cell, IDS, SCHEDULE)
    with pytest.raises(DataError, match="missing from the seed schedule"):
        plan_cell(grid, cell, [*IDS, "NOT-IN-SCHEDULE"], SCHEDULE)
    far = cell.model_copy(update={"idx": 99})
    with pytest.raises(DataError, match="outside the seed schedule"):
        plan_cell(grid, far, IDS, SCHEDULE)


# --- running -------------------------------------------------------------------------------


def test_a_cell_runs_to_completion_and_passes_every_check(mid: Setup) -> None:
    report = go(mid, AutoLLM())
    assert (report.planned, report.completed, report.skipped, report.failed) == (6, 6, 0, ())
    assert report.status is CellStatus.COMPLETE
    assert all(is_finished(mid.directory, i.run_id) for i in mid.items)
    check = check_cell(mid.cell, mid.items, mid.directory, BY_ID, MASTER)
    assert check.ok, [c.detail for c in check.checks]
    assert check.draws == 6 and check.empirical_rate is not None


def test_the_manifest_records_what_was_run(mid: Setup) -> None:
    go(mid, AutoLLM())
    m = read_manifest(mid.directory)
    assert (m.cell_id, m.cell_idx, m.model, m.p, m.mediator) == (
        "llama_p0.5_none",
        1,
        "llama",
        0.5,
        "none",
    )
    assert (m.planned_runs, m.completed_runs, m.unfinished_runs, m.status) == (
        6, 6, (), CellStatus.COMPLETE,
    )  # fmt: skip
    assert m.model_fingerprints == ("digest-1",)
    assert m.config_hash == mid.grid.config_hash()
    assert m.seeds[IDS[0]] == tuple(i.seed for i in mid.items if i.scenario_id == IDS[0])
    assert m.finished_at >= m.started_at
    assert mid.grid.config_hash() != make_grid(mid.directory.parent, max_steps=7).config_hash()


def test_p_zero_and_p_one_cells_pass_the_replay(tmp_path: Path) -> None:
    for idx, expected_rate in ((0, 0.0), (2, 1.0)):
        setup = Setup(make_grid(tmp_path), cell_idx=idx)
        go(setup, AutoLLM())
        check = check_cell(setup.cell, setup.items, setup.directory, BY_ID, MASTER)
        assert check.ok and check.empirical_rate == expected_rate


def test_rerunning_a_finished_cell_does_nothing(mid: Setup) -> None:
    go(mid, AutoLLM())
    before = {p.name: p.read_bytes() for p in mid.directory.glob("*.jsonl")}
    llm = AutoLLM()
    report = go(mid, llm)
    assert (report.completed, report.skipped, llm.calls) == (0, 6, 0)
    assert {p.name: p.read_bytes() for p in mid.directory.glob("*.jsonl")} == before


def test_a_batch_killed_midway_resumes_without_duplicates_or_damage(mid: Setup) -> None:
    with pytest.raises(KeyboardInterrupt):
        go(mid, AutoLLM(interrupt_after=5))  # 2 calls per run: 2 runs finish, the 3rd is cut off
    done = {p.name: p.read_bytes() for p in mid.directory.glob("*.jsonl")}
    assert len([n for n in done if not n.endswith(".raw.jsonl")]) == 2
    assert not list(mid.directory.glob("*.tmp")) and not list(mid.directory.glob(".*"))
    assert not (mid.directory / "manifest.json").exists()  # a killed cell has no manifest

    report = go(mid, AutoLLM())
    assert (report.completed, report.skipped, report.status) == (4, 2, CellStatus.COMPLETE)
    after = {p.name: p.read_bytes() for p in mid.directory.glob("*.jsonl")}
    assert all(after[name] == data for name, data in done.items())  # finished runs untouched
    mains = sorted(n for n in after if not n.endswith(".raw.jsonl"))
    assert mains == sorted(f"{i.run_id}.jsonl" for i in mid.items)  # each run exactly once
    assert check_cell(mid.cell, mid.items, mid.directory, BY_ID, MASTER).ok


def test_a_corrupted_result_is_treated_as_unfinished_and_redone(mid: Setup) -> None:
    go(mid, AutoLLM())
    victim = mid.items[2].run_id
    (mid.directory / f"{victim}.jsonl").write_text("{this is not json\n")
    assert not is_finished(mid.directory, victim)
    report = go(mid, AutoLLM())
    assert (report.completed, report.skipped) == (1, 5)
    assert is_finished(mid.directory, victim)


def test_limit_runs_only_that_many_then_the_rest_later(mid: Setup) -> None:
    first = go(mid, AutoLLM(), limit=2)
    assert (first.completed, first.status) == (2, CellStatus.INCOMPLETE)
    assert len(read_manifest(mid.directory).unfinished_runs) == 4
    second = go(mid, AutoLLM())
    assert (second.completed, second.skipped, second.status) == (4, 2, CellStatus.COMPLETE)


# --- infrastructure errors -----------------------------------------------------------------


def test_infrastructure_errors_are_retried_with_back_off_and_logged_apart(mid: Setup) -> None:
    waits: list[float] = []
    llm = AutoLLM(fail_first=2)
    report = go(mid, llm, retry=RetryPolicy(attempts=4, wait_s=2.0), sleep=waits.append)
    assert report.status is CellStatus.COMPLETE and report.failed == ()
    assert waits == [2.0, 4.0]  # doubles each time
    lines = [
        json.loads(x)
        for x in (mid.directory / "infrastructure_errors.jsonl").read_text().splitlines()
    ]
    assert [(x["record_type"], x["attempt"], x["error"]) for x in lines] == [
        ("infrastructure_error", 1, "LLMTimeoutError"),
        ("infrastructure_error", 2, "LLMTimeoutError"),
    ]
    assert all(x["run_id"] == mid.items[0].run_id for x in lines)
    # the retried run's own data has no trace of the failures
    first = mid.directory / f"{mid.items[0].run_id}.jsonl"
    assert "infrastructure" not in first.read_text() and "Timeout" not in first.read_text()


def test_a_run_that_keeps_failing_is_left_for_the_next_invocation(mid: Setup) -> None:
    broken = AutoLLM(error=LLMCallError("503 from provider", model_key="llama", model="fake"))
    report = go(mid, broken, retry=RetryPolicy(attempts=2, wait_s=0.0), sleep=lambda s: None)
    assert (report.completed, len(report.failed), report.status) == (0, 6, CellStatus.INCOMPLETE)
    assert not [p for p in mid.directory.glob("*.jsonl") if "infrastructure" not in p.name]
    log = (mid.directory / "infrastructure_errors.jsonl").read_text().splitlines()
    assert len(log) == 6 * 2  # every failed attempt is logged, the last one included
    assert len(read_manifest(mid.directory).unfinished_runs) == 6

    again = go(mid, AutoLLM())  # the model service is back
    assert (again.completed, again.status) == (6, CellStatus.COMPLETE)
    assert check_cell(mid.cell, mid.items, mid.directory, BY_ID, MASTER).ok


def test_a_missing_api_key_stops_the_whole_batch(mid: Setup) -> None:
    llm = AutoLLM(error=MissingCredentialError("GEMINI_API_KEY is not set"))
    with pytest.raises(MissingCredentialError):
        go(mid, llm)
    assert llm.calls == 1  # no retries and no moving on to the next run


def test_an_unbuilt_mediator_is_a_clear_error(tmp_path: Path) -> None:
    grid = make_grid(tmp_path, mediators=("quantum",))
    item = plan_cell(grid, expand_cells(grid)[0], IDS, SCHEDULE)[0]
    with pytest.raises(KeyError, match="'quantum' is not implemented yet"):
        run_item(item, deps(AutoLLM()))


# --- integrity checks catch planted errors -------------------------------------------------


def edit_lines(path: Path, change: Callable[[list[dict[str, Any]]], None]) -> None:
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    change(rows)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture
def finished(mid: Setup) -> Setup:
    go(mid, AutoLLM())
    return mid


def failed_checks(s: Setup) -> dict[str, str]:
    report = check_cell(s.cell, s.items, s.directory, BY_ID, MASTER)
    return {c.name: c.detail for c in report.checks if not c.passed}


def test_a_missing_run_fails_the_presence_check(finished: Setup) -> None:
    victim = finished.items[3].run_id
    (finished.directory / f"{victim}.jsonl").unlink()
    assert victim in failed_checks(finished)["all_runs_present"]


def test_an_unexpected_extra_result_fails_the_presence_check(finished: Setup) -> None:
    source = finished.directory / f"{finished.items[0].run_id}.jsonl"
    (finished.directory / "stray_run.jsonl").write_text(source.read_text())
    assert "stray_run" in failed_checks(finished)["all_runs_present"]


def test_a_flipped_injection_flag_fails_the_replay(finished: Setup) -> None:
    item = finished.items[0]

    def flip(rows: list[dict[str, Any]]) -> None:
        call = next(r for r in rows if r["record_type"] == "call")
        call["injected"] = not call["injected"]

    edit_lines(finished.directory / f"{item.run_id}.jsonl", flip)
    failures = failed_checks(finished)
    assert set(failures) == {"injection_replay"}
    assert f"{item.run_id} step 1" in failures["injection_replay"]


def test_a_wrong_tier_fails_the_attribution_check(finished: Setup) -> None:
    def wrong_tier(rows: list[dict[str, Any]]) -> None:
        call = next(r for r in rows if r["record_type"] == "call")
        call["proposed_tier"] = 2
        call["is_violation"] = True

    edit_lines(finished.directory / f"{finished.items[1].run_id}.jsonl", wrong_tier)
    assert set(failed_checks(finished)) == {"tier_attribution"}


def test_a_summary_that_disagrees_with_its_calls_fails_the_attribution_check(
    finished: Setup,
) -> None:
    def lie(rows: list[dict[str, Any]]) -> None:
        rows[-1]["violations"] = 9

    edit_lines(finished.directory / f"{finished.items[1].run_id}.jsonl", lie)
    assert "summary" in failed_checks(finished)["tier_attribution"]


def test_the_checks_do_not_trust_the_data_they_check(finished: Setup) -> None:
    edit_lines(
        finished.directory / f"{finished.items[0].run_id}.jsonl",
        lambda rows: rows[0].update({"tool_name": "a_tool_that_does_not_exist"}),
    )
    assert "tier_attribution" in failed_checks(finished)


# --- command line --------------------------------------------------------------------------

cli = CliRunner()


def test_cli_lists_the_18_cells() -> None:
    result = cli.invoke(app, ["list-cells"])
    assert result.exit_code == 0
    assert len(result.stdout.strip().splitlines()) == 18
    assert " 0  llama_p0_none" in result.stdout


@pytest.mark.parametrize("command", ["run-cell", "check-cell"])
def test_cli_names_the_known_cells_for_an_unknown_one(command: str) -> None:
    result = cli.invoke(app, [command, "no_such_cell"])
    assert result.exit_code == 2
    assert "unknown cell" in result.output and "llama_p0_none" in result.output
