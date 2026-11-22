from __future__ import annotations

import pytest

from mediator_contract import MediatorContract, scenarios
from privilege_drift.mediators import BLOCK_MESSAGE, Mediator, NoneMediator, blocked_result
from privilege_drift.schema import ToolCall


class TestNoneMediatorContract(MediatorContract):
    def make(self) -> Mediator:
        return NoneMediator()


def test_none_mediator_allows_every_tool_including_the_riskiest() -> None:
    mediator = NoneMediator()
    for scenario in scenarios():
        mediator.start_run(scenario)
        for tool in scenario.tools:
            assert mediator.gate(ToolCall(name=tool.name), None).allow is True


def test_blocked_result_is_the_one_fixed_message() -> None:
    result = blocked_result()
    assert result.body == BLOCK_MESSAGE
    assert (result.http_code, result.injected) == (403, False)


@pytest.mark.parametrize("word", ["503", "unavailable", "temporar", "try again", "retry"])
def test_block_message_cannot_be_mistaken_for_a_transient_failure(word: str) -> None:
    # D04: the block text must differ from the 503 text, or 503 opacity is lost.
    assert word not in BLOCK_MESSAGE.lower()
