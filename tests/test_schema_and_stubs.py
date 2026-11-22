from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from privilege_drift.data import RoleTierMap, StubExecutor, load_role_tier_map, load_toolprivbench
from privilege_drift.data.errors import DataError
from privilege_drift.schema import Decision, Scenario, Source, Tier, Tool, ToolCall, ToolResult

FIXTURE = Path(__file__).parent / "fixtures" / "toolprivbench_sample.jsonl"


def _tool(name: str, tier: Tier) -> Tool:
    return Tool(name=name, description="d", tier=tier)


def _scenario(**overrides: object) -> Scenario:
    fields: dict[str, object] = {
        "id": "S-1",
        "source": Source.TOOLPRIVBENCH,
        "domain": "d",
        "category": "c",
        "title": "t",
        "user_task": "do it",
        "tools": (_tool("low", Tier.USER), _tool("high", Tier.ADMIN)),
        "min_tools": ("low",),
        "min_tier": Tier.USER,
    }
    fields.update(overrides)
    return Scenario.model_validate(fields)


def test_valid_scenario_builds_and_is_frozen() -> None:
    s = _scenario()
    assert s.tool("high") is not None and s.tool("nope") is None
    with pytest.raises(ValidationError):
        s.title = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"min_tools": ()}, "min_tools is empty"),
        ({"min_tools": ("ghost",)}, "not one of the scenario's tools"),
        ({"min_tools": ("high",)}, "not at min_tier"),
        ({"min_tier": Tier.ADMIN, "min_tools": ("high",)}, "below min_tier"),
        ({"tools": (_tool("a", Tier.USER), _tool("a", Tier.ADMIN))}, "duplicate tool names"),
    ],
)
def test_inconsistent_scenarios_are_rejected(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _scenario(**overrides)


def test_tier_order_is_privilege_order() -> None:
    assert Tier.READ_ONLY < Tier.USER < Tier.ADMIN


def test_results_and_decisions() -> None:
    assert ToolResult(http_code=503, body="x", injected=True).injected
    assert ToolResult(http_code=200, body="x").injected is False
    assert Decision(allow=False, reason="over-privileged").allow is False
    assert ToolCall(name="t").arguments == {}


def test_stub_returns_the_benchmarks_canned_output() -> None:
    scenario = load_toolprivbench(FIXTURE)[0]
    stub = StubExecutor(scenario)
    tool = scenario.tools[0]
    first = stub.execute(ToolCall(name=tool.name, arguments={"x": 1}))
    again = stub.execute(ToolCall(name=tool.name, arguments={"x": 2}))
    assert first == again == ToolResult(http_code=200, body=tool.success_output or "")


def test_stub_returns_404_for_a_tool_not_offered() -> None:
    stub = StubExecutor(load_toolprivbench(FIXTURE)[0])
    result = stub.execute(ToolCall(name="delete_everything"))
    assert (result.http_code, result.injected) == (404, False)
    assert "delete_everything" in result.body


def test_tier_map_loads_and_inverts() -> None:
    tier_map = load_role_tier_map()
    assert tier_map.role_to_tier == {"standard": Tier.USER, "risk": Tier.ADMIN}
    assert tier_map.tier_to_role() == {Tier.USER: "standard", Tier.ADMIN: "risk"}


def test_tier_map_rejects_unknown_tier_and_shared_tiers() -> None:
    with pytest.raises(ValidationError, match="unknown tier 'root'"):
        RoleTierMap.model_validate({"source": "x", "role_to_tier": {"a": "root"}})
    with pytest.raises(ValidationError, match="one-to-one"):
        RoleTierMap.model_validate({"source": "x", "role_to_tier": {"a": "user", "b": "user"}})


def test_missing_tier_file_is_a_data_error(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="cannot load tier map"):
        load_role_tier_map(tmp_path / "missing.yaml")
