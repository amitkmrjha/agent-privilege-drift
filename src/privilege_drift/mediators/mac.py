"""The MAC baseline: a fixed role-to-tier matrix checked at call time (decision D26).

This is a simplified re-implementation of the idea in SEAgent (Ji et al., arXiv 2601.11893):
tools carry labels fixed before the run, a role is fixed before the run, and the call is allowed
or denied by a rule over those labels, without reading the user's task. It leaves out SEAgent's
information-flow graph and path-pattern policies, which concern injection and multi-agent
messages that this experiment does not have. See D26 for exactly what is and is not kept.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from privilege_drift.data.errors import DataError
from privilege_drift.mediators.base import Intent
from privilege_drift.schema import Decision, Scenario, Tier, Tool, ToolCall

DEFAULT_MATRIX_PATH = Path("configs/policies/mac_matrix.yaml")


class RolePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allow_tiers: frozenset[Tier]

    @field_validator("allow_tiers", mode="before")
    @classmethod
    def _parse_tier_names(cls, value: Any) -> Any:
        if not isinstance(value, list | tuple | set | frozenset):
            return value
        return [Tier.parse(name) for name in value]


class MacMatrix(BaseModel):
    """Which tiers each role may call, and which role each scenario gets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_role: str
    roles: Mapping[str, RolePolicy]
    scenario_roles: Mapping[str, str] = {}

    @model_validator(mode="after")
    def _roles_exist(self) -> MacMatrix:
        if self.default_role not in self.roles:
            raise ValueError(f"default_role {self.default_role!r} is not a defined role")
        unknown = {r for r in self.scenario_roles.values() if r not in self.roles}
        if unknown:
            raise ValueError(f"scenario_roles use undefined roles: {sorted(unknown)}")
        return self

    def role_for(self, scenario_id: str) -> str:
        return self.scenario_roles.get(scenario_id, self.default_role)


def load_mac_matrix(path: Path | str = DEFAULT_MATRIX_PATH) -> MacMatrix:
    try:
        return MacMatrix.model_validate(yaml.safe_load(Path(path).read_text()))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise DataError(f"cannot load MAC matrix {path}: {exc}") from exc


@cache
def default_matrix() -> MacMatrix:
    """The matrix in ``configs/policies/mac_matrix.yaml``, read once per process."""
    return load_mac_matrix()


class MacMediator:
    """Allows a call exactly when the scenario's role may use the called tool's tier.

    A tool the scenario does not offer has no label, so the call is denied (fail closed). The
    paper allows by default when no policy matches; that default cannot arise here, because every
    tool the agent can legitimately name has a tier.
    """

    def __init__(self, matrix: MacMatrix) -> None:
        self._matrix = matrix
        self._role: str | None = None
        self._tools: dict[str, Tool] = {}

    def start_run(self, scenario: Scenario) -> None:
        self._role = self._matrix.role_for(scenario.id)
        self._tools = {t.name: t for t in scenario.tools}

    def gate(self, call: ToolCall, intent: Intent | None) -> Decision:
        if self._role is None:
            return Decision(allow=False, reason="MAC: no run started")
        tool = self._tools.get(call.name)
        if tool is None:
            return Decision(allow=False, reason=f"MAC: {call.name!r} has no label in this scenario")
        tier = tool.tier.name.lower()
        if tool.tier in self._matrix.roles[self._role].allow_tiers:
            return Decision(allow=True, reason=f"MAC: role {self._role} may use tier {tier}")
        return Decision(allow=False, reason=f"MAC: role {self._role} may not use tier {tier}")
