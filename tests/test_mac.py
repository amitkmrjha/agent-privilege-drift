from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mediator_contract import MediatorContract, scenarios
from privilege_drift.agent import Outcome, ReActAgent
from privilege_drift.data import DataError, StubExecutor
from privilege_drift.failure import DrawKey, FailureInjector
from privilege_drift.mediators import (
    BLOCK_MESSAGE,
    Intent,
    MacMatrix,
    MacMediator,
    Mediator,
    default_matrix,
    load_mac_matrix,
)
from privilege_drift.runner import default_mediators
from privilege_drift.schema import Scenario, Source, Tier, Tool, ToolCall
from privilege_drift.telemetry import RunContext, TelemetryRecorder
from test_react_agent import FINAL, SCENARIO, ScriptedLLM, act

MATRIX = default_matrix()


class TestMacMediatorContract(MediatorContract):
    def make(self) -> Mediator:
        return MacMediator(MATRIX)


def three_tier_scenario(scenario_id: str = "S-1") -> Scenario:
    tools = tuple(
        Tool(name=name, description="d", tier=tier)
        for name, tier in (("read", Tier.READ_ONLY), ("write", Tier.USER), ("root", Tier.ADMIN))
    )
    return Scenario(
        id=scenario_id, source=Source.TOOLPRIVBENCH, domain="d", category="c", title="t",
        user_task="do it", tools=tools, min_tools=("read",), min_tier=Tier.READ_ONLY,
    )  # fmt: skip


def matrix(**over: object) -> MacMatrix:
    fields: dict[str, object] = {
        "default_role": "user_role",
        "roles": {
            "user_role": {"allow_tiers": ["read_only", "user"]},
            "viewer": {"allow_tiers": ["read_only"]},
            "boss": {"allow_tiers": ["read_only", "user", "admin"]},
            "nobody": {"allow_tiers": []},
        },
    }
    fields.update(over)
    return MacMatrix.model_validate(fields)


def verdicts(mediator: MacMediator, scenario: Scenario) -> dict[str, bool]:
    mediator.start_run(scenario)
    return {t.name: mediator.gate(ToolCall(name=t.name), None).allow for t in scenario.tools}


# --- blocks and allows exactly as the matrix says -----------------------------------------


def test_the_shipped_matrix_allows_standard_tools_and_blocks_risk_tools() -> None:
    mediator = MacMediator(MATRIX)
    for scenario in scenarios():
        for tool, allowed in zip(
            scenario.tools, verdicts(mediator, scenario).values(), strict=True
        ):
            assert allowed is (tool.tier is Tier.USER), (scenario.id, tool.name)


def test_every_role_gets_exactly_the_tiers_it_lists() -> None:
    scenario = three_tier_scenario()
    expected = {
        "user_role": {"read": True, "write": True, "root": False},
        "viewer": {"read": True, "write": False, "root": False},
        "boss": {"read": True, "write": True, "root": True},
        "nobody": {"read": False, "write": False, "root": False},
    }
    for role, want in expected.items():
        m = matrix(default_role=role)
        assert verdicts(MacMediator(m), scenario) == want, role


def test_scenario_roles_override_the_default_for_that_scenario_only() -> None:
    m = matrix(scenario_roles={"S-2": "boss"})
    mediator = MacMediator(m)
    assert verdicts(mediator, three_tier_scenario("S-1"))["root"] is False
    assert verdicts(mediator, three_tier_scenario("S-2"))["root"] is True
    assert verdicts(mediator, three_tier_scenario("S-1"))["root"] is False  # no carry-over


def test_the_decision_ignores_the_task_and_the_intent() -> None:
    mediator = MacMediator(MATRIX)
    mediator.start_run(SCENARIO)
    risky = ToolCall(name=SCENARIO.tools[3].name)
    labels = [None, Intent("read_data"), Intent("update_record"), Intent("administer_system")]
    assert {mediator.gate(risky, i).allow for i in labels} == {False}


def test_reasons_say_which_role_and_tier() -> None:
    mediator = MacMediator(MATRIX)
    mediator.start_run(SCENARIO)
    assert mediator.gate(ToolCall(name=SCENARIO.tools[0].name), None).reason == (
        "MAC: role standard_user may use tier user"
    )
    assert mediator.gate(ToolCall(name=SCENARIO.tools[3].name), None).reason == (
        "MAC: role standard_user may not use tier admin"
    )


def test_an_unlabelled_tool_is_denied_and_a_call_before_start_run_is_denied() -> None:
    mediator = MacMediator(MATRIX)
    assert mediator.gate(ToolCall(name="x"), None).reason == "MAC: no run started"
    mediator.start_run(SCENARIO)
    unknown = mediator.gate(ToolCall(name="not_offered"), None)
    assert unknown.allow is False and "no label" in unknown.reason


# --- the matrix file -----------------------------------------------------------------------


def test_the_shipped_matrix_loads() -> None:
    assert MATRIX.default_role == "standard_user"
    assert MATRIX.roles["standard_user"].allow_tiers == {Tier.READ_ONLY, Tier.USER}
    assert MATRIX.scenario_roles == {}
    assert load_mac_matrix() == MATRIX


@pytest.mark.parametrize(
    ("over", "message"),
    [
        ({"default_role": "ghost"}, "default_role"),
        ({"scenario_roles": {"S-1": "ghost"}}, "undefined roles"),
        ({"roles": {"user_role": {"allow_tiers": ["root"]}}}, "unknown tier 'root'"),
        ({"roles": {"user_role": {"allow_tiers": ["user"], "extra": 1}}}, "extra"),
    ],
)
def test_a_bad_matrix_is_rejected(over: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        matrix(**over)


def test_a_missing_matrix_file_is_a_data_error(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="cannot load MAC matrix"):
        load_mac_matrix(tmp_path / "nope.yaml")


# --- in the harness ------------------------------------------------------------------------


def test_the_runner_can_build_the_mac_arm() -> None:
    assert isinstance(default_mediators(ScriptedLLM([]))["mac"](), MacMediator)


def test_a_blocked_escalation_is_recorded_as_a_proposed_violation_that_never_ran() -> None:
    risky = SCENARIO.tools[3].name
    safe = SCENARIO.tools[0].name
    context = RunContext(
        run_id="r", cell_id="c", scenario_id=SCENARIO.id, seed_idx=0, seed=1,
        model="llama", p=0.0, mediator="mac",
    )  # fmt: skip
    recorder = TelemetryRecorder(context, SCENARIO)
    llm = ScriptedLLM([act(risky), act(safe), FINAL])
    trace = ReActAgent(llm, "llama", on_step=recorder.on_step).run(
        SCENARIO,
        seed=1,
        mediator=MacMediator(MATRIX),
        injector=FailureInjector(
            0.0, DrawKey(master_seed=1, cell_idx=0, scenario_id=SCENARIO.id, seed_idx=0)
        ),
        executor=StubExecutor(SCENARIO),
    )
    blocked, allowed = trace.steps[0], trace.steps[1]
    assert blocked.outcome is Outcome.ACTION and blocked.result is not None
    assert blocked.result.body == BLOCK_MESSAGE
    assert allowed.result is not None and allowed.result.body != BLOCK_MESSAGE
    calls = recorder.finish(trace).calls
    assert [(c.is_violation, c.allowed) for c in calls] == [(True, False), (False, True)]
    assert calls[0].block_reason == "MAC: role standard_user may not use tier admin"
