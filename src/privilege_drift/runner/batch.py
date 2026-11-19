"""Run one cell unattended: skip finished runs, retry infrastructure errors, write a manifest.

Resume rule: a run is finished if its result file exists and parses as that run. Files are
written atomically (temp then rename, main file last), so a killed batch leaves either a whole
file or none; restarting simply runs whatever is missing.

Infrastructure errors (timeouts, 429/5xx, connection errors) are retried with back-off and are
logged apart from the run data, so they are never mistaken for agent behaviour or for an
injected 503. A run that still fails after the retries is left without a result file and listed
in the manifest, so the next invocation tries it again. A missing API key stops the whole batch.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from privilege_drift.llm import LLMCallError
from privilege_drift.runner.execute import RunDeps, run_item
from privilege_drift.runner.grid import Cell, GridConfig, WorkItem
from privilege_drift.runner.manifest import CellStatus, Manifest, git_info, write_manifest
from privilege_drift.telemetry import RunTelemetry, read_run, run_path, write_run
from privilege_drift.telemetry.recorder import Clock, utc_now

INFRA_LOG_NAME = "infrastructure_errors.jsonl"
_MESSAGE_LIMIT = 300


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 4  # tries per run, the first included
    wait_s: float = 2.0  # first back-off; doubles each time
    max_wait_s: float = 60.0


class CellReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_id: str
    planned: int
    skipped: int  # already had a valid result
    completed: int  # run in this invocation
    failed: tuple[str, ...]  # run ids still without a result
    status: CellStatus


def is_finished(directory: Path, run_id: str) -> bool:
    """True if the run's result file exists and is a valid record of that run."""
    path = run_path(directory, run_id)
    if not path.is_file():
        return False
    try:
        return read_run(path).summary.run_id == run_id
    except (OSError, ValueError, ValidationError):
        return False


def _log_infrastructure_error(
    directory: Path, item: WorkItem, error: Exception, attempt: int, now: datetime
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    line = {
        "record_type": "infrastructure_error",
        "run_id": item.run_id,
        "attempt": attempt,
        "timestamp": now.isoformat(),
        "error": type(error).__name__,
        "message": str(error)[:_MESSAGE_LIMIT],
    }
    with (directory / INFRA_LOG_NAME).open("a") as handle:
        handle.write(json.dumps(line) + "\n")


def run_cell(
    grid: GridConfig,
    cell: Cell,
    items: Sequence[WorkItem],
    deps: RunDeps,
    *,
    retry: RetryPolicy = RetryPolicy(),
    limit: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Clock = utc_now,
    on_item: Callable[[WorkItem, str], None] | None = None,
) -> CellReport:
    """Run every unfinished item of one cell (the first ``limit`` unfinished, if given)."""
    directory = grid.runs_dir / cell.cell_id
    started = clock()
    skipped = completed = 0
    failed: list[str] = []
    fingerprints: set[str] = set()
    remaining = limit

    for item in items:
        if is_finished(directory, item.run_id):
            skipped += 1
            continue
        if remaining is not None and remaining <= 0:
            continue
        outcome = _run_with_retries(item, deps, directory, retry, sleep, clock)
        if remaining is not None:
            remaining -= 1
        if outcome is None:
            failed.append(item.run_id)
            if on_item:
                on_item(item, "failed")
            continue
        telemetry, seen = outcome
        write_run(telemetry, directory)
        fingerprints |= seen
        completed += 1
        if on_item:
            on_item(item, "done")

    unfinished = [i.run_id for i in items if not is_finished(directory, i.run_id)]
    status = CellStatus.COMPLETE if not unfinished else CellStatus.INCOMPLETE
    sha, dirty = git_info()
    write_manifest(
        Manifest(
            cell_id=cell.cell_id,
            cell_idx=cell.idx,
            model=cell.model,
            p=cell.p,
            mediator=cell.mediator,
            config_hash=grid.config_hash(),
            git_sha=sha,
            git_dirty=dirty,
            model_fingerprints=tuple(sorted(fingerprints)),
            seeds=_seeds_by_scenario(items),
            planned_runs=len(items),
            completed_runs=len(items) - len(unfinished),
            unfinished_runs=tuple(unfinished),
            started_at=started,
            finished_at=clock(),
            status=status,
        ),
        directory,
    )
    return CellReport(
        cell_id=cell.cell_id,
        planned=len(items),
        skipped=skipped,
        completed=completed,
        failed=tuple(failed),
        status=status,
    )


def _seeds_by_scenario(items: Sequence[WorkItem]) -> dict[str, tuple[int, ...]]:
    grouped: dict[str, list[tuple[int, int]]] = {}
    for item in items:
        grouped.setdefault(item.scenario_id, []).append((item.seed_idx, item.seed))
    return {sid: tuple(seed for _, seed in sorted(pairs)) for sid, pairs in grouped.items()}


def _run_with_retries(
    item: WorkItem,
    deps: RunDeps,
    directory: Path,
    retry: RetryPolicy,
    sleep: Callable[[float], None],
    clock: Clock,
) -> tuple[RunTelemetry, frozenset[str]] | None:
    """The run's telemetry, or None if the model service kept failing."""

    def log_failure(state: RetryCallState) -> None:
        error = state.outcome.exception() if state.outcome else None
        if isinstance(error, Exception):
            _log_infrastructure_error(directory, item, error, state.attempt_number, clock())

    retrying = Retrying(
        stop=stop_after_attempt(retry.attempts),
        wait=wait_exponential(multiplier=retry.wait_s, max=retry.max_wait_s),
        retry=retry_if_exception_type(LLMCallError),
        after=log_failure,
        reraise=True,
        sleep=sleep,
    )
    try:
        return retrying(run_item, item, deps)
    except LLMCallError:
        return None
