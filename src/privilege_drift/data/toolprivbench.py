"""Load ToolPrivBench (BAAI/ToolPrivBench, CC-BY-4.0) into the common schema, and back.

The raw files are not committed: ``make data`` downloads a pinned revision into
``data/raw/toolprivbench/``. Raw field names are validated strictly, so a changed upstream file
fails loudly instead of loading half-understood.

Reference: Yang et al., "When Lower Privileges Suffice: Investigating Over-Privileged Tool
Selection in LLM Agents", arXiv 2606.20023.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import orjson
from pydantic import BaseModel, ConfigDict, ValidationError

from privilege_drift.data.errors import DataError
from privilege_drift.data.tiers import RoleTierMap, load_role_tier_map
from privilege_drift.schema import Scenario, Source, Tool

DEFAULT_PATH = Path("data/raw/toolprivbench/data/benchmark.jsonl")
# The one place the pinned data version is written down (used by the fetch script and by the
# frozen subset, which records both so it cannot drift from the data).
REVISION = "a86a3e830a02077c8b18bac94572956c6731566a"
BENCHMARK_SHA256 = "5b96309aa2df7eacc78222f582b5cc20e2241dc8a3e9d30d45d111b172ce4122"


class _RawTool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str
    name: str
    origin: str
    description: str
    success_output: str
    # Absent on 1,494 risk tools, "" on 138 risk tools, and a message on every standard tool.
    simulation_error: str | None = None
    # Present only on the 46 scenarios that give tools a typed parameter schema.
    parameters: dict[str, Any] | None = None


class _RawScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str
    type: str
    domain: str
    title: str
    user_instruction: str
    tools: list[_RawTool]


def parse_scenario(raw: Mapping[str, Any], tier_map: RoleTierMap) -> Scenario:
    """Validate one raw record and convert it to a ``Scenario``.

    ``min_tools`` are the tools at the lowest tier present: ToolPrivBench gives no single
    ground-truth tool, only three equally sufficient standard tools (decision D05).
    """
    parsed = _RawScenario.model_validate(raw)
    tools: list[Tool] = []
    for t in parsed.tools:
        tier = tier_map.role_to_tier.get(t.role)
        if tier is None:
            raise DataError(f"{parsed.scenario_id}: tool {t.name!r} has unknown role {t.role!r}")
        tools.append(
            Tool(
                name=t.name,
                description=t.description,
                params=t.parameters,
                tier=tier,
                origin=t.origin,
                success_output=t.success_output,
                simulation_error=t.simulation_error,
            )
        )
    if not tools:
        raise DataError(f"{parsed.scenario_id}: scenario has no tools")
    min_tier = min(t.tier for t in tools)
    return Scenario(
        id=parsed.scenario_id,
        source=Source.TOOLPRIVBENCH,
        domain=parsed.domain,
        category=parsed.type,
        title=parsed.title,
        user_task=parsed.user_instruction,
        tools=tuple(tools),
        min_tools=tuple(t.name for t in tools if t.tier == min_tier),
        min_tier=min_tier,
    )


def to_raw(scenario: Scenario, tier_map: RoleTierMap) -> dict[str, Any]:
    """Convert a ``Scenario`` back to its raw ToolPrivBench record (inverse of ``parse_scenario``).

    Used by the round-trip test to prove the conversion loses nothing.
    """
    role_of = tier_map.tier_to_role()
    tools: list[dict[str, Any]] = []
    for t in scenario.tools:
        record: dict[str, Any] = {
            "role": role_of[t.tier],
            "name": t.name,
            "origin": t.origin,
            "description": t.description,
            "success_output": t.success_output,
            "simulation_error": t.simulation_error,
            "parameters": t.params,
        }
        tools.append({k: v for k, v in record.items() if v is not None})
    return {
        "scenario_id": scenario.id,
        "type": scenario.category,
        "domain": scenario.domain,
        "title": scenario.title,
        "user_instruction": scenario.user_task,
        "tools": tools,
    }


def load_toolprivbench(
    path: Path | str = DEFAULT_PATH, tier_map: RoleTierMap | None = None
) -> list[Scenario]:
    """Load every scenario from a ToolPrivBench ``benchmark.jsonl``, in file order.

    Raises ``DataError`` naming the file and line for a missing file, malformed JSON, a record
    that fails validation, or a duplicate scenario id.
    """
    path = Path(path)
    tier_map = tier_map or load_role_tier_map()
    try:
        lines = path.read_bytes().splitlines()
    except OSError as exc:
        raise DataError(f"cannot read {path} (run `make data` to download it): {exc}") from exc

    scenarios: list[Scenario] = []
    seen: set[str] = set()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            scenario = parse_scenario(orjson.loads(line), tier_map)
        except (orjson.JSONDecodeError, ValidationError, DataError, ValueError) as exc:
            raise DataError(f"{path}:{number}: {exc}") from exc
        if scenario.id in seen:
            raise DataError(f"{path}:{number}: duplicate scenario id {scenario.id!r}")
        seen.add(scenario.id)
        scenarios.append(scenario)
    return scenarios
