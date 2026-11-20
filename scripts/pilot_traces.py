"""Pick about ten varied pilot runs and write them out to be read by hand (issue #25).

Usage:
    uv run python scripts/pilot_traces.py [--runs runs/pilot] [--out runs/pilot/traces_to_read.md]

The sanity check asks for ten traces read by a person. The picks are deterministic (each stratum
takes the run whose id has the lowest SHA-256), and each stratum is something worth looking at:
a run with and without a violation, a recovery from a 503, an escalation after a 503, a block, a
lost task, an unreadable reply, the longest run, and a wrong classification. The file goes under
``runs/`` (gitignored) because it quotes model text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from privilege_drift.analysis.reproduce import finished_runs
from privilege_drift.data import DataError
from privilege_drift.data.toolprivbench import DEFAULT_PATH, load_toolprivbench
from privilege_drift.schema import Scenario
from privilege_drift.telemetry import load_summaries

SHOWN_CHARS = 700


def _rank(run_id: str) -> str:
    return hashlib.sha256(run_id.encode()).hexdigest()


Rule = tuple[str, Callable[[pd.DataFrame], pd.Series]]


def _no_mediator(d: pd.DataFrame, p: float) -> pd.Series:
    return (d.mediator == "none") & (d.p == p)


def _wrong_classification(d: pd.DataFrame, domains: dict[str, str]) -> pd.Series:
    truth = d.scenario_id.map(lambda s: domains.get(s, "").lower())
    known = d.scenario_id.isin(list(domains))
    return (
        (d.mediator == "ibac")
        & d.classifier_intent.notna()
        & known
        & (d.classifier_intent != truth)
    )


def strata(domains: dict[str, str]) -> list[Rule]:
    return [
        ("no mediator, p=0, no violation", lambda d: _no_mediator(d, 0) & (d.violations == 0)),
        ("no mediator, p=0, with a violation", lambda d: _no_mediator(d, 0) & (d.violations > 0)),
        (
            "no mediator, p=0.6, with a violation and 503s",
            lambda d: _no_mediator(d, 0.6) & (d.violations > 0) & (d.injected_calls >= 2),
        ),
        (
            "no mediator, p=0.6, 503s but no violation",
            lambda d: _no_mediator(d, 0.6) & (d.violations == 0) & (d.injected_calls >= 1),
        ),
        ("MAC blocked a call", lambda d: (d.mediator == "mac") & (d.blocked_calls > 0)),
        ("IBAC blocked a call", lambda d: (d.mediator == "ibac") & (d.blocked_calls > 0)),
        ("task not completed", lambda d: ~d.task_success),
        ("an unreadable reply", lambda d: d.parse_errors > 0),
        ("the longest run", lambda d: d.llm_calls == d.llm_calls.max()),
        ("IBAC classified the task wrongly", lambda d: _wrong_classification(d, domains)),
    ]


def pick(summaries: pd.DataFrame, domains: dict[str, str]) -> list[tuple[str, str]]:
    chosen: list[tuple[str, str]] = []
    used: set[str] = set()
    for label, rule in strata(domains):
        candidates = sorted(summaries[rule(summaries)]["run_id"], key=_rank)
        run_id = next((r for r in candidates if r not in used), None)
        if run_id is not None:
            used.add(run_id)
            chosen.append((label, run_id))
    return chosen


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render_run(label: str, path: Path, scenario: Scenario | None) -> str:
    records = _lines(path)
    raw = _lines(path.with_name(path.name.removesuffix(".jsonl") + ".raw.jsonl"))
    summary = records[-1]
    out = [f"## {label}: `{summary['run_id']}`\n"]
    if scenario is not None:
        tools = ", ".join(
            f"{t.name} [{t.tier.name.lower()}{', minimum' if t.name in scenario.min_tools else ''}]"
            for t in scenario.tools
        )
        out.append(f"**Task:** {scenario.user_task}\n\n**Tools:** {tools}\n")
    out.append(
        f"Mediator `{summary['mediator']}`, failure rate {summary['p']:g}. Ended: "
        f"{summary['stop_reason']}; violations {summary['violations']} of {summary['total_calls']} "
        f"calls; blocked {summary['blocked_calls']}; injected 503s {summary['injected_calls']}; "
        f"task success {summary['task_success']}.\n"
    )
    for rec in records[:-1]:
        index = int(rec["raw_response_ref"].rsplit(":", 1)[1])
        reply = raw[index]["text"].strip()
        if len(reply) > SHOWN_CHARS:
            reply = reply[:SHOWN_CHARS] + " [...]"
        out.append(f"**Step {rec['step_idx']}** (attempt {rec['attempt']}) model wrote:\n")
        out.append("```\n" + reply + "\n```\n")
        if rec["record_type"] == "parse_error":
            out.append(f"-> unreadable ({rec['kind']}): {rec['detail']}\n")
        else:
            verdict = "allowed" if rec["allowed"] else f"BLOCKED ({rec['block_reason']})"
            result = "injected 503" if rec["injected"] else f"HTTP {rec['http_code']}"
            flag = "  **<- above minimum tier**" if rec["is_violation"] else ""
            out.append(f"-> `{rec['tool_name']}` tier {rec['proposed_tier']}, minimum "
                       f"{rec['min_tier']}; {verdict}; result: {result}.{flag}\n")  # fmt: skip
    if summary.get("final_answer"):
        out.append(f"**Final answer:** {summary['final_answer']}\n")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs/pilot"))
    parser.add_argument("--out", type=Path, default=Path("runs/pilot/traces_to_read.md"))
    args = parser.parse_args()

    paths = {p.name.removesuffix(".jsonl"): p for p in finished_runs(args.runs)}
    if not paths:
        parser.error(f"no finished runs under {args.runs}")
    try:
        scenarios = {s.id: s for s in load_toolprivbench(DEFAULT_PATH)}
    except DataError:
        scenarios = {}
    summaries = load_summaries(list(paths.values()))
    picks = pick(summaries, {sid: s.domain for sid, s in scenarios.items()})
    parts = [
        "# Pilot traces to read (issue #25)\n",
        "For each one, ask: did the model understand the task? Was the tool choice reasonable? "
        "Did the harness show it the right result? Is anything scored wrongly? Note anything odd "
        "with the run id.\n",
    ]
    for label, run_id in picks:
        run_scenario = scenarios.get(
            str(summaries.loc[summaries.run_id == run_id, "scenario_id"].iloc[0])
        )
        parts.append(render_run(label, paths[run_id], run_scenario))
    args.out.write_text("\n---\n\n".join(parts))
    print(f"{len(picks)} traces -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
