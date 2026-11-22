"""RQ1 analysis on made-up run summaries where the right answer is known. No run data, no model."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from privilege_drift.analysis.rq1 import (
    build_rq1,
    contrasts_table,
    plot_rates,
    render_markdown,
    scenario_table,
)

SCENARIOS = [f"S{i:02d}" for i in range(12)]
PS = (0.0, 0.3, 0.6)


def make_summaries(mediators: tuple[str, ...] = ("none", "mac")) -> pd.DataFrame:
    """Llama's rate rises by 0.6 per unit of p; the frontier model's stays flat near 0.05."""
    rng = np.random.default_rng(0)
    rows = []
    for model in ("llama", "frontier"):
        for p in PS:
            for mediator in mediators:
                for i, scenario in enumerate(SCENARIOS):
                    for seed_idx in range(3):
                        base = 0.2 + 0.6 * p if model == "llama" else 0.05
                        rate = base + 0.01 * (i % 3) + rng.normal(0, 0.005)
                        rows.append(
                            {
                                "scenario_id": scenario,
                                "model": model,
                                "p": p,
                                "mediator": mediator,
                                "seed_idx": seed_idx,
                                "violation_rate": min(max(rate, 0.0), 1.0),
                            }
                        )
    return pd.DataFrame(rows)


def test_rates_table_has_one_row_per_cell_with_the_expected_means() -> None:
    report = build_rq1(make_summaries(), seed=1, n_boot=200)
    rates = report.rates
    assert len(rates) == 2 * 3 * 2  # models x failure rates x mediators
    llama_high = rates[(rates.model == "llama") & (rates.p == 0.6) & (rates.mediator == "none")]
    assert llama_high["mean"].iloc[0] == pytest.approx(0.2 + 0.36 + 0.01, abs=0.01)
    assert (rates["ci_low"] <= rates["mean"]).all() and (rates["mean"] <= rates["ci_high"]).all()
    assert (rates["n_scenarios"] == 12).all()


def test_primary_contrast_has_the_documented_sign_and_is_significant() -> None:
    primary = build_rq1(make_summaries(), seed=1, n_boot=500).primary
    assert primary is not None
    assert primary.llama_delta == pytest.approx(0.36, abs=0.01)
    assert primary.frontier_delta == pytest.approx(0.0, abs=0.01)
    # frontier delta minus Llama delta: the frontier model rose less, so the estimate is negative
    assert primary.did.estimate == pytest.approx(-0.36, abs=0.01)
    assert primary.did.high < 0
    assert primary.p_wilcoxon < 0.01
    assert primary.cliffs_delta == -1.0 and primary.magnitude == "large"
    assert (primary.low_p, primary.high_p, primary.mediator) == (0.0, 0.6, "none")


def test_contrast_counts_and_holm_families() -> None:
    contrasts = build_rq1(make_summaries(), seed=1, n_boot=50).contrasts
    kinds = contrasts["kind"].value_counts().to_dict()
    # across p: 2 models x 2 mediators x 3 pairs of rates; between models: 3 rates x 2 mediators
    assert kinds == {"across_p": 12, "between_models": 6}
    assert (contrasts["p_holm"] >= contrasts["p_wilcoxon"] - 1e-12).all()
    llama = contrasts[(contrasts.kind == "across_p") & (contrasts.model_a == "llama")]
    assert llama["reject_holm"].all()
    assert (llama["diff"] > 0).all()  # higher failure rate minus lower failure rate
    between = contrasts[contrasts.kind == "between_models"]
    assert (between["model_a"] == "frontier").all() and (between["model_b"] == "llama").all()


def test_page_trend_finds_llamas_rise_but_not_the_flat_model() -> None:
    page = build_rq1(make_summaries(), seed=1, n_boot=50).page
    llama = page[(page.model == "llama") & (page.mediator == "none")].iloc[0]
    frontier = page[(page.model == "frontier") & (page.mediator == "none")].iloc[0]
    assert llama["p_value"] < 0.01
    assert frontier["p_value"] > 0.05
    assert (llama["n"], llama["k"]) == (12, 3)


def test_a_scenario_without_a_value_is_left_out_and_counted() -> None:
    data = make_summaries()
    gap = (data.scenario_id == "S00") & (data.model == "llama") & (data.p == 0.6)
    data.loc[gap & (data.mediator == "none"), "violation_rate"] = float("nan")
    report = build_rq1(data, seed=1, n_boot=50)
    row = report.contrasts[
        (report.contrasts.kind == "across_p")
        & (report.contrasts.model_a == "llama")
        & (report.contrasts.mediator == "none")
        & (report.contrasts.p_a == 0.6)
        & (report.contrasts.p_b == 0.0)
    ].iloc[0]
    assert (row["n"], row["n_excluded"]) == (11, 1)
    assert report.primary is not None
    assert (report.primary.n_scenarios, report.primary.n_excluded) == (11, 1)


def test_a_partly_finished_batch_does_not_crash_the_report() -> None:
    # Found on a pilot still running: only one scenario had a value at all three failure rates.
    data = make_summaries(("none",))
    data = data[data.model == "llama"]
    keep = (data.scenario_id == "S00") | (data.p == 0.0)
    report = build_rq1(data[keep], seed=1, n_boot=50)
    assert report.page.empty
    assert not report.contrasts.empty
    assert "Page's trend" in render_markdown(report)


def test_without_the_second_model_there_is_no_primary_contrast() -> None:
    data = make_summaries()
    report = build_rq1(data[data.model == "llama"], seed=1, n_boot=50)
    assert report.primary is None
    assert set(report.contrasts["kind"]) == {"across_p"}
    assert len(report.rates) == 6


def test_same_seed_gives_the_same_report() -> None:
    a = build_rq1(make_summaries(), seed=5, n_boot=100)
    b = build_rq1(make_summaries(), seed=5, n_boot=100)
    assert a.rates.equals(b.rates)
    assert a.primary == b.primary


def test_contrasts_use_each_scenarios_mean_over_seeds() -> None:
    data = make_summaries(("none",))
    table = scenario_table(data)
    assert table.shape == (12, 6)
    assert not table.isna().any().any()
    assert len(contrasts_table(table)) == 2 * 3 + 3


def test_markdown_and_figure(tmp_path: Path) -> None:
    report = build_rq1(make_summaries(), seed=1, n_boot=100)
    text = render_markdown(report)
    for heading in ("# RQ1", "## Primary contrast", "## Contrasts", "## Page's trend"):
        assert heading in text
    assert "Difference in differences (frontier minus Llama)" in text
    assert "not ruled out" in text or "upper bound" in text
    figure = plot_rates(report.rates, tmp_path / "out" / "rq1.png")
    assert figure.is_file() and figure.stat().st_size > 0


def test_the_report_says_when_the_primary_contrast_cannot_be_computed() -> None:
    data = make_summaries()
    text = render_markdown(build_rq1(data[data.model == "llama"], seed=1, n_boot=50))
    assert "Not computed" in text


def test_the_primary_contrast_can_compare_another_pair_of_models() -> None:
    """The exp-v2 amendment compares a third model with Llama using the same contrast (D32)."""
    summaries = make_summaries()
    renamed = summaries.assign(model=summaries["model"].replace({"frontier": "frontier_large"}))
    report = build_rq1(renamed, seed=1, n_boot=200, models=("llama", "frontier_large"))
    assert report.primary is not None
    assert (report.primary.first_model, report.primary.second_model) == ("llama", "frontier_large")
    assert report.primary.did.estimate < 0
    assert "frontier_large minus Llama" in render_markdown(report)
