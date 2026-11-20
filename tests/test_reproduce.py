"""The one-command analysis on a made-up runs/ folder. No model, no real run data."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from privilege_drift.analysis.reproduce import finished_runs, inputs_digest, run_analysis
from privilege_drift.telemetry import CallRecord, RunSummary, RunTelemetry, write_run
from privilege_drift.telemetry.records import ErrorSurface

SCENARIOS = [f"S{i:02d}" for i in range(8)]
PS = (0.0, 0.3, 0.6)
STAMP = datetime(2026, 1, 1, tzinfo=UTC)
CALLS_PER_RUN = 5


def make_run(
    cell_id: str, model: str, p: float, scenario: str, seed_idx: int, violations: list[bool]
) -> RunTelemetry:
    run_id = f"{cell_id}__{scenario}__s{seed_idx}"
    keys: dict[str, Any] = {
        "run_id": run_id,
        "cell_id": cell_id,
        "scenario_id": scenario,
        "seed_idx": seed_idx,
        "model": model,
        "p": p,
        "mediator": "none",
    }
    calls = []
    for step, violation in enumerate(violations, start=1):
        calls.append(
            CallRecord(
                **keys,
                step_idx=step,
                attempt=0,
                timestamp=STAMP,
                tool_name="tool",
                proposed_tier=2 if violation else 1,
                min_tier=1,
                is_violation=violation,
                escalated_above_prior=violation and step > 1,
                min_tools_untried=1,
                is_opur=violation,
                allowed=True,
                block_reason=None,
                classifier_intent=None,
                classifier_conf=None,
                injected=False,
                http_code=200,
                retry_since_success=step % 3,
                rolling_503_rate=round(p * (step % 4) / 3, 4),
                rolling_window_k=5,
                blocks_prior=0,
                error_surface=ErrorSurface.NONE if step == 1 else ErrorSurface.SUCCESS,
                reasoning_tokens_cum=90 * step,
                cot_hash="0" * 64,
                latency_ms=100.0,
                tokens_in=500,
                tokens_out=60,
                cached=False,
                possible_truncation=False,
                raw_response_ref=f"{run_id}.raw.jsonl:{step - 1}",
            )
        )
    n = len(violations)
    summary = RunSummary(
        **keys,
        seed=seed_idx,
        stop_reason="final_answer",
        final_answer="done",
        max_steps_hit=False,
        format_error=False,
        task_success=True,
        total_calls=n,
        violations=sum(violations),
        violation_rate=sum(violations) / n,
        executed_violations=sum(violations),
        blocked_calls=0,
        injected_calls=0,
        parse_errors=0,
        llm_calls=n + 1,
        tokens_in_total=500 * n,
        tokens_out_total=60 * n,
        latency_s_total=1.0,
        rolling_window_k=5,
        classifier_intent=None,
        classifier_conf=None,
        classifier_failed=False,
    )
    return RunTelemetry(records=(*calls, summary), raw=())


def make_runs(root: Path, *, violate: bool = True) -> Path:
    """Llama's violations rise with p, the frontier model's stay rare; 2 seeds per scenario."""
    rng = np.random.default_rng(0)
    for model in ("llama", "frontier"):
        for p in PS:
            cell_id = f"{model}_p{p:g}_none"
            for scenario in SCENARIOS:
                for seed_idx in range(2):
                    chance = (0.1 + 0.7 * p) if model == "llama" else 0.03
                    flags = [bool(rng.random() < chance) and violate for _ in range(CALLS_PER_RUN)]
                    write_run(
                        make_run(cell_id, model, p, scenario, seed_idx, flags), root / cell_id
                    )
    return root


def analyse(runs: Path, out: Path) -> dict[str, Any]:
    return run_analysis(runs, out, seed=7, n_boot_rq1=60, n_boot_rq3=20)


def files_under(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_every_expected_output_is_written(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs")
    numbers = analyse(runs, tmp_path / "out")
    written = set(files_under(tmp_path / "out"))
    assert {
        "numbers.json",
        "rq1.md",
        "rq3_primary.md",
        "rq3_secondary.md",
        "tables/rq1_rates.csv",
        "tables/rq1_contrasts.csv",
        "tables/rq1_page.csv",
        "tables/rq3_primary_importance.csv",
        "tables/rq3_primary_calibration.csv",
        "tables/rq3_secondary_importance.csv",
        "figures/rq1.png",
        "figures/rq3_primary.png",
        "figures/rq3_secondary.png",
    } <= written
    assert numbers["inputs"]["n_runs"] == 2 * 3 * len(SCENARIOS) * 2
    assert numbers["inputs"]["n_calls"] == numbers["inputs"]["n_runs"] * CALLS_PER_RUN
    assert (
        numbers["rq1"]["primary"]["did"]["estimate"] < 0
    )  # Llama rose, the frontier model did not
    assert numbers["rq3"]["primary"]["auc"] is not None
    assert numbers["rq3"]["primary"]["importance"][0]["rank"] == 1


def test_a_second_run_gives_byte_identical_files(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs")
    analyse(runs, tmp_path / "first")
    analyse(runs, tmp_path / "second")
    first, second = files_under(tmp_path / "first"), files_under(tmp_path / "second")
    assert first.keys() == second.keys()
    differing = [name for name in first if first[name] != second[name]]
    assert differing == []


def test_numbers_json_is_strict_json_with_no_machine_details(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs")
    analyse(runs, tmp_path / "out")
    text = (tmp_path / "out" / "numbers.json").read_text()

    def reject(constant: str) -> None:
        raise AssertionError(f"numbers.json contains {constant}")

    json.loads(text, parse_constant=reject)
    assert str(tmp_path) not in text  # no absolute paths
    assert "2026-01-01" not in text  # no timestamps copied from the records


def test_the_input_digest_follows_the_data(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs")
    first = analyse(runs, tmp_path / "a")["inputs"]["sha256"]
    assert analyse(runs, tmp_path / "b")["inputs"]["sha256"] == first
    victim = finished_runs(runs)[0]
    victim.write_text(victim.read_text() + "\n")  # still parses, but is a different file
    assert inputs_digest(finished_runs(runs)) != first


def test_only_finished_runs_are_read(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs")
    cell = runs / "llama_p0_none"
    (cell / "llama_p0_none__S00__s9.raw.jsonl").write_text("{}\n")  # replies only, no main file
    (cell / "llama_p0_none__S01__s9.jsonl").write_text("not json\n")  # unreadable main file
    (cell / "infrastructure_errors.jsonl").write_text("{}\n")
    assert len(finished_runs(runs)) == 2 * 3 * len(SCENARIOS) * 2


def test_a_part_that_cannot_be_computed_is_reported_not_fatal(tmp_path: Path) -> None:
    runs = make_runs(tmp_path / "runs", violate=False)  # no call has the positive label
    numbers = analyse(runs, tmp_path / "out")
    assert "skipped" in numbers["rq3"]["primary"]
    assert numbers["rq1"]["rates"]  # RQ1 still ran
    assert (tmp_path / "out" / "numbers.json").is_file()


def test_no_finished_runs_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "runs" / "cell").mkdir(parents=True)
    with pytest.raises(ValueError, match="no finished runs"):
        analyse(tmp_path / "runs", tmp_path / "out")
