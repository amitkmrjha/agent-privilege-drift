from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from privilege_drift.agent import (
    FailureKind,
    LLMCallInfo,
    Outcome,
    ParseFailure,
    ReActAgent,
    RunTrace,
    StepRecord,
    StopReason,
)
from privilege_drift.data import StubExecutor
from privilege_drift.failure import DrawKey, FailureInjector
from privilege_drift.mediators import NoneMediator
from privilege_drift.schema import Decision, ToolCall, ToolResult
from privilege_drift.telemetry import (
    ErrorSurface,
    RunContext,
    RunTelemetry,
    TelemetryRecorder,
    is_complete,
    load_calls,
    load_summaries,
    read_run,
    run_path,
    write_run,
)
from test_react_agent import FINAL, SCENARIO, ScriptedLLM, act

S0, S1, S2 = (t.name for t in SCENARIO.tools[:3])  # least-privilege tools
R0 = SCENARIO.tools[3].name  # a risk tool
CTX = RunContext(
    run_id="run-0001", cell_id="cell-07", scenario_id=SCENARIO.id, seed_idx=1, seed=42,
    model="llama", p=0.6, mediator="none",
)  # fmt: skip
T0 = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


class Clock:
    """Each reading is one second after the last, so timestamps are exact and ordered."""

    def __init__(self) -> None:
        self.n = 0

    def __call__(self) -> datetime:
        self.n += 1
        return T0 + timedelta(seconds=self.n)


def info(tokens_out: int) -> LLMCallInfo:
    return LLMCallInfo(
        tokens_in=100, tokens_out=tokens_out, latency_s=0.5, finish_reason="stop",
        cached=False, possible_truncation=False, model_fingerprint=None,
    )  # fmt: skip


def action(
    step: int, tool: str, *, tokens_out: int, thought: str = "t", attempt: int = 0,
    allowed: bool = True, injected: bool = False,
) -> StepRecord:  # fmt: skip
    if not allowed:
        result = ToolResult(http_code=403, body="Access denied", injected=False)
    elif injected:
        result = ToolResult(http_code=503, body="Error 503", injected=True)
    else:
        result = ToolResult(http_code=200, body="ok")
    return StepRecord(
        step=step, attempt=attempt, outcome=Outcome.ACTION, llm_text=f"reply {step}.{attempt}",
        llm=info(tokens_out), thought=thought, proposed_call=ToolCall(name=tool),
        decision=Decision(allow=allowed, reason="ok" if allowed else "blocked by test"),
        result=result,
    )  # fmt: skip


def parse_error(step: int, *, tokens_out: int) -> StepRecord:
    return StepRecord(
        step=step, attempt=0, outcome=Outcome.PARSE_ERROR, llm_text="garbled", llm=info(tokens_out),
        thought="", parse_failure=ParseFailure(kind=FailureKind.NO_ACTION, detail="d"),
    )  # fmt: skip


# A hand-built run. Expected values below were worked out by hand from this table.
#
#  call  step.attempt  tool  result        tokens_out (cum incl. parse error)
#   1    1.0           S0    503           10  (10)
#   2    2.0           S0    503           20  (30)
#   -    3.0           parse error          7  (37)
#   3    3.1           R0    503 (allowed) 30  (67)
#   4    4.0           R0    blocked       40  (107)
#   5    5.0           S1    success       50  (157)
#   6    6.0           S2    success       60  (217)
STEPS = [
    action(1, S0, tokens_out=10, thought="first", injected=True),
    action(2, S0, tokens_out=20, thought="first", injected=True),
    parse_error(3, tokens_out=7),
    action(3, R0, tokens_out=30, attempt=1, injected=True),
    action(4, R0, tokens_out=40, allowed=False),
    action(5, S1, tokens_out=50),
    action(6, S2, tokens_out=60),
]


def record(steps: list[StepRecord], *, k: int = 3) -> RunTelemetry:
    recorder = TelemetryRecorder(CTX, SCENARIO, window_k=k, clock=Clock())
    for step in steps:
        recorder.on_step(step)
    trace = RunTrace(
        scenario_id=SCENARIO.id, model_key="llama", seed=42, max_steps=15, steps=tuple(steps),
        stop_reason=StopReason.MAX_STEPS,
    )  # fmt: skip
    return recorder.finish(trace)


@pytest.fixture(scope="module")
def run() -> RunTelemetry:
    return record(STEPS)


def test_predictors_match_the_hand_calculation(run: RunTelemetry) -> None:
    got = [
        (
            c.retry_since_success, c.rolling_503_rate, c.error_surface, c.blocks_prior,
            c.reasoning_tokens_cum,
        )
        for c in run.calls
    ]  # fmt: skip
    N, U, B, S = (
        ErrorSurface.NONE,
        ErrorSurface.SERVICE_UNAVAILABLE,
        ErrorSurface.BLOCKED,
        ErrorSurface.SUCCESS,
    )
    assert got == [
        (0, 0.0, N, 0, 10),
        (1, 1.0, U, 0, 30),
        (2, 1.0, U, 0, 67),
        (3, 1.0, U, 0, 107),
        (4, 2 / 3, B, 1, 157),
        (0, 1 / 3, S, 1, 217),
    ]


def test_outcome_flags_match_the_hand_calculation(run: RunTelemetry) -> None:
    got = [
        (c.is_violation, c.escalated_above_prior, c.min_tools_untried, c.is_opur, c.allowed)
        for c in run.calls
    ]
    assert got == [
        (False, False, 3, False, True),
        (False, False, 2, False, True),
        (True, True, 2, True, True),
        (True, False, 2, True, False),
        (False, False, 2, False, True),
        (False, False, 1, False, True),
    ]
    assert [c.proposed_tier for c in run.calls] == [1, 1, 2, 2, 1, 1]
    assert {c.min_tier for c in run.calls} == {1}


def test_failure_and_mediator_fields(run: RunTelemetry) -> None:
    assert [(c.injected, c.http_code) for c in run.calls] == [
        (True, 503), (True, 503), (True, 503), (False, 403), (False, 200), (False, 200),
    ]  # fmt: skip
    blocked = run.calls[3]
    assert blocked.block_reason == "blocked by test" and run.calls[0].block_reason is None


def test_a_call_record_never_depends_on_later_steps() -> None:
    """Feed the recorder only the first n steps: its records equal the first ones of a full run."""
    full = record(STEPS).records[:-1]
    for n in range(1, len(STEPS) + 1):
        prefix = record(STEPS[:n]).records[:-1]  # drop each run's own summary
        assert prefix == full[: len(prefix)], n


def test_a_calls_own_result_is_not_in_its_own_predictors() -> None:
    first_fails = record([action(1, S0, tokens_out=5, injected=True)]).calls[0]
    first_ok = record([action(1, S0, tokens_out=5)]).calls[0]
    assert (first_fails.retry_since_success, first_fails.rolling_503_rate) == (0, 0.0)
    assert (first_fails.error_surface, first_ok.error_surface) == (ErrorSurface.NONE,) * 2


def test_window_size_changes_the_rolling_rate_only() -> None:
    wide, narrow = record(STEPS, k=5), record(STEPS, k=1)
    assert wide.calls[4].rolling_503_rate == 3 / 4  # last 4 prior calls: 503, 503, 503, blocked
    assert narrow.calls[4].rolling_503_rate == 0.0  # last 1 prior call: blocked
    assert [c.retry_since_success for c in wide.calls] == [
        c.retry_since_success for c in narrow.calls
    ]
    assert wide.calls[0].rolling_window_k == 5 and narrow.calls[0].rolling_window_k == 1


def test_summary_matches_the_hand_calculation(run: RunTelemetry) -> None:
    s = run.summary
    assert (s.total_calls, s.violations, s.executed_violations) == (6, 2, 1)
    assert s.violation_rate == 2 / 6
    assert (s.blocked_calls, s.injected_calls, s.parse_errors, s.llm_calls) == (1, 3, 1, 7)
    assert (s.tokens_in_total, s.tokens_out_total) == (700, 217)
    assert s.latency_s_total == pytest.approx(3.5)
    assert (s.stop_reason, s.max_steps_hit, s.format_error, s.final_answer) == (
        "max_steps", True, False, None,
    )  # fmt: skip
    assert s.task_success is True and s.rolling_window_k == 3


def test_a_run_with_no_calls_has_no_violation_rate() -> None:
    recorder = TelemetryRecorder(CTX, SCENARIO, clock=Clock())
    steps = [parse_error(1, tokens_out=3)]
    recorder.on_step(steps[0])
    trace = RunTrace(
        scenario_id=SCENARIO.id, model_key="llama", seed=42, max_steps=15, steps=tuple(steps),
        stop_reason=StopReason.FORMAT_ERROR,
    )  # fmt: skip
    summary = recorder.finish(trace).summary
    assert (summary.total_calls, summary.violation_rate, summary.task_success) == (0, None, False)
    assert summary.format_error is True


def test_a_run_where_every_call_failed_is_not_a_success() -> None:
    summary = record([action(1, S0, tokens_out=5, injected=True)]).summary
    assert summary.task_success is False


def test_parse_errors_are_recorded_with_their_kind(run: RunTelemetry) -> None:
    (error,) = run.parse_errors
    assert (error.kind, error.step_idx, error.attempt, error.tokens_out) == ("no_action", 3, 0, 7)


def test_the_thought_is_hashed_not_stored(run: RunTelemetry) -> None:
    expected = hashlib.sha256(b"first").hexdigest()
    assert run.calls[0].cot_hash == run.calls[1].cot_hash == expected
    assert run.calls[2].cot_hash != expected
    assert "first" not in run.records[0].model_dump_json()


def test_raw_replies_are_kept_and_referenced(run: RunTelemetry) -> None:
    assert [r.text for r in run.raw] == [s.llm_text for s in STEPS]
    assert [c.raw_response_ref for c in run.calls] == [
        "run-0001.raw.jsonl:0", "run-0001.raw.jsonl:1", "run-0001.raw.jsonl:3",
        "run-0001.raw.jsonl:4", "run-0001.raw.jsonl:5", "run-0001.raw.jsonl:6",
    ]  # fmt: skip
    assert run.parse_errors[0].raw_response_ref == "run-0001.raw.jsonl:2"


def test_timestamps_come_from_the_injected_clock(run: RunTelemetry) -> None:
    stamps = [r.timestamp for r in run.calls + run.parse_errors]
    stamps.sort()  # the summary has no timestamp
    assert stamps == [T0 + timedelta(seconds=i) for i in range(1, 8)]  # 6 calls + 1 parse error


def test_the_classifier_result_is_copied_into_calls_and_summary() -> None:
    recorder = TelemetryRecorder(CTX, SCENARIO, clock=Clock())
    recorder.set_classifier("update_record", 0.8)
    recorder.on_step(STEPS[0])
    trace = RunTrace(
        scenario_id=SCENARIO.id, model_key="llama", seed=42, max_steps=15, steps=(STEPS[0],),
        stop_reason=StopReason.MAX_STEPS,
    )  # fmt: skip
    out = recorder.finish(trace)
    assert (out.calls[0].classifier_intent, out.calls[0].classifier_conf) == ("update_record", 0.8)
    assert (out.summary.classifier_intent, out.summary.classifier_failed) == (
        "update_record",
        False,
    )


# --- validation ----------------------------------------------------------------------------


def test_run_and_cell_ids_must_be_filesystem_safe() -> None:
    with pytest.raises(ValidationError, match="letters, digits"):
        RunContext.model_validate({**CTX.model_dump(), "run_id": "../evil"})


def test_recorder_rejects_a_mismatched_scenario_or_window() -> None:
    with pytest.raises(ValueError, match="context is for"):
        TelemetryRecorder(CTX.model_copy(update={"scenario_id": "OTHER"}), SCENARIO)
    with pytest.raises(ValueError, match="window_k"):
        TelemetryRecorder(CTX, SCENARIO, window_k=0)


def test_finish_rejects_a_trace_it_did_not_watch() -> None:
    recorder = TelemetryRecorder(CTX, SCENARIO, clock=Clock())
    recorder.on_step(STEPS[0])
    wrong = RunTrace(
        scenario_id=SCENARIO.id, model_key="llama", seed=42, max_steps=15, steps=tuple(STEPS),
        stop_reason=StopReason.MAX_STEPS,
    )  # fmt: skip
    with pytest.raises(ValueError, match="does not match"):
        recorder.finish(wrong)


# --- files ---------------------------------------------------------------------------------


def test_write_then_read_round_trips_and_the_main_file_marks_completion(
    tmp_path: Path, run: RunTelemetry
) -> None:
    assert not is_complete(tmp_path, "run-0001")
    path = write_run(run, tmp_path)
    assert path == run_path(tmp_path, "run-0001") and is_complete(tmp_path, "run-0001")
    assert read_run(path).records == run.records
    raw_lines = (tmp_path / "run-0001.raw.jsonl").read_text().splitlines()
    assert len(raw_lines) == len(run.raw)
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


def test_a_crash_while_writing_leaves_no_main_file_and_no_temp_files(
    tmp_path: Path, run: RunTelemetry, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = os.replace
    calls = {"n": 0}

    def flaky(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        calls["n"] += 1
        if calls["n"] == 2:  # the main file's rename
            raise OSError("disk went away")
        real(src, dst)

    monkeypatch.setattr("privilege_drift.telemetry.io.os.replace", flaky)
    with pytest.raises(OSError, match="disk went away"):
        write_run(run, tmp_path)
    assert not is_complete(tmp_path, "run-0001")
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


def test_the_same_run_writes_identical_bytes(tmp_path: Path) -> None:
    a = write_run(record(STEPS), tmp_path / "a").read_bytes()
    b = write_run(record(STEPS), tmp_path / "b").read_bytes()
    assert a == b


def test_every_line_is_valid_json_with_a_record_type(tmp_path: Path, run: RunTelemetry) -> None:
    import json

    lines = write_run(run, tmp_path).read_text().splitlines()
    kinds = [json.loads(line)["record_type"] for line in lines]
    assert kinds == ["call", "call", "parse_error", "call", "call", "call", "call", "run_summary"]


# --- a fake run end to end -----------------------------------------------------------------


def test_a_fake_agent_run_writes_a_file_that_reloads_into_a_dataframe(tmp_path: Path) -> None:
    llm = ScriptedLLM(["junk", act(S0), act(R0), act(S1), FINAL])
    recorder = TelemetryRecorder(CTX, SCENARIO, window_k=3, clock=Clock())
    agent = ReActAgent(llm, "llama", on_step=recorder.on_step)
    trace = agent.run(
        SCENARIO, seed=42, mediator=NoneMediator(),
        injector=FailureInjector(
            1.0, DrawKey(master_seed=1, cell_idx=0, scenario_id=SCENARIO.id, seed_idx=0)
        ),
        executor=StubExecutor(SCENARIO),
    )  # fmt: skip
    path = write_run(recorder.finish(trace), tmp_path)

    calls = load_calls([path])
    assert list(calls["tool_name"]) == [S0, R0, S1]
    assert list(calls["is_violation"]) == [False, True, False]
    assert list(calls["injected"]) == [True, True, True]
    assert list(calls["retry_since_success"]) == [0, 1, 2]
    assert calls["rolling_503_rate"].tolist() == [0.0, 1.0, 1.0]
    assert calls["reasoning_tokens_cum"].tolist() == [
        10,
        15,
        20,
    ]  # 5 tokens/reply; junk reply first
    assert set(calls["run_id"]) == {"run-0001"}

    summaries = load_summaries([path])
    assert summaries.loc[0, "stop_reason"] == "final_answer"
    assert summaries.loc[0, "parse_errors"] == 1 and summaries.loc[0, "total_calls"] == 3
    assert summaries.loc[0, "task_success"] == False  # noqa: E712  every call was a 503
