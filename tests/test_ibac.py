from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from mediator_contract import MediatorContract
from privilege_drift.data import DataError, load_toolprivbench
from privilege_drift.data.toolprivbench import DEFAULT_PATH
from privilege_drift.llm import ChatMessage, LLMCallError, LLMResult
from privilege_drift.mediators import (
    IbacMediator,
    IbacPolicy,
    Intent,
    IntentClassifier,
    Mediator,
    Taxonomy,
    default_policy,
    default_taxonomy,
    evaluate_classifier,
    load_ibac_policy,
    load_taxonomy,
    parse_intent,
)
from privilege_drift.runner import check_cell, default_mediators
from privilege_drift.schema import ToolCall
from privilege_drift.telemetry import load_calls, load_summaries, run_path
from test_react_agent import SCENARIO, SCENARIOS, ScriptedLLM
from test_runner import IDS, MASTER, AutoLLM, Setup, go, make_grid

TAXONOMY = default_taxonomy()
NAMES = TAXONOMY.names
GOOD = json.dumps({"intent": "business", "confidence": 0.9})


def reply(text: str, model_key: str = "llama") -> LLMResult:
    return LLMResult(
        text=text, tokens_in=1, tokens_out=1, latency_s=0.0, model_key=model_key, model="fake",
        seed=0, finish_reason="stop", raw={},
    )  # fmt: skip


class EndlessLLM:
    """Answers every classification with the same valid JSON."""

    def __init__(self, text: str = GOOD) -> None:
        self.text = text
        self.calls = 0

    def complete(
        self, messages: Sequence[ChatMessage], *, model_key: str, seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:  # fmt: skip
        self.calls += 1
        return reply(self.text, model_key)


def classifier(llm: Any) -> IntentClassifier:
    return IntentClassifier(llm, TAXONOMY)


def ibac(llm: Any = None, policy: IbacPolicy | None = None) -> IbacMediator:
    return IbacMediator(classifier(llm or EndlessLLM()), policy or default_policy(), TAXONOMY)


def policy(**max_tiers: str) -> IbacPolicy:
    levels = {n: {"max_tier": "user"} for n in NAMES} | {
        k: {"max_tier": v} for k, v in max_tiers.items()
    }
    return IbacPolicy.model_validate({"intents": levels, "fallback": {"max_tier": "read_only"}})


class TestIbacMediatorContract(MediatorContract):
    def make(self) -> Mediator:
        return ibac()


# --- taxonomy and policy files -------------------------------------------------------------


def test_the_taxonomy_is_the_eight_toolprivbench_domains() -> None:
    assert len(NAMES) == 8
    fixture_domains = {s.domain.lower() for s in SCENARIOS}
    assert fixture_domains <= set(NAMES)


@pytest.mark.skipif(not DEFAULT_PATH.is_file(), reason="run `make data` first")
def test_the_taxonomy_matches_every_domain_in_the_full_data() -> None:
    assert set(NAMES) == {s.domain.lower() for s in load_toolprivbench(DEFAULT_PATH)}


def test_descriptions_say_nothing_about_permissions() -> None:
    text = " ".join(i.description.lower() for i in TAXONOMY.intents)
    assert not re.search(r"\b(privilege|permission|admin|access)\b", text)  # whole words only


def test_the_shipped_policy_covers_every_intent() -> None:
    p = default_policy()
    assert set(p.intents) == set(NAMES)
    assert {i.max_tier.name for i in p.intents.values()} == {"USER"}
    assert p.fallback.max_tier.name == "READ_ONLY"


@pytest.mark.parametrize(
    ("names", "message"),
    [([], "non-empty"), (["a", "a"], "unique"), (["Business"], "lower case")],
)
def test_a_bad_taxonomy_is_rejected(names: list[str], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Taxonomy.model_validate({"intents": [{"name": n, "description": "d"} for n in names]})


def test_a_bad_policy_is_rejected() -> None:
    with pytest.raises(ValidationError, match="lowest tier"):
        IbacPolicy.model_validate({"intents": {}, "fallback": {"max_tier": "user"}})
    with pytest.raises(ValidationError, match="unknown tier 'root'"):
        policy(business="root")


def test_missing_files_are_data_errors(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="cannot load intents"):
        load_taxonomy(tmp_path / "nope.yaml")
    with pytest.raises(DataError, match="cannot load IBAC policy"):
        load_ibac_policy(tmp_path / "nope.yaml")


def test_a_policy_that_does_not_match_the_taxonomy_is_rejected() -> None:
    short = IbacPolicy.model_validate(
        {"intents": {"business": {"max_tier": "user"}}, "fallback": {"max_tier": "read_only"}}
    )
    with pytest.raises(ValueError, match="different intents"):
        IbacMediator(classifier(EndlessLLM()), short, TAXONOMY)


# --- parsing and the classifier ------------------------------------------------------------


def test_a_clean_reply_is_parsed() -> None:
    assert parse_intent(GOOD, NAMES) == ("business", 0.9)


def test_chatter_fences_case_and_integer_confidence_are_tolerated() -> None:
    text = 'Sure!\n```json\n{"intent": " Healthcare ", "confidence": 1}\n```\nHope that helps.'
    assert parse_intent(text, NAMES) == ("healthcare", 1.0)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "no braces here",
        "{not json",
        '{"intent": "cooking", "confidence": 0.5}',
        '{"intent": "media"}',
        '{"intent": "media", "confidence": 2}',
        '{"intent": "media", "confidence": -0.1}',
        '{"intent": "media", "confidence": "high"}',
        '{"intent": "media", "confidence": true}',
        '{"intent": 5, "confidence": 0.5}',
        '{"confidence": 0.5}',
    ],
)
def test_unusable_replies_give_a_reason_not_an_exception(text: str) -> None:
    assert isinstance(parse_intent(text, NAMES), str)


@given(st.text())
def test_parse_intent_never_raises(text: str) -> None:
    parse_intent(text, NAMES)


def test_a_valid_reply_is_one_call() -> None:
    llm = ScriptedLLM([GOOD])
    result = classifier(llm).classify("Update the manager")
    assert (result.intent, result.confidence, result.failed, result.attempts) == (
        "business", 0.9, False, 1,
    )  # fmt: skip
    assert len(llm.calls) == 1


def test_an_invalid_reply_is_retried_once_with_the_reason() -> None:
    llm = ScriptedLLM(["I think it is business", GOOD])
    result = classifier(llm).classify("Update the manager")
    assert (result.intent, result.failed, result.attempts) == ("business", False, 2)
    retry_prompt = llm.calls[1][0][-1]["content"]
    assert "not valid" in retry_prompt and "no JSON object" in retry_prompt


def test_two_invalid_replies_mean_failure_and_no_third_try() -> None:
    llm = ScriptedLLM(["nope", "still nope"])
    result = classifier(llm).classify("Update the manager")
    assert (result.intent, result.confidence, result.failed, result.attempts) == (
        None, None, True, 2,
    )  # fmt: skip
    assert len(llm.calls) == 2


def test_an_answer_is_remembered_per_task_text() -> None:
    llm = EndlessLLM()
    c = classifier(llm)
    c.classify("task A")
    c.classify("task A")
    assert llm.calls == 1
    c.classify("task B")
    assert llm.calls == 2


def test_a_failure_is_remembered_too_so_a_task_always_gets_the_same_answer() -> None:
    llm = EndlessLLM("garbage")
    c = classifier(llm)
    assert c.classify("t").failed and c.classify("t").failed
    assert llm.calls == 2  # the two attempts of the first classification only


def test_the_classifier_sees_only_the_task_and_the_categories() -> None:
    llm = ScriptedLLM([GOOD])
    classifier(llm).classify(SCENARIO.user_task)
    messages, meta = llm.calls[0]
    text = " ".join(m["content"] for m in messages)
    assert SCENARIO.user_task in text
    assert not any(t.name in text or t.description in text for t in SCENARIO.tools)
    assert not any(w in text.lower() for w in ("tier", "privilege", "tool"))
    assert all(n in text for n in NAMES)
    assert meta == {"model_key": "llama", "seed": 0, "stop": None}


def test_service_errors_propagate_and_are_not_remembered() -> None:
    class Flaky:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages: Any, *, model_key: str, **kw: Any) -> LLMResult:
            self.calls += 1
            if self.calls == 1:
                raise LLMCallError("down", model_key=model_key, model="fake")
            return reply(GOOD, model_key)

    c = classifier(Flaky())
    with pytest.raises(LLMCallError):
        c.classify("t")
    assert c.classify("t").intent == "business"  # the next attempt starts afresh


def test_evaluation_counts_right_wrong_and_failed_answers() -> None:
    llm = ScriptedLLM(
        [json.dumps({"intent": s, "confidence": 0.8}) for s in ("business", "media")] + ["x", "y"]
    )
    report = evaluate_classifier(classifier(llm), list(SCENARIOS))  # business, business, healthcare
    assert (report.total, report.correct, report.failed) == (3, 1, 1)
    assert report.accuracy == pytest.approx(1 / 3)
    assert report.confusions == {"business -> media": 1, "healthcare -> (failed)": 1}


# --- the mediator --------------------------------------------------------------------------


def verdicts(mediator: IbacMediator) -> list[bool]:
    mediator.start_run(SCENARIO)
    return [mediator.gate(ToolCall(name=t.name), None).allow for t in SCENARIO.tools]


def test_the_shipped_policy_allows_standard_tools_and_blocks_risk_tools() -> None:
    assert verdicts(ibac()) == [True, True, True, False, False, False]


def test_reasons_name_the_intent_and_confidence() -> None:
    m = ibac()
    m.start_run(SCENARIO)
    assert m.gate(ToolCall(name=SCENARIO.tools[0].name), None).reason == (
        "IBAC: intent business (confidence 0.90) allows tier user"
    )
    assert m.gate(ToolCall(name=SCENARIO.tools[3].name), None).reason == (
        "IBAC: intent business (confidence 0.90) does not allow tier admin"
    )


def test_the_intent_decides_which_tiers_are_allowed() -> None:
    p = policy(business="admin", media="read_only")
    assert verdicts(ibac(EndlessLLM(GOOD), p)) == [True] * 6  # business may use admin tools
    media = json.dumps({"intent": "media", "confidence": 0.7})
    assert verdicts(ibac(EndlessLLM(media), p)) == [False] * 6  # media may use read_only only


def test_a_failed_classification_applies_the_most_restrictive_policy() -> None:
    m = ibac(EndlessLLM("garbage"))
    assert verdicts(m) == [False] * 6
    assert m.classification is not None and m.classification.failed
    reason = m.gate(ToolCall(name=SCENARIO.tools[0].name), None).reason
    assert "classifier_failed" in reason and "does not allow tier user" in reason


def test_each_run_is_classified_afresh() -> None:
    answers = {
        SCENARIOS[0].user_task: "business",
        SCENARIOS[2].user_task: "healthcare",
    }

    class ByTask:
        def complete(self, messages: Any, *, model_key: str, **kw: Any) -> LLMResult:
            task = messages[-1]["content"].removeprefix("Request: ")
            return reply(json.dumps({"intent": answers[task], "confidence": 0.5}), model_key)

    m = ibac(ByTask())
    m.start_run(SCENARIOS[0])
    assert m.classification is not None and m.classification.intent == "business"
    m.start_run(SCENARIOS[2])
    assert m.classification.intent == "healthcare"


def test_the_gate_ignores_an_intent_passed_in() -> None:
    m = ibac()
    m.start_run(SCENARIO)
    risky = ToolCall(name=SCENARIO.tools[3].name)
    assert {m.gate(risky, i).allow for i in (None, Intent("business"), Intent("coding"))} == {False}


def test_guard_cases() -> None:
    m = ibac()
    assert m.gate(ToolCall(name="x"), None).reason == "IBAC: no run started"
    m.start_run(SCENARIO)
    unknown = m.gate(ToolCall(name="not_offered"), None)
    assert unknown.allow is False and "no label" in unknown.reason


def test_a_service_error_in_start_run_propagates() -> None:
    class Down:
        def complete(self, messages: Any, *, model_key: str, **kw: Any) -> LLMResult:
            raise LLMCallError("down", model_key=model_key, model="fake")

    with pytest.raises(LLMCallError):
        ibac(Down()).start_run(SCENARIO)


# --- in the runner -------------------------------------------------------------------------


def test_the_registry_has_all_three_arms_and_shares_one_classifier() -> None:
    llm = EndlessLLM()
    factories = default_mediators(llm)
    assert set(factories) == {"none", "mac", "ibac"}
    first, second = factories["ibac"](), factories["ibac"]()
    assert isinstance(first, IbacMediator) and first is not second
    first.start_run(SCENARIO)
    second.start_run(SCENARIO)
    assert llm.calls == 1  # the second run reused the first answer


class ClassifyingAutoLLM(AutoLLM):
    """Plays the agent (as AutoLLM does) and answers classification requests."""

    def __init__(self, classifier_reply: str | None = None) -> None:
        super().__init__()
        self.classifier_reply = classifier_reply
        self.classifier_calls = 0

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        if messages[0]["content"].startswith("Classify the user's request"):
            self.classifier_calls += 1
            if self.classifier_reply is not None:
                return reply(self.classifier_reply, model_key)
            task = messages[1]["content"].removeprefix("Request: ")
            domain = next(s.domain.lower() for s in SCENARIOS if s.user_task == task)
            return reply(json.dumps({"intent": domain, "confidence": 0.9}), model_key)
        return super().complete(messages, model_key=model_key, seed=seed, stop=stop)


def ibac_cell(tmp_path: Path) -> Setup:
    return Setup(make_grid(tmp_path, mediators=("ibac",)), cell_idx=1)


def test_an_ibac_cell_runs_logs_the_classification_and_passes_the_checks(tmp_path: Path) -> None:
    setup = ibac_cell(tmp_path)
    llm = ClassifyingAutoLLM()
    report = go(setup, llm)
    assert report.status.value == "complete"
    assert llm.classifier_calls == len(IDS)  # once per task, not once per run (2 seeds each)
    paths = [run_path(setup.directory, i.run_id) for i in setup.items]
    calls = load_calls(paths)
    by_id = {s.id: s.domain.lower() for s in SCENARIOS}
    assert [by_id[s] for s in calls["scenario_id"]] == list(calls["classifier_intent"])
    assert set(calls["classifier_conf"]) == {0.9}
    summaries = load_summaries(paths)
    assert not summaries["classifier_failed"].any()
    assert check_cell(
        setup.cell, setup.items, setup.directory, {s.id: s for s in SCENARIOS}, MASTER
    ).ok


def test_when_classification_fails_every_call_is_blocked_and_the_failure_is_logged(
    tmp_path: Path,
) -> None:
    setup = ibac_cell(tmp_path)
    go(setup, ClassifyingAutoLLM(classifier_reply="I cannot say"))
    paths = [run_path(setup.directory, i.run_id) for i in setup.items]
    calls = load_calls(paths)
    assert not calls["allowed"].any()
    assert calls["classifier_intent"].isna().all()
    summaries = load_summaries(paths)
    assert summaries["classifier_failed"].all() and not summaries["task_success"].any()
