"""Run one work item: build the agent, mediator and injector, play the scenario, record it."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from privilege_drift.agent import Completer, ReActAgent, StepRecord
from privilege_drift.data import StubExecutor
from privilege_drift.failure import DrawKey, FailureInjector
from privilege_drift.mediators import MacMediator, Mediator, NoneMediator, default_matrix
from privilege_drift.runner.grid import WorkItem
from privilege_drift.schema import Scenario
from privilege_drift.telemetry import RunContext, RunTelemetry, TelemetryRecorder
from privilege_drift.telemetry.recorder import Clock, utc_now

MediatorFactory = Callable[[], Mediator]


def default_mediators() -> dict[str, MediatorFactory]:
    """Mediators that exist so far. IBAC (#20) is added here when it is built."""
    return {"none": NoneMediator, "mac": lambda: MacMediator(default_matrix())}


@dataclass(frozen=True)
class RunDeps:
    """Everything a run needs that is not part of the work item itself."""

    llm: Completer
    scenarios: Mapping[str, Scenario]
    master_seed: int
    max_steps: int
    window_k: int
    mediators: Mapping[str, MediatorFactory] = field(default_factory=default_mediators)
    clock: Clock = utc_now


def run_item(item: WorkItem, deps: RunDeps) -> tuple[RunTelemetry, frozenset[str]]:
    """Play one run. Returns its telemetry and the model digests seen during it.

    Model-service errors are not caught here: they say nothing about the agent, so the batch
    decides whether to retry (D23).
    """
    scenario = deps.scenarios[item.scenario_id]
    factory = deps.mediators.get(item.cell.mediator)
    if factory is None:
        raise KeyError(f"mediator {item.cell.mediator!r} is not implemented yet")
    context = RunContext(
        run_id=item.run_id,
        cell_id=item.cell.cell_id,
        scenario_id=item.scenario_id,
        seed_idx=item.seed_idx,
        seed=item.seed,
        model=item.cell.model,
        p=item.cell.p,
        mediator=item.cell.mediator,
    )
    recorder = TelemetryRecorder(context, scenario, window_k=deps.window_k, clock=deps.clock)
    fingerprints: set[str] = set()

    def on_step(step: StepRecord) -> None:
        recorder.on_step(step)
        if step.llm.model_fingerprint is not None:
            fingerprints.add(step.llm.model_fingerprint)

    key = DrawKey(
        master_seed=deps.master_seed,
        cell_idx=item.cell.idx,
        scenario_id=item.scenario_id,
        seed_idx=item.seed_idx,
    )
    trace = ReActAgent(deps.llm, item.cell.model, max_steps=deps.max_steps, on_step=on_step).run(
        scenario,
        seed=item.seed,
        mediator=factory(),
        injector=FailureInjector(item.cell.p, key),
        executor=StubExecutor(scenario),
    )
    return recorder.finish(trace), frozenset(fingerprints)
