"""Benchmark-neutral data model shared by the loaders, agent, mediators and injector.

Every benchmark is converted into these types, so nothing downstream knows which benchmark a
scenario came from. All models are frozen: a loaded scenario can never change mid-run.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Tier(IntEnum):
    """Privilege level of a tool. Higher value = more privileged; only the order is analysed.

    ToolPrivBench has two roles and uses ``USER`` and ``ADMIN`` (decision D18); AgentDojo uses
    all three.
    """

    READ_ONLY = 0
    USER = 1
    ADMIN = 2


class Source(StrEnum):
    TOOLPRIVBENCH = "toolprivbench"
    AGENTDOJO = "agentdojo"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Tool(_Frozen):
    """One tool offered to the agent.

    ``params`` is a JSON-schema-like mapping of parameter name to spec, or ``None`` when the
    benchmark gives no parameter schema (most ToolPrivBench tools). ``success_output`` is what
    the deterministic stub returns. ``simulation_error`` is the benchmark's own scenario-specific
    failure text; ``None`` and ``""`` both mean "none" and are kept apart only so a scenario can
    be converted back to its raw form exactly (see ``Tool.failure_message``).
    """

    name: str = Field(min_length=1)
    description: str
    params: dict[str, Any] | None = None
    tier: Tier
    origin: str | None = None
    success_output: str | None = None
    simulation_error: str | None = None

    @property
    def failure_message(self) -> str | None:
        """The benchmark's failure text for this tool, or ``None`` if it defines none."""
        return self.simulation_error or None


class Scenario(_Frozen):
    """One task with its tools and the least-privilege answer.

    ``min_tools`` is the set of tools that are sufficient at the lowest privilege tier. It is a
    set, not a single tool, because ToolPrivBench gives every scenario three equally sufficient
    standard tools (decision D05). ``min_tier`` is the tier of those tools.
    """

    id: str = Field(min_length=1)
    source: Source
    domain: str
    category: str
    title: str
    user_task: str
    tools: tuple[Tool, ...]
    min_tools: tuple[str, ...]
    min_tier: Tier

    @model_validator(mode="after")
    def _check_consistency(self) -> Scenario:
        names = [t.name for t in self.tools]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.id}: duplicate tool names {sorted(names)}")
        if not self.min_tools:
            raise ValueError(f"{self.id}: min_tools is empty")
        by_name = {t.name: t for t in self.tools}
        for name in self.min_tools:
            tool = by_name.get(name)
            if tool is None:
                raise ValueError(f"{self.id}: min_tool {name!r} is not one of the scenario's tools")
            if tool.tier != self.min_tier:
                raise ValueError(f"{self.id}: min_tool {name!r} is not at min_tier")
        if any(t.tier < self.min_tier for t in self.tools):
            raise ValueError(f"{self.id}: a tool is below min_tier")
        return self

    def tool(self, name: str) -> Tool | None:
        """Look a tool up by name, or ``None`` if it is not offered in this scenario."""
        return next((t for t in self.tools if t.name == name), None)


class ToolCall(_Frozen):
    """A tool invocation proposed by the agent."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(_Frozen):
    """What a tool call returned. ``injected`` is true when the failure injector produced it."""

    http_code: int
    body: str
    injected: bool = False


class Decision(_Frozen):
    """A mediator's verdict on one proposed call."""

    allow: bool
    reason: str
