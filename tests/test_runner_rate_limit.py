"""What the batch does when the provider's quota runs out (429). No network, no model."""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from typer.testing import CliRunner

from privilege_drift.cli import app
from privilege_drift.llm import (
    ChatMessage,
    LLMRateLimitError,
    LLMResult,
    QuotaExhaustedError,
)
from privilege_drift.runner import CellStatus, RetryPolicy, read_manifest
from test_runner import AutoLLM, Setup, go, make_grid

NO_WAIT = RetryPolicy(attempts=3, wait_s=0.0, rate_limited_runs_before_stop=2)


@pytest.fixture
def mid(tmp_path: Path) -> Setup:
    return Setup(make_grid(tmp_path), cell_idx=1)  # six runs in the cell


def limited() -> LLMRateLimitError:
    return LLMRateLimitError(
        "frontier rate limited on all 8 tries: quota", model_key="llama", model="fake"
    )


class QuotaLLM(AutoLLM):
    """Plays the scenarios like ``AutoLLM``, but raises a given error on chosen call numbers."""

    def __init__(self, error: Exception, on_calls: set[int]) -> None:
        super().__init__()
        self.quota_error = error
        self.on_calls = on_calls

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        if self.calls + 1 in self.on_calls:
            self.calls += 1
            raise self.quota_error
        return super().complete(messages, model_key=model_key, seed=seed, stop=stop)


def test_a_rate_limited_run_is_not_restarted_and_two_in_a_row_stop_the_batch(mid: Setup) -> None:
    llm = AutoLLM(error=limited())
    report = go(mid, llm, retry=NO_WAIT, sleep=lambda s: None)
    # one call per run: the run is not retried from scratch (that would spend its earlier calls
    # again); two such runs in a row stop the batch, leaving the other four untouched
    assert llm.calls == 2
    assert len(report.failed) == 2 and report.completed == 0
    assert report.stopped_reason is not None and "2 runs in a row" in report.stopped_reason
    manifest = read_manifest(mid.directory)
    assert manifest.status is CellStatus.INCOMPLETE and len(manifest.unfinished_runs) == 6
    log = [
        json.loads(x)
        for x in (mid.directory / "infrastructure_errors.jsonl").read_text().splitlines()
    ]
    assert [x["error"] for x in log] == ["LLMRateLimitError", "LLMRateLimitError"]


def test_a_success_in_between_resets_the_count(mid: Setup) -> None:
    # six runs, two model calls each: calls 1 and 4 hit the quota, the rest work
    llm = QuotaLLM(limited(), on_calls={1, 4})
    report = go(mid, llm, retry=NO_WAIT, sleep=lambda s: None)
    assert report.stopped_reason is None
    assert (report.completed, len(report.failed)) == (4, 2)


def test_the_next_invocation_resumes_the_runs_that_were_missing(mid: Setup) -> None:
    go(mid, AutoLLM(error=limited()), retry=NO_WAIT, sleep=lambda s: None)
    again = go(mid, AutoLLM())  # the quota is back
    assert (again.completed, again.status, again.stopped_reason) == (
        6,
        CellStatus.COMPLETE,
        None,
    )


def test_an_exhausted_quota_stops_the_batch_at_once(mid: Setup) -> None:
    error = QuotaExhaustedError("the provider asked for 5000s", retry_after_s=5000)
    llm = AutoLLM(error=error)
    report = go(mid, llm)
    assert llm.calls == 1 and report.stopped_reason == "the provider asked for 5000s"
    assert len(report.failed) == 1
    assert read_manifest(mid.directory).status is CellStatus.INCOMPLETE  # still written


def test_other_infrastructure_errors_still_restart_the_run(mid: Setup) -> None:
    llm = AutoLLM(fail_first=2)  # two timeouts, then it works
    report = go(mid, llm, retry=RetryPolicy(attempts=4, wait_s=0.0), sleep=lambda s: None)
    assert report.status is CellStatus.COMPLETE and report.stopped_reason is None


def test_the_command_reports_the_stop_and_exits_with_an_error(
    mid: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    from privilege_drift import cli

    def fake_run_cell(*args: object, **kwargs: object) -> object:
        return go(mid, AutoLLM(error=limited()), retry=NO_WAIT, sleep=lambda s: None)

    monkeypatch.setattr(cli, "run_cell", fake_run_cell)
    monkeypatch.setattr(cli, "load_grid", lambda path: mid.grid)
    monkeypatch.setattr(cli, "load_plan_inputs", lambda grid: _Inputs())
    monkeypatch.setattr(cli, "plan_cell", lambda *a, **k: mid.items)
    monkeypatch.setattr(cli, "LLMClient", lambda config: object())
    monkeypatch.setattr(cli, "load_models_config", lambda: object())
    result = CliRunner().invoke(app, ["run-cell", mid.cell.cell_id])
    assert result.exit_code == 1
    assert "stopped early" in result.output


class _Inputs:
    scenarios: dict[str, object] = {}
    scenario_ids: list[str] = []

    class schedule:  # noqa: N801 - a stand-in object with the one attribute the command reads
        master_seed = 1
