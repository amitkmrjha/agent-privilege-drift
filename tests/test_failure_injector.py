from __future__ import annotations

import math
from pathlib import Path

import pytest

from privilege_drift.data import StubExecutor, load_toolprivbench
from privilege_drift.failure import FIXED_503_BODY, DrawKey, FailureInjector, unit_draw
from privilege_drift.mediators import BLOCK_MESSAGE
from privilege_drift.schema import ToolCall, ToolResult

FIXTURE = Path(__file__).parent / "fixtures" / "toolprivbench_sample.jsonl"
KEY = DrawKey(master_seed=20261119, cell_idx=3, scenario_id="BIZ-AUTH-001", seed_idx=0)
CALL = ToolCall(name="any_tool")
N = 10_000


class CountingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, call: ToolCall) -> ToolResult:
        self.calls += 1
        return ToolResult(http_code=200, body="real answer")


def run(p: float, key: DrawKey = KEY, n: int = N) -> list[bool]:
    injector, execute = FailureInjector(p, key), CountingExecutor()
    return [injector(CALL, execute).injected for _ in range(n)]


@pytest.mark.parametrize("p", [0.3, 0.6])
def test_empirical_rate_is_close_to_p(p: float) -> None:
    rate = sum(run(p)) / N
    sd = math.sqrt(p * (1 - p) / N)
    assert abs(rate - p) < 4 * sd  # about 0.02 here; fixed key, so this cannot flake


def test_rate_holds_across_many_runs_not_just_one_key() -> None:
    hits = sum(
        sum(run(0.3, DrawKey(master_seed=1, cell_idx=c, scenario_id="S", seed_idx=s), 200))
        for c in range(18)
        for s in range(5)
    )
    assert abs(hits / (18 * 5 * 200) - 0.3) < 0.02


def test_p_zero_never_injects_and_always_runs_the_tool() -> None:
    injector, execute = FailureInjector(0.0, KEY), CountingExecutor()
    results = [injector(CALL, execute) for _ in range(2_000)]
    assert not any(r.injected for r in results)
    assert execute.calls == 2_000


def test_p_one_always_injects_and_never_runs_the_tool() -> None:
    injector, execute = FailureInjector(1.0, KEY), CountingExecutor()
    results = [injector(CALL, execute) for _ in range(2_000)]
    assert all(r == ToolResult(http_code=503, body=FIXED_503_BODY, injected=True) for r in results)
    assert execute.calls == 0


def test_a_passed_through_call_returns_the_tools_own_result_unchanged() -> None:
    result = FailureInjector(0.0, KEY)(CALL, CountingExecutor())
    assert result == ToolResult(http_code=200, body="real answer", injected=False)


def test_same_key_gives_the_same_sequence() -> None:
    assert run(0.5, n=500) == run(0.5, n=500)


@pytest.mark.parametrize(
    "other",
    [
        KEY.model_copy(update={"seed_idx": 1}),
        KEY.model_copy(update={"cell_idx": 4}),
        KEY.model_copy(update={"scenario_id": "BIZ-SCOPE-001"}),
        KEY.model_copy(update={"master_seed": 7}),
    ],
)
def test_changing_any_part_of_the_key_changes_the_sequence(other: DrawKey) -> None:
    assert run(0.5, n=500) != run(0.5, other, n=500)


def test_draws_are_in_unit_interval_and_independent_looking() -> None:
    draws = [unit_draw(KEY, n) for n in range(N)]
    assert all(0.0 <= d < 1.0 for d in draws)
    both = sum(1 for a, b in zip(draws, draws[1:], strict=False) if a < 0.3 and b < 0.3)
    assert abs(both / (N - 1) - 0.09) < 0.02  # P(two hits in a row) is p*p when independent


def test_a_resumed_run_sees_the_same_draws_as_an_uninterrupted_one() -> None:
    full = run(0.5, n=100)
    resumed_injector, execute = FailureInjector(0.5, KEY, start_index=40), CountingExecutor()
    tail = [resumed_injector(CALL, execute).injected for _ in range(60)]
    assert tail == full[40:]
    assert resumed_injector.calls_seen == 100


@pytest.mark.parametrize("p", [-0.1, 1.1, math.nan, math.inf])
def test_invalid_rate_is_rejected(p: float) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        FailureInjector(p, KEY)


def test_negative_start_index_is_rejected() -> None:
    with pytest.raises(ValueError, match="start_index"):
        FailureInjector(0.5, KEY, start_index=-1)


def test_the_503_text_is_opaque_and_differs_from_the_block_message() -> None:
    assert FIXED_503_BODY != BLOCK_MESSAGE
    assert "503" in FIXED_503_BODY
    for giveaway in ("inject", "simulat", "fake", "test", "experiment"):
        assert giveaway not in FIXED_503_BODY.lower()


def test_every_tier_can_fail_so_escalation_is_not_a_way_out() -> None:
    """Decision D19: the draw ignores the tool's tier, risk tools included."""
    scenario = load_toolprivbench(FIXTURE)[0]
    injector = FailureInjector(1.0, KEY)
    stub = StubExecutor(scenario)
    for tool in scenario.tools:
        assert injector(ToolCall(name=tool.name), stub.execute).injected is True
