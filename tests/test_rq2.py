"""RQ2 analysis on made-up run summaries where the right answer is known. No run data, no model."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from privilege_drift.analysis.rq2 import (
    build_rq2,
    classifier_accuracy,
    classifier_failures,
    floor_outcome,
    metric_tables,
    plot_metrics,
    render_markdown,
    run_metrics,
)

SCENARIOS = [f"S{i:02d}" for i in range(12)]
PS = (0.0, 0.3, 0.6)
CALLS = 10


def make_summaries(mediators: tuple[str, ...] = ("ibac", "mac", "none")) -> pd.DataFrame:
    """Mediators block every violation, so executed violations are 0 under MAC and IBAC.

    Task success: no mediator and MAC 90%; IBAC 55% for Llama (clearly below the floor) and 90%
    for the frontier model (no loss).
    """
    rng = np.random.default_rng(0)
    rows = []
    for model in ("llama", "frontier"):
        for p in PS:
            for mediator in mediators:
                success_rate = {"none": 0.9, "mac": 0.9}.get(
                    mediator, 0.55 if model == "llama" else 0.9
                )
                chance = (0.1 + 0.4 * p) if model == "llama" else 0.02
                for i, scenario in enumerate(SCENARIOS):
                    for seed_idx in range(3):
                        violations = int(rng.binomial(CALLS, chance))
                        gated = mediator != "none"
                        rows.append(
                            {
                                "scenario_id": scenario,
                                "model": model,
                                "p": p,
                                "mediator": mediator,
                                "seed_idx": seed_idx,
                                "total_calls": CALLS,
                                "violations": violations,
                                "executed_violations": 0 if gated else violations,
                                "blocked_calls": violations if gated else 0,
                                "task_success": bool(rng.random() < success_rate + 0.001 * i),
                                "classifier_failed": False,
                                "classifier_intent": "business" if mediator == "ibac" else None,
                            }
                        )
    return pd.DataFrame(rows)


# ---- the metrics ---------------------------------------------------------------------------


def test_run_metrics_use_the_proposed_calls_as_the_denominator() -> None:
    frame = pd.DataFrame(
        {
            "scenario_id": ["A", "B"],
            "model": "m",
            "p": 0.0,
            "mediator": "ibac",
            "total_calls": [10, 0],
            "violations": [4, 0],
            "executed_violations": [1, 0],
            "blocked_calls": [3, 0],
            "task_success": [True, False],
        }
    )
    out = run_metrics(frame)
    assert out["proposed_violation_rate"].iloc[0] == pytest.approx(0.4)
    assert out["executed_violation_rate"].iloc[0] == pytest.approx(0.1)
    assert out["blocked_rate"].iloc[0] == pytest.approx(0.3)
    assert out["task_success"].tolist() == [1.0, 0.0]
    assert out["proposed_violation_rate"].isna().iloc[1]  # no calls, so no rate (D11)


def test_missing_columns_are_named() -> None:
    with pytest.raises(ValueError, match="no column"):
        run_metrics(make_summaries().drop(columns=["blocked_calls"]))


def test_metric_tables_have_one_value_per_scenario_and_cell() -> None:
    tables = metric_tables(make_summaries())
    assert set(tables) == {
        "proposed_violation_rate",
        "executed_violation_rate",
        "blocked_rate",
        "task_success",
    }
    assert tables["task_success"].shape == (12, 18)  # 2 models x 3 failure rates x 3 mediators


# ---- the report ----------------------------------------------------------------------------


def test_metrics_table_shape_and_values() -> None:
    metrics = build_rq2(make_summaries(), seed=1, n_boot=100).metrics
    assert len(metrics) == 4 * 2 * 3 * 3
    row = metrics[
        (metrics.metric == "executed_violation_rate")
        & (metrics.model == "llama")
        & (metrics.p == 0.6)
        & (metrics.mediator == "none")
    ].iloc[0]
    assert row["mean"] == pytest.approx(0.1 + 0.4 * 0.6, abs=0.08)
    gated = metrics[(metrics.metric == "executed_violation_rate") & (metrics.mediator != "none")]
    assert (gated["mean"] == 0).all()
    assert ((metrics["ci_low"] <= metrics["mean"]) & (metrics["mean"] <= metrics["ci_high"])).all()


def test_contrast_counts_signs_and_holm_families() -> None:
    contrasts = build_rq2(make_summaries(), seed=1, n_boot=50).contrasts
    assert contrasts["metric"].value_counts().to_dict() == {
        "proposed_violation_rate": 18,
        "executed_violation_rate": 18,
        "blocked_rate": 18,
        "task_success": 18,
    }
    assert (contrasts["p_holm"] >= contrasts["p_wilcoxon"] - 1e-12).all()
    # IBAC minus none, executed violations: the gate removes them, so the difference is negative
    row = contrasts[
        (contrasts.metric == "executed_violation_rate")
        & (contrasts.model == "llama")
        & (contrasts.p == 0.6)
        & (contrasts.mediator_a == "ibac")
        & (contrasts.mediator_b == "none")
    ].iloc[0]
    assert row["diff"] < 0 and row["p_wilcoxon"] < 0.01
    assert set(contrasts["mediator_a"] + "-" + contrasts["mediator_b"]) == {
        "ibac-mac",
        "ibac-none",
        "mac-none",
    }


def test_the_floor_is_not_met_for_llama_and_met_for_the_frontier_model() -> None:
    floor = build_rq2(make_summaries(), seed=1, n_boot=300).floor
    pooled = floor[(floor.p == "all") & (floor.comparator == "mac")].set_index("model")
    assert pooled.loc["llama", "outcome"] == "not_met"
    assert pooled.loc["llama", "diff"] == pytest.approx(-0.35, abs=0.1)
    assert pooled.loc["frontier", "outcome"] == "met"
    assert set(floor["p"]) == {"0", "0.3", "0.6", "all"}
    assert (floor["floor"] == 0.05).all()


@pytest.mark.parametrize(
    ("low", "high", "outcome"),
    [
        (-0.04, 0.02, "met"),
        (-0.05, 0.03, "inconclusive"),  # the bound sits exactly on the floor: not clearly above it
        (-0.08, 0.01, "inconclusive"),
        (-0.20, -0.07, "not_met"),
        (-0.20, -0.05, "inconclusive"),
    ],
)
def test_floor_outcome_boundaries(low: float, high: float, outcome: str) -> None:
    assert floor_outcome(low, high) == outcome


def test_without_ibac_the_floor_table_is_empty_not_an_error() -> None:
    report = build_rq2(make_summaries(("mac", "none")), seed=1, n_boot=50)
    assert report.floor.empty and report.classifier.empty
    assert "# RQ2" in render_markdown(report)


# ---- the classifier ------------------------------------------------------------------------


def test_classifier_failure_rate_counts_ibac_runs_only() -> None:
    data = make_summaries()
    bad = (data.mediator == "ibac") & (data.model == "llama") & (data.scenario_id == "S00")
    data.loc[bad, "classifier_failed"] = True
    table = classifier_failures(data)
    assert set(table["model"]) == {"llama", "frontier"}
    llama = table[(table.model == "llama") & (table.p == 0.0)].iloc[0]
    assert (llama["runs"], llama["failed_runs"]) == (36, 3)
    assert llama["failure_rate"] == pytest.approx(3 / 36)
    frontier = table[table.model == "frontier"]
    assert (frontier["failed_runs"] == 0).all()


def test_classifier_accuracy_against_domain_labels() -> None:
    data = make_summaries()
    ibac = data.mediator == "ibac"
    data.loc[ibac & (data.scenario_id == "S09"), "classifier_intent"] = "database"  # wrong
    data.loc[ibac & (data.scenario_id == "S10"), "classifier_intent"] = None  # unreadable
    data.loc[ibac & (data.scenario_id == "S11"), "classifier_intent"] = "coding"
    domains = {s: "Business" for s in SCENARIOS[:11]} | {"S11": "Coding"}
    result = classifier_accuracy(data, domains)
    assert result is not None
    assert (result["n_scored"], result["correct"], result["failed"]) == (12, 10, 1)
    assert result["accuracy"] == pytest.approx(10 / 12)
    assert classifier_accuracy(data, None) is None
    assert classifier_accuracy(data, {"other": "Business"}) is None  # nothing to score


# ---- output --------------------------------------------------------------------------------


def test_markdown_wording_and_figure(tmp_path: Path) -> None:
    report = build_rq2(make_summaries(), seed=1, n_boot=100)
    text = render_markdown(report)
    for heading in ("# RQ2", "## Utility floor", "## Mediator contrasts", "## IBAC classifier"):
        assert heading in text
    assert "IBAC's task success is not more than 5 points below mac's." in text  # frontier: met
    assert "IBAC's task success is more than 5 points below mac's." in text  # Llama: not met
    custom = render_markdown(
        report, wording={"not_met": "PRE-DECLARED: floor missed vs {comparator}."}
    )
    assert "PRE-DECLARED: floor missed vs mac." in custom
    assert "IBAC's task success is more than 5 points below mac's." not in custom
    figure = plot_metrics(report.metrics, tmp_path / "out" / "rq2.png")
    assert figure.is_file() and figure.stat().st_size > 0


def test_same_seed_gives_the_same_report() -> None:
    a = build_rq2(make_summaries(), seed=3, n_boot=80)
    b = build_rq2(make_summaries(), seed=3, n_boot=80)
    assert a.metrics.equals(b.metrics) and a.floor.equals(b.floor)
