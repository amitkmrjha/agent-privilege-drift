"""The text-format ReAct loop used for every model (decision D06).

One step: ask the model, parse the reply, then for an action send the call through

    mediator gate -> failure injector -> tool executor        (decision D03)

and show the agent the result as an ``Observation:``. A blocked call never reaches the injector,
so it gets no failure draw. The harness never retries on its own (D07): if a tool fails, what the
agent does next is the thing being measured.

Errors from the model service (timeouts, connection errors) are *not* caught here. They say
nothing about the agent's behaviour, so they propagate and the batch runner decides whether to
retry the run.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from typing import Protocol

from privilege_drift.agent.parser import (
    ParsedAction,
    ParsedFinal,
    ParsedStep,
    ParseFailure,
    parse_step,
)
from privilege_drift.agent.prompt import correction_message, initial_messages, observation_message
from privilege_drift.agent.trace import (
    LLMCallInfo,
    Outcome,
    RunTrace,
    StepRecord,
    StopReason,
)
from privilege_drift.data.stubs import ToolExecutor
from privilege_drift.llm import ChatMessage, LLMResult
from privilege_drift.mediators.base import Intent, Mediator, blocked_result
from privilege_drift.schema import Scenario, ToolCall, ToolResult

STOP_SEQUENCES = ("Observation:",)
DEFAULT_MAX_STEPS = 15  # decision D07: suggested, to be confirmed by the pilot and pre-registered
_OBSERVATION_MARKER = "Observation:"

Execute = Callable[[ToolCall], ToolResult]
Injector = Callable[[ToolCall, Execute], ToolResult]
StepObserver = Callable[[StepRecord], None]


class Completer(Protocol):
    """What the agent needs from a model client (``LLMClient`` satisfies it)."""

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult: ...


def _call_info(result: LLMResult) -> LLMCallInfo:
    return LLMCallInfo(
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        latency_s=result.latency_s,
        finish_reason=result.finish_reason,
        cached=result.cached,
        possible_truncation=result.possible_truncation,
        model_fingerprint=result.model_fingerprint,
    )


class ReActAgent:
    """Runs one scenario to completion and returns the full trace.

    ``on_step`` is called with every ``StepRecord`` as it happens (the hook the telemetry writer
    uses), so a run that crashes midway still leaves its earlier steps recorded.
    """

    def __init__(
        self,
        llm: Completer,
        model_key: str,
        *,
        max_steps: int = DEFAULT_MAX_STEPS,
        on_step: StepObserver | None = None,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self._llm = llm
        self._model_key = model_key
        self._max_steps = max_steps
        self._on_step = on_step

    def run(
        self,
        scenario: Scenario,
        *,
        seed: int | None,
        mediator: Mediator,
        injector: Injector,
        executor: ToolExecutor,
        intent: Intent | None = None,
    ) -> RunTrace:
        mediator.start_run(scenario)
        tool_names = {t.name for t in scenario.tools}
        messages = initial_messages(scenario)
        steps: list[StepRecord] = []

        def finish(reason: StopReason, answer: str | None = None) -> RunTrace:
            return RunTrace(
                scenario_id=scenario.id,
                model_key=self._model_key,
                seed=seed,
                max_steps=self._max_steps,
                steps=tuple(steps),
                stop_reason=reason,
                final_answer=answer,
            )

        def record(item: StepRecord) -> None:
            steps.append(item)
            if self._on_step is not None:
                self._on_step(item)

        for step in range(1, self._max_steps + 1):
            reply, parsed = self._ask(messages, tool_names, seed)
            attempt = 0
            if isinstance(parsed, ParseFailure):
                record(self._parse_error(step, attempt, reply, parsed))
                messages += [
                    {"role": "assistant", "content": _before_observation(reply.text)},
                    correction_message(parsed, tool_names),
                ]
                reply, parsed = self._ask(messages, tool_names, seed)
                attempt = 1
                if isinstance(parsed, ParseFailure):
                    record(self._parse_error(step, attempt, reply, parsed))
                    return finish(StopReason.FORMAT_ERROR)

            if isinstance(parsed, ParsedFinal):
                record(
                    StepRecord(
                        step=step,
                        attempt=attempt,
                        outcome=Outcome.FINAL_ANSWER,
                        llm_text=reply.text,
                        llm=_call_info(reply),
                        thought=parsed.thought,
                    )
                )
                return finish(StopReason.FINAL_ANSWER, parsed.answer)

            assert isinstance(parsed, ParsedAction)
            call = ToolCall(name=parsed.tool, arguments=parsed.arguments)
            decision = mediator.gate(call, intent)
            result = injector(call, executor.execute) if decision.allow else blocked_result()
            record(
                StepRecord(
                    step=step,
                    attempt=attempt,
                    outcome=Outcome.ACTION,
                    llm_text=reply.text,
                    llm=_call_info(reply),
                    thought=parsed.thought,
                    proposed_call=call,
                    decision=decision,
                    result=result,
                )
            )
            messages += [
                {"role": "assistant", "content": _before_observation(reply.text)},
                observation_message(result.body),
            ]
        return finish(StopReason.MAX_STEPS)

    def _ask(
        self, messages: Sequence[ChatMessage], tool_names: Collection[str], seed: int | None
    ) -> tuple[LLMResult, ParsedStep]:
        reply = self._llm.complete(
            messages, model_key=self._model_key, seed=seed, stop=STOP_SEQUENCES
        )
        return reply, parse_step(_before_observation(reply.text), tool_names)

    @staticmethod
    def _parse_error(
        step: int, attempt: int, reply: LLMResult, failure: ParseFailure
    ) -> StepRecord:
        return StepRecord(
            step=step,
            attempt=attempt,
            outcome=Outcome.PARSE_ERROR,
            llm_text=reply.text,
            llm=_call_info(reply),
            thought=failure.thought,
            parse_failure=failure,
        )


def _before_observation(text: str) -> str:
    """Drop anything after ``Observation:``. Providers honour the stop sequence, but a model that
    writes its own observation must never have it treated as a real tool result."""
    return text.split(_OBSERVATION_MARKER, 1)[0].rstrip()
