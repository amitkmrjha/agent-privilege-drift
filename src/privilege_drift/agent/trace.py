"""What a run records. One ``StepRecord`` per model call; the telemetry issue (#18) builds on it."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from privilege_drift.agent.parser import ParseFailure
from privilege_drift.schema import Decision, ToolCall, ToolResult


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StopReason(StrEnum):
    FINAL_ANSWER = "final_answer"
    MAX_STEPS = "max_steps"
    FORMAT_ERROR = "format_error"  # a reply stayed unreadable after the one correction


class Outcome(StrEnum):
    ACTION = "action"
    FINAL_ANSWER = "final_answer"
    PARSE_ERROR = "parse_error"


class LLMCallInfo(_Frozen):
    tokens_in: int
    tokens_out: int
    latency_s: float
    finish_reason: str | None
    cached: bool
    possible_truncation: bool
    model_fingerprint: str | None


class StepRecord(_Frozen):
    """One model call and what came of it.

    ``step`` counts action and final steps from 1. ``attempt`` is 0 for the first reply and 1
    for the single correction re-prompt after a malformed one, so both share a ``step``.
    ``proposed_call`` is what the model chose (before the gate); ``decision`` is the mediator's
    verdict; ``result`` is what the agent saw next (the tool's answer, a 503 or the block text).
    """

    step: int
    attempt: int
    outcome: Outcome
    llm_text: str
    llm: LLMCallInfo
    thought: str
    parse_failure: ParseFailure | None = None
    proposed_call: ToolCall | None = None
    decision: Decision | None = None
    result: ToolResult | None = None


class RunTrace(_Frozen):
    scenario_id: str
    model_key: str
    seed: int | None
    max_steps: int
    steps: tuple[StepRecord, ...]
    stop_reason: StopReason
    final_answer: str | None = None

    @property
    def proposed_calls(self) -> tuple[ToolCall, ...]:
        return tuple(s.proposed_call for s in self.steps if s.proposed_call is not None)
