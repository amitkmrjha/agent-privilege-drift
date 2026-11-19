"""Deterministic tool executors: nothing real runs, the benchmark's canned output comes back."""

from __future__ import annotations

from typing import Protocol

from privilege_drift.schema import Scenario, ToolCall, ToolResult

DEFAULT_OUTPUT = '{"status": "ok"}'


class ToolExecutor(Protocol):
    """Anything that can answer a tool call. The failure injector and mediators wrap this."""

    def execute(self, call: ToolCall) -> ToolResult: ...


class StubExecutor:
    """Answers calls for one scenario from its tools' ``success_output``.

    The reply depends only on the tool name, never on the arguments or on earlier calls, so a
    run is reproducible and the executor holds no state. A tool the scenario does not offer
    gets a 404, which a ReAct agent can see and recover from.
    """

    def __init__(self, scenario: Scenario) -> None:
        self._scenario = scenario

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._scenario.tool(call.name)
        if tool is None:
            return ToolResult(http_code=404, body=f"Unknown tool: {call.name}")
        return ToolResult(http_code=200, body=tool.success_output or DEFAULT_OUTPUT)
