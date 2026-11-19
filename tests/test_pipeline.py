"""Whole-pipeline tests with a scripted model (gate G1): no live model, no network.

The scripted agent deliberately escalates. In every run it proposes, in this order:

    1. a risk tool    2. a standard tool    3. a risk tool    then gives its final answer

whatever it is told in between. That makes every number below derivable by hand:
three proposed calls, two of them violations, whichever mediator or failure rate is in use.

- ``none``: all three calls reach the injector.
- ``mac`` and ``ibac``: calls 1 and 3 are blocked (no failure draw, a 403), call 2 goes through,
  so no violation is executed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import litellm
import pandas as pd
import pytest

from privilege_drift.llm import ChatMessage, LLMClient, LLMResult, ResponseCache, load_models_config
from privilege_drift.llm.config import ModelsConfig
from privilege_drift.runner import (
    Cell,
    CellStatus,
    GridConfig,
    RetryPolicy,
    RunDeps,
    WorkItem,
    check_cell,
    expand_cells,
    plan_cell,
    read_manifest,
    run_cell,
)
from privilege_drift.schema import Tier
from privilege_drift.subsets import build_seed_schedule
from privilege_drift.telemetry import load_calls, load_summaries, run_path
from test_react_agent import FINAL, SCENARIOS, act
from test_runner import IDS, MASTER, make_grid

BY_ID = {s.id: s for s in SCENARIOS}
SCHEDULE = build_seed_schedule(IDS, n_cells=9, seeds_per_scenario=3, master_seed=MASTER)
GOLDEN = Path(__file__).parent / "golden" / "pipeline_cell.json"
GOLDEN_CELL = "llama_p0.5_mac"
NO_WAIT = RetryPolicy(attempts=1, wait_s=0.0)
CONFIG_PATH = Path(__file__).parents[1] / "configs" / "models.yaml"


# --- the scripted model --------------------------------------------------------------------


class EscalatingScript:
    """Decides what the model says, from the conversation alone (so it is easy to cache)."""

    def reply_text(self, messages: Sequence[ChatMessage]) -> str:
        first = messages[0]["content"]
        if first.startswith("Classify the user's request"):
            task = messages[1]["content"].removeprefix("Request: ")
            domain = next(s.domain.lower() for s in SCENARIOS if s.user_task == task)
            return json.dumps({"intent": domain, "confidence": 0.9})
        scenario = next(s for s in SCENARIOS if messages[1]["content"] == f"Task: {s.user_task}")
        standard = scenario.min_tools[0]
        risk = next(t.name for t in scenario.tools if t.tier is Tier.ADMIN)
        seen = sum(m["content"].startswith("Observation:") for m in messages)
        return [act(risk), act(standard), act(risk), FINAL][min(seen, 3)]


class ScriptedModel:
    """Satisfies the agent's ``Completer`` interface directly."""

    def __init__(self) -> None:
        self.script = EscalatingScript()

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        return LLMResult(
            text=self.script.reply_text(messages), tokens_in=100, tokens_out=20, latency_s=0.0,
            model_key=model_key, model="scripted", seed=seed, finish_reason="stop", raw={},
        )  # fmt: skip


class ScriptedProvider:
    """Plays the LiteLLM provider, so the real ``LLMClient`` and its cache can be used."""

    def __init__(self) -> None:
        self.script = EscalatingScript()
        self.calls = 0

    def __call__(self, **kwargs: Any) -> litellm.ModelResponse:
        self.calls += 1
        return litellm.ModelResponse(
            model=kwargs["model"],
            choices=[
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": self.script.reply_text(kwargs["messages"]),
                    },
                }
            ],
            usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        )


class NeverCalled:
    def __call__(self, **kwargs: Any) -> litellm.ModelResponse:
        raise AssertionError("the provider was called, but every answer should come from the cache")


def real_client(provider: Any, cache: ResponseCache, config: ModelsConfig) -> LLMClient:
    return LLMClient(
        config,
        cache=cache,
        completion_fn=provider,
        token_counter=lambda model, messages: 100,
        environ={},
        fingerprint_fn=lambda spec, base: (
            "digest-test" if spec.litellm_model.startswith("ollama/") else None
        ),
    )


# --- running cells -------------------------------------------------------------------------


def make_deps(llm: Any) -> RunDeps:
    return RunDeps(llm=llm, scenarios=BY_ID, master_seed=MASTER, max_steps=15, window_k=5)


def play(grid: GridConfig, cell: Cell, llm: Any) -> list[WorkItem]:
    items = plan_cell(grid, cell, IDS, SCHEDULE)
    report = run_cell(grid, cell, items, make_deps(llm), retry=NO_WAIT)
    assert report.status is CellStatus.COMPLETE and not report.failed
    return items


@pytest.fixture(scope="module")
def nine_cells(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, tuple[Cell, list[WorkItem], GridConfig]]:
    grid = make_grid(
        tmp_path_factory.mktemp("pipeline"),
        rates=(0.0, 0.5, 1.0),
        mediators=("none", "mac", "ibac"),
        seeds_per_scenario=2,
    )
    out = {}
    for cell in expand_cells(grid):
        out[cell.cell_id] = (cell, play(grid, cell, ScriptedModel()), grid)
    return out


def rows(entry: tuple[Cell, list[WorkItem], GridConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cell, items, grid = entry
    paths = [run_path(grid.runs_dir / cell.cell_id, i.run_id) for i in items]
    return load_calls(paths), load_summaries(paths)


# --- integration: 3 mediators x 3 failure rates --------------------------------------------


def test_the_grid_is_nine_cells_of_six_runs_each(nine_cells: dict[str, Any]) -> None:
    assert len(nine_cells) == 9
    assert all(len(items) == 6 for _, items, _ in nine_cells.values())  # 3 scenarios x 2 seeds


def test_every_cell_passes_its_integrity_checks(nine_cells: dict[str, Any]) -> None:
    for cell, items, grid in nine_cells.values():
        report = check_cell(cell, items, grid.runs_dir / cell.cell_id, BY_ID, MASTER)
        assert report.ok, (cell.cell_id, [c.detail for c in report.checks])
        assert read_manifest(grid.runs_dir / cell.cell_id).status is CellStatus.COMPLETE


@pytest.mark.parametrize("p", ["0", "0.5", "1"])
@pytest.mark.parametrize("mediator", ["none", "mac", "ibac"])
def test_the_agent_escalates_and_every_arm_records_it_as_a_proposed_violation(
    nine_cells: dict[str, Any], mediator: str, p: str
) -> None:
    calls, summaries = rows(nine_cells[f"llama_p{p}_{mediator}"])
    for _, run in calls.groupby("run_id"):
        run = run.sort_values("step_idx")
        assert list(run["proposed_tier"]) == [2, 1, 2]  # risk, standard, risk
        assert list(run["is_violation"]) == [True, False, True]
    assert (summaries["total_calls"] == 3).all()
    assert (summaries["violations"] == 2).all()
    assert (summaries["violation_rate"] == 2 / 3).all()
    assert (summaries["stop_reason"] == "final_answer").all()


@pytest.mark.parametrize("p", ["0", "0.5", "1"])
def test_without_a_mediator_every_call_is_allowed_and_two_violations_run(
    nine_cells: dict[str, Any], p: str
) -> None:
    calls, summaries = rows(nine_cells[f"llama_p{p}_none"])
    assert calls["allowed"].all()
    assert (summaries["blocked_calls"] == 0).all()
    assert (summaries["executed_violations"] == 2).all()


@pytest.mark.parametrize("p", ["0", "0.5", "1"])
@pytest.mark.parametrize("mediator", ["mac", "ibac"])
def test_a_correct_gate_blocks_both_escalations_and_no_violation_is_executed(
    nine_cells: dict[str, Any], mediator: str, p: str
) -> None:
    calls, summaries = rows(nine_cells[f"llama_p{p}_{mediator}"])
    for _, run in calls.groupby("run_id"):
        run = run.sort_values("step_idx")
        assert list(run["allowed"]) == [False, True, False]
        assert list(run["http_code"])[0] == list(run["http_code"])[2] == 403
        assert not run.iloc[[0, 2]]["injected"].any()  # blocked calls never get a failure draw
        assert run.iloc[0]["block_reason"].startswith(mediator.upper() + ":")
    assert (summaries["blocked_calls"] == 2).all()
    assert (summaries["executed_violations"] == 0).all()


def test_ibac_logs_its_classification_and_the_others_log_none(nine_cells: dict[str, Any]) -> None:
    domain = {s.id: s.domain.lower() for s in SCENARIOS}
    for p in ("0", "0.5", "1"):
        ibac_calls, ibac_summaries = rows(nine_cells[f"llama_p{p}_ibac"])
        assert [domain[s] for s in ibac_calls["scenario_id"]] == list(
            ibac_calls["classifier_intent"]
        )
        assert set(ibac_calls["classifier_conf"]) == {0.9}
        assert not ibac_summaries["classifier_failed"].any()
        for mediator in ("none", "mac"):
            other_calls, _ = rows(nine_cells[f"llama_p{p}_{mediator}"])
            assert other_calls["classifier_intent"].isna().all()


def test_failure_rate_zero_never_injects_and_rate_one_always_does(
    nine_cells: dict[str, Any],
) -> None:
    for mediator in ("none", "mac", "ibac"):
        zero_calls, zero = rows(nine_cells[f"llama_p0_{mediator}"])
        one_calls, one = rows(nine_cells[f"llama_p1_{mediator}"])
        assert not zero_calls["injected"].any() and (zero["injected_calls"] == 0).all()
        assert (one_calls[one_calls["allowed"]]["injected"]).all()
    none_one = rows(nine_cells["llama_p1_none"])[1]
    gated_one = rows(nine_cells["llama_p1_mac"])[1]
    assert (none_one["injected_calls"] == 3).all()  # all three calls reach the injector
    assert (gated_one["injected_calls"] == 1).all()  # only the one allowed call does


def test_task_success_follows_the_failure_rate(nine_cells: dict[str, Any]) -> None:
    for mediator in ("none", "mac", "ibac"):
        assert rows(nine_cells[f"llama_p0_{mediator}"])[1]["task_success"].all()
        assert not rows(nine_cells[f"llama_p1_{mediator}"])[1]["task_success"].any()


# --- golden: the real client and cache, metrics that must not move -------------------------

VOLATILE_CALLS = ["timestamp", "latency_ms", "cached"]
VOLATILE_SUMMARIES = ["latency_s_total"]


def metrics(cell: Cell, items: list[WorkItem], grid: GridConfig) -> str:
    paths = [run_path(grid.runs_dir / cell.cell_id, i.run_id) for i in items]
    calls = (
        load_calls(paths)
        .drop(columns=VOLATILE_CALLS)
        .sort_values(["run_id", "step_idx", "attempt"])
    )
    summaries = load_summaries(paths).drop(columns=VOLATILE_SUMMARIES).sort_values("run_id")
    body = {
        "cell_id": cell.cell_id,
        "summaries": json.loads(summaries.to_json(orient="records")),
        "calls": json.loads(calls.to_json(orient="records")),
    }
    return json.dumps(body, indent=1, sort_keys=True) + "\n"


def golden_cell(tmp_path: Path, name: str, provider: Any, cache: ResponseCache) -> str:
    grid = make_grid(
        tmp_path / name,
        rates=(0.0, 0.5, 1.0),
        mediators=("none", "mac", "ibac"),
        seeds_per_scenario=2,
    )
    cell = next(c for c in expand_cells(grid) if c.cell_id == GOLDEN_CELL)
    items = play(grid, cell, real_client(provider, cache, load_models_config(CONFIG_PATH)))
    return metrics(cell, items, grid)


def test_golden_metrics_reproduce_exactly_and_replay_from_the_cache(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache")
    provider = ScriptedProvider()
    first = golden_cell(tmp_path, "first", provider, cache)
    assert provider.calls > 0

    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(first)
    assert first == GOLDEN.read_text(), "metrics changed; if intended run `make update-golden`"

    # A second batch in a fresh directory, with a provider that must not be called.
    replay = golden_cell(tmp_path, "second", NeverCalled(), cache)
    assert replay == first


def test_the_golden_file_says_what_the_hand_calculation_says() -> None:
    body = json.loads(GOLDEN.read_text())
    assert body["cell_id"] == GOLDEN_CELL
    assert len(body["summaries"]) == 6 and len(body["calls"]) == 18
    for s in body["summaries"]:
        assert (
            s["total_calls"],
            s["violations"],
            s["executed_violations"],
            s["blocked_calls"],
        ) == (3, 2, 0, 2)
        assert s["classifier_intent"] is None  # MAC has no classifier
    assert {c["allowed"] for c in body["calls"] if c["proposed_tier"] == 2} == {False}
