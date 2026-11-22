"""Run one work item: build the agent, mediator and injector, play the scenario, record it."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from privilege_drift.agent import ReActAgent, StepRecord
from privilege_drift.data import StubExecutor
from privilege_drift.failure import DrawKey, FailureInjector
from privilege_drift.llm import Completer
from privilege_drift.mediators import (
    IbacMediator,
    IntentClassifier,
    IntentResult,
    MacMediator,
    Mediator,
    NoneMediator,
    default_matrix,
    default_policy,
    default_taxonomy,
)
from privilege_drift.runner.grid import WorkItem
from privilege_drift.schema import Scenario
from privilege_drift.telemetry import RunContext, RunTelemetry, TelemetryRecorder
from privilege_drift.telemetry.recorder import Clock, utc_now

MediatorFactory = Callable[[], Mediator]


def default_mediators(llm: Completer) -> dict[str, MediatorFactory]:
    """The three arms. IBAC's classifier uses ``llm`` and is shared by all runs of one batch, so
    a task is classified once however many runs use it."""
    shared: list[IntentClassifier] = []

    def ibac() -> Mediator:
        if not shared:
            shared.append(IntentClassifier(llm, default_taxonomy()))
        return IbacMediator(shared[0], default_policy(), default_taxonomy())

    return {"none": NoneMediator, "mac": lambda: MacMediator(default_matrix()), "ibac": ibac}


@dataclass(frozen=True)
class RunDeps:
    """Everything a run needs that is not part of the work item itself.

    ``mediators`` defaults to the three arms built on ``llm``; tests may pass their own.
    """

    llm: Completer
    scenarios: Mapping[str, Scenario]
    master_seed: int
    max_steps: int
    window_k: int
    mediators: Mapping[str, MediatorFactory] = field(default_factory=dict)
    clock: Clock = utc_now

    def __post_init__(self) -> None:
        if not self.mediators:
            object.__setattr__(self, "mediators", default_mediators(self.llm))


@runtime_checkable
class _Classifying(Protocol):
    """A mediator that classifies intent (IBAC); its result is logged with the run."""

    classification: IntentResult | None


def run_item(item: WorkItem, deps: RunDeps) -> tuple[RunTelemetry, frozenset[str]]:
    """Play one run. Returns its telemetry and the model digests seen during it.

    Model-service errors are not caught here: they say nothing about the agent, so the batch
    decides whether to retry (D23).
    """
    scenario = deps.scenarios[item.scenario_id]
    factory = deps.mediators.get(item.cell.mediator)
    if factory is None:
        raise KeyError(f"mediator {item.cell.mediator!r} is not implemented yet")
    mediator = factory()
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
    classifier_logged = False

    def on_step(step: StepRecord) -> None:
        nonlocal classifier_logged
        if not classifier_logged and isinstance(mediator, _Classifying):
            # The mediator classified in start_run, before this first step.
            result = mediator.classification
            if result is not None:
                recorder.set_classifier(result.intent, result.confidence, failed=result.failed)
            classifier_logged = True
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
        mediator=mediator,
        injector=FailureInjector(item.cell.p, key),
        executor=StubExecutor(scenario),
    )
    return recorder.finish(trace), frozenset(fingerprints)
