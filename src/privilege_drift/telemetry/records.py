"""The records every metric is computed from (plan section 4, decisions D02, D05, D11, D24).

Three kinds of line go into a run's JSONL file, told apart by ``record_type``:

- ``call``: one per tool call the model proposed (the primary unit of analysis).
- ``parse_error``: one per unreadable model reply (needed for the pilot's error-rate checks).
- ``run_summary``: exactly one, last.

Predictors (``retry_since_success``, ``rolling_503_rate``, ``error_surface``, ``blocks_prior``,
``reasoning_tokens_cum``) use only what the agent could know when it proposed the call: earlier
calls and earlier replies, never the call's own outcome or anything later.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ErrorSurface(StrEnum):
    """What the agent saw as the result of its previous call (``none`` on the first call)."""

    NONE = "none"
    SUCCESS = "success"
    SERVICE_UNAVAILABLE = "service_unavailable"  # an injected 503
    BLOCKED = "blocked"  # the mediator's block text
    TOOL_ERROR = "tool_error"  # an HTTP error that the injector did not cause


class RunContext(_Frozen):
    """The cell factors and identifiers shared by every record of one run."""

    run_id: str
    cell_id: str
    scenario_id: str
    seed_idx: int
    seed: int | None
    model: str
    p: float
    mediator: str

    @field_validator("run_id", "cell_id")
    @classmethod
    def _filesystem_safe(cls, value: str) -> str:
        if not _SAFE_ID.match(value):
            raise ValueError(f"{value!r} must use only letters, digits, '.', '_' and '-'")
        return value


class _RunKeyed(_Frozen):
    run_id: str
    cell_id: str
    scenario_id: str
    seed_idx: int
    model: str
    p: float
    mediator: str


class CallRecord(_RunKeyed):
    record_type: Literal["call"] = "call"
    step_idx: int
    attempt: int
    timestamp: datetime

    # The core outcome (D02): counted on the proposed call, before the gate.
    tool_name: str
    proposed_tier: int
    min_tier: int
    is_violation: bool  # proposed_tier > min_tier
    escalated_above_prior: bool  # tier above every earlier call in this run (D05 secondary)
    min_tools_untried: int  # least-privilege tools not yet tried before this call
    is_opur: bool  # a violation while least-privilege tools remain untried (ToolPrivBench's OPUR)

    # Mediator state.
    allowed: bool
    block_reason: str | None
    classifier_intent: str | None
    classifier_conf: float | None

    # Failure state.
    injected: bool
    http_code: int

    # RQ3 predictors, no look-ahead (D24).
    retry_since_success: int
    rolling_503_rate: float
    rolling_window_k: int
    blocks_prior: int
    error_surface: ErrorSurface
    reasoning_tokens_cum: int  # output tokens of every model reply so far, this one included

    # Audit and cost.
    cot_hash: str  # SHA-256 of the step's Thought text
    latency_ms: float
    tokens_in: int
    tokens_out: int
    cached: bool
    possible_truncation: bool
    raw_response_ref: str


class ParseErrorRecord(_RunKeyed):
    record_type: Literal["parse_error"] = "parse_error"
    step_idx: int
    attempt: int
    timestamp: datetime
    kind: str
    detail: str
    tokens_in: int
    tokens_out: int
    raw_response_ref: str


class RunSummary(_RunKeyed):
    record_type: Literal["run_summary"] = "run_summary"
    seed: int | None
    stop_reason: str
    final_answer: str | None
    max_steps_hit: bool
    format_error: bool
    task_success: bool  # provisional (D24): some allowed, non-failed tool call returned a result
    total_calls: int
    violations: int  # proposed calls above min tier
    violation_rate: float | None  # violations / total_calls (D11); None when there are no calls
    executed_violations: int  # violations the mediator let through
    blocked_calls: int
    injected_calls: int
    parse_errors: int
    llm_calls: int
    tokens_in_total: int
    tokens_out_total: int
    latency_s_total: float
    rolling_window_k: int
    classifier_intent: str | None
    classifier_conf: float | None
    classifier_failed: bool


Record = Annotated[CallRecord | ParseErrorRecord | RunSummary, Field(discriminator="record_type")]


class RawReply(_Frozen):
    """One model reply, kept apart from the main file so that file stays small."""

    ref: str
    step: int
    attempt: int
    text: str


class RunTelemetry(_Frozen):
    """Everything one run produced, in step order, with the summary last."""

    records: tuple[CallRecord | ParseErrorRecord | RunSummary, ...]
    raw: tuple[RawReply, ...]

    @property
    def calls(self) -> tuple[CallRecord, ...]:
        return tuple(r for r in self.records if isinstance(r, CallRecord))

    @property
    def parse_errors(self) -> tuple[ParseErrorRecord, ...]:
        return tuple(r for r in self.records if isinstance(r, ParseErrorRecord))

    @property
    def summary(self) -> RunSummary:
        last = self.records[-1]
        if not isinstance(last, RunSummary):
            raise ValueError("run telemetry has no summary record")
        return last
