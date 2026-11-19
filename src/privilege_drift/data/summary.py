"""Descriptive counts for a loaded benchmark, and a check against the published ones."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from privilege_drift.data.tiers import RoleTierMap
from privilege_drift.schema import Scenario


def summarise(scenarios: Iterable[Scenario]) -> dict[str, Any]:
    """Counts used by ``docs/data_summary.md`` (and later the thesis data chapter)."""
    items = list(scenarios)
    tools = [t for s in items for t in s.tools]
    per_scenario = [len(s.tools) for s in items]
    return {
        "scenarios": len(items),
        "tools": len(tools),
        "unique_tool_names": len({t.name for t in tools}),
        "by_domain": dict(sorted(Counter(s.domain for s in items).items())),
        "by_category": dict(sorted(Counter(s.category for s in items).items())),
        "tools_by_tier": {
            tier.name.lower(): n
            for tier, n in sorted(Counter(t.tier for t in tools).items(), key=lambda kv: kv[0])
        },
        "tools_per_scenario": {"min": min(per_scenario), "max": max(per_scenario)},
        "min_tools_per_scenario": dict(sorted(Counter(len(s.min_tools) for s in items).items())),
        "scenarios_with_parameters": sum(any(t.params for t in s.tools) for s in items),
        "tools_with_failure_message": sum(1 for t in tools if t.failure_message),
    }


def check_against_published(
    scenarios: Iterable[Scenario], published: Mapping[str, Any], tier_map: RoleTierMap
) -> list[str]:
    """Compare our counts with the dataset's own ``metadata/stats.json``.

    Returns one message per mismatch; an empty list means every published count matches.
    """
    items = list(scenarios)
    tools = [t for s in items for t in s.tools]
    problems: list[str] = []

    def compare(label: str, ours: Any, theirs: Any) -> None:
        if ours != theirs:
            problems.append(f"{label}: loaded {ours!r}, published {theirs!r}")

    compare("num_rows", len(items), published["num_rows"])
    compare("num_tools", len(tools), published["num_tools"])
    compare("types", dict(Counter(s.category for s in items)), published["types"])
    compare("domains", dict(Counter(s.domain for s in items)), published["domains"])
    tier_to_role = tier_map.tier_to_role()
    compare(
        "tool_roles",
        dict(Counter(tier_to_role[t.tier] for t in tools)),
        published["tool_roles"],
    )
    return problems


def render_markdown(summary: Mapping[str, Any], *, title: str = "ToolPrivBench") -> str:
    """Render ``summarise`` output as the Markdown tables in ``docs/data_summary.md``."""

    def table(heading: str, rows: Mapping[Any, Any]) -> list[str]:
        return (
            [f"### {heading}", "", "| Value | Count |", "|---|---|"]
            + [f"| {k} | {v} |" for k, v in rows.items()]
            + [""]
        )

    lines = [
        f"## {title}",
        "",
        f"- Scenarios: {summary['scenarios']}",
        f"- Tools: {summary['tools']} ({summary['unique_tool_names']} distinct names; "
        "names repeat across scenarios, never within one)",
        f"- Tools per scenario: {summary['tools_per_scenario']['min']} to "
        f"{summary['tools_per_scenario']['max']}",
        f"- Scenarios whose tools have a typed parameter schema: "
        f"{summary['scenarios_with_parameters']}",
        f"- Tools with a scenario-specific failure message: "
        f"{summary['tools_with_failure_message']}",
        "",
    ]
    lines += table("Scenarios per domain", summary["by_domain"])
    lines += table("Scenarios per category", summary["by_category"])
    lines += table("Tools per tier", summary["tools_by_tier"])
    lines += table("Least-privilege tools per scenario", summary["min_tools_per_scenario"])
    return "\n".join(lines)
