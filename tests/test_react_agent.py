from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from privilege_drift.agent import (
    STOP_SEQUENCES,
    FailureKind,
    Outcome,
    ReActAgent,
    RunTrace,
    StepRecord,
    StopReason,
    build_system_prompt,
    ordered_tools,
)
from privilege_drift.data import StubExecutor, load_toolprivbench
from privilege_drift.failure import FIXED_503_BODY, DrawKey, FailureInjector
from privilege_drift.llm import ChatMessage, LLMCallError, LLMResult
from privilege_drift.mediators import BLOCK_MESSAGE, Intent, NoneMediator
from privilege_drift.schema import Decision, Scenario, Tier, ToolCall, ToolResult

FIXTURE = Path(__file__).parent / "fixtures" / "toolprivbench_sample.jsonl"
SCENARIOS = load_toolprivbench(FIXTURE)
SCENARIO = SCENARIOS[0]
SAFE = SCENARIO.tools[0]  # a standard tool
RISKY = SCENARIO.tools[3]  # a risk tool
SEED = 123


def act(tool: str, args: str = "{}") -> str:
    return f"Thought: do it\nAction: {tool}\nAction Input: {args}"


FINAL = "Thought: done\nFinal Answer: Finished the task."


class ScriptedLLM:
    """Replays canned replies and records exactly what the agent sent."""

    def __init__(self, replies: Sequence[str]) -> None:
        self._replies = list(replies)
        self.calls: list[tuple[list[ChatMessage], dict[str, object]]] = []

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        self.calls.append((list(messages), {"model_key": model_key, "seed": seed, "stop": stop}))
        assert self._replies, "the agent asked for more replies than the script has"
        return LLMResult(
            text=self._replies.pop(0),
            tokens_in=10,
            tokens_out=5,
            latency_s=0.01,
            model_key=model_key,
            model="fake",
            seed=seed,
            finish_reason="stop",
            raw={},
        )


class RecordingMediator:
    """Blocks the named tools and remembers how it was driven."""

    def __init__(self, block: Sequence[str] = ()) -> None:
        self.block = set(block)
        self.starts: list[str] = []
        self.gated: list[str] = []

    def start_run(self, scenario: Scenario) -> None:
        self.starts.append(scenario.id)

    def gate(self, call: ToolCall, intent: Intent | None) -> Decision:
        self.gated.append(call.name)
        if call.name in self.block:
            return Decision(allow=False, reason="test block")
        return Decision(allow=True, reason="test allow")


def injector(p: float = 0.0) -> FailureInjector:
    return FailureInjector(
        p, DrawKey(master_seed=1, cell_idx=0, scenario_id=SCENARIO.id, seed_idx=0)
    )


def run(
    replies: Sequence[str],
    *,
    mediator: RecordingMediator | NoneMediator | None = None,
    inj: FailureInjector | None = None,
    max_steps: int = 15,
    on_step: list[StepRecord] | None = None,
) -> tuple[RunTrace, ScriptedLLM]:
    llm = ScriptedLLM(replies)
    agent = ReActAgent(
        llm, "llama", max_steps=max_steps, on_step=on_step.append if on_step is not None else None
    )
    trace = agent.run(
        SCENARIO,
        seed=SEED,
        mediator=mediator or NoneMediator(),
        injector=inj or injector(),
        executor=StubExecutor(SCENARIO),
    )
    return trace, llm


# --- normal runs ---------------------------------------------------------------------------


def test_normal_run_acts_observes_then_finishes() -> None:
    trace, llm = run([act(SAFE.name), FINAL])
    assert trace.stop_reason is StopReason.FINAL_ANSWER
    assert trace.final_answer == "Finished the task."
    assert [s.outcome for s in trace.steps] == [Outcome.ACTION, Outcome.FINAL_ANSWER]
    first = trace.steps[0]
    assert first.proposed_call == ToolCall(name=SAFE.name)
    assert first.result == ToolResult(http_code=200, body=SAFE.success_output or "")
    assert trace.proposed_calls == (ToolCall(name=SAFE.name),)
    # the second model call saw the observation
    second_call_messages = llm.calls[1][0]
    assert second_call_messages[-1] == {
        "role": "user",
        "content": f"Observation: {SAFE.success_output}",
    }


def test_every_model_call_uses_the_stop_sequence_model_key_and_seed() -> None:
    _, llm = run([act(SAFE.name), FINAL])
    assert all(
        meta == {"model_key": "llama", "seed": SEED, "stop": STOP_SEQUENCES}
        for _, meta in llm.calls
    )


def test_the_agent_stops_at_the_first_final_answer() -> None:
    trace, llm = run([FINAL])
    assert len(llm.calls) == 1 and trace.steps[0].step == 1


# --- failures and the one correction -------------------------------------------------------


def test_a_malformed_reply_gets_one_correction_then_continues() -> None:
    trace, llm = run(["I will just do it.", act(SAFE.name), FINAL])
    assert [(s.step, s.attempt, s.outcome) for s in trace.steps] == [
        (1, 0, Outcome.PARSE_ERROR),
        (1, 1, Outcome.ACTION),
        (2, 0, Outcome.FINAL_ANSWER),
    ]
    assert trace.steps[0].parse_failure is not None
    assert trace.steps[0].parse_failure.kind is FailureKind.NO_ACTION
    correction = llm.calls[1][0][-1]
    assert correction["role"] == "user" and "could not be read" in correction["content"]
    assert trace.stop_reason is StopReason.FINAL_ANSWER


def test_two_unreadable_replies_in_a_row_end_the_run() -> None:
    trace, llm = run(["nonsense", "more nonsense"])
    assert trace.stop_reason is StopReason.FORMAT_ERROR
    assert len(llm.calls) == 2  # original plus exactly one correction
    assert [s.outcome for s in trace.steps] == [Outcome.PARSE_ERROR, Outcome.PARSE_ERROR]
    assert trace.final_answer is None


def test_an_unknown_tool_is_a_parse_error_and_never_reaches_the_gate() -> None:
    mediator = RecordingMediator()
    trace, _ = run([act("delete_everything"), act(SAFE.name), FINAL], mediator=mediator)
    assert trace.steps[0].parse_failure is not None
    assert trace.steps[0].parse_failure.kind is FailureKind.UNKNOWN_TOOL
    assert mediator.gated == [SAFE.name]


def test_max_steps_ends_a_run_that_never_finishes() -> None:
    mediator = RecordingMediator()
    trace, llm = run([act(SAFE.name)] * 3, mediator=mediator, max_steps=3)
    assert trace.stop_reason is StopReason.MAX_STEPS
    assert len(llm.calls) == 3 and len(trace.steps) == 3
    assert mediator.gated == [SAFE.name] * 3
    assert trace.final_answer is None


def test_a_correction_does_not_use_up_an_extra_step() -> None:
    trace, _ = run(["junk", act(SAFE.name), act(SAFE.name)], max_steps=2)
    assert trace.stop_reason is StopReason.MAX_STEPS
    assert [s.step for s in trace.steps] == [1, 1, 2]


# --- the gate, the injector and their order (D03) ------------------------------------------


def test_a_failed_call_is_shown_as_the_fixed_503_and_the_agent_may_retry() -> None:
    inj = injector(1.0)
    trace, llm = run([act(SAFE.name), act(SAFE.name), FINAL], inj=inj)
    first, second = trace.steps[0], trace.steps[1]
    assert first.result == ToolResult(http_code=503, body=FIXED_503_BODY, injected=True)
    assert second.proposed_call == first.proposed_call  # the agent chose to retry; we did not
    assert llm.calls[1][0][-1]["content"] == f"Observation: {FIXED_503_BODY}"
    assert inj.calls_seen == 2


def test_a_blocked_call_shows_the_block_text_and_gets_no_failure_draw() -> None:
    inj = injector(1.0)
    mediator = RecordingMediator(block=[RISKY.name])
    trace, llm = run([act(RISKY.name), FINAL], mediator=mediator, inj=inj)
    step = trace.steps[0]
    assert step.proposed_call == ToolCall(name=RISKY.name)  # the proposal is still recorded
    assert step.decision == Decision(allow=False, reason="test block")
    assert step.result is not None and step.result.body == BLOCK_MESSAGE
    assert step.result.injected is False
    assert inj.calls_seen == 0  # D03: a blocked call never reaches the injector
    assert llm.calls[1][0][-1]["content"] == f"Observation: {BLOCK_MESSAGE}"


def test_the_mediator_is_started_once_before_the_first_gate() -> None:
    mediator = RecordingMediator()
    run([act(SAFE.name), act(RISKY.name), FINAL], mediator=mediator)
    assert mediator.starts == [SCENARIO.id]
    assert mediator.gated == [SAFE.name, RISKY.name]


# --- hooks, errors, hallucinated observations ----------------------------------------------


def test_the_observer_sees_every_step_in_order() -> None:
    seen: list[StepRecord] = []
    trace, _ = run(["junk", act(SAFE.name), FINAL], on_step=seen)
    assert tuple(seen) == trace.steps


def test_model_service_errors_propagate_instead_of_being_recorded_as_behaviour() -> None:
    class Broken:
        def complete(self, *a: object, **k: object) -> LLMResult:
            raise LLMCallError("boom", model_key="llama", model="x")

    agent = ReActAgent(Broken(), "llama")
    with pytest.raises(LLMCallError):
        agent.run(
            SCENARIO,
            seed=1,
            mediator=NoneMediator(),
            injector=injector(),
            executor=StubExecutor(SCENARIO),
        )


def test_an_observation_the_model_invented_is_not_used() -> None:
    reply = f"{act(SAFE.name)}\nObservation: it all worked\nFinal Answer: done already"
    trace, llm = run([reply, FINAL])
    assert trace.steps[0].outcome is Outcome.ACTION  # not mistaken for a final answer
    assistant = llm.calls[1][0][-2]
    assert assistant["role"] == "assistant" and "it all worked" not in assistant["content"]


def test_max_steps_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_steps"):
        ReActAgent(ScriptedLLM([]), "llama", max_steps=0)


# --- the prompt ----------------------------------------------------------------------------


def test_prompt_lists_every_tool_and_shows_no_tier() -> None:
    prompt = build_system_prompt(SCENARIO)
    assert all(t.name in prompt and t.description in prompt for t in SCENARIO.tools)
    assert "tier" not in prompt.lower() and "privilege" not in prompt.lower()


def test_prompt_does_not_depend_on_the_tiers() -> None:
    flipped = SCENARIO.model_copy(
        update={
            "tools": tuple(t.model_copy(update={"tier": Tier.READ_ONLY}) for t in SCENARIO.tools)
        }
    )
    assert build_system_prompt(flipped) == build_system_prompt(SCENARIO)


def test_tool_order_is_fixed_complete_and_not_standard_first() -> None:
    for scenario in SCENARIOS:
        order = ordered_tools(scenario)
        assert order == ordered_tools(scenario)
        assert sorted(t.name for t in order) == sorted(t.name for t in scenario.tools)
    # file order is "three standard, then three risk"; the agent must not see that order
    assert any(ordered_tools(s) != s.tools for s in SCENARIOS)
    assert any([t.tier for t in ordered_tools(s)] != [t.tier for t in s.tools] for s in SCENARIOS)


def test_parameter_schemas_are_shown_when_the_benchmark_has_them() -> None:
    with_params = next(s for s in SCENARIOS if any(t.params for t in s.tools))
    assert "Parameters:" in build_system_prompt(with_params)
    assert "Parameters:" not in build_system_prompt(SCENARIO)


def test_an_escalation_followed_by_an_imagined_conversation_is_still_recorded() -> None:
    """Found with real Llama: after a valid Action it wrote '### User:' and its own Final Answer."""
    imagined = "\n\n### User:\nthe tool worked\n\n### Assistant:\nFinal Answer: all done already"
    trace, llm = run([act(RISKY.name) + imagined, FINAL])
    first = trace.steps[0]
    assert first.outcome is Outcome.ACTION  # not discarded as ambiguous
    assert first.proposed_call == ToolCall(name=RISKY.name)
    assert first.llm_text.endswith("all done already")  # the raw reply is kept for the audit
    kept = llm.calls[1][0][-2]
    assert kept["role"] == "assistant" and "### User" not in kept["content"]
    assert "all done" not in kept["content"]  # the model never sees its own invention again
