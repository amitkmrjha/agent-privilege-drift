"""RQ3 on made-up calls where the true driver is known. No run data, no model."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from privilege_drift.analysis.predictors import (
    COMPONENT,
    Table,
    _mean_abs_shap,
    bootstrap_importance,
    build_rq3,
    calibration_table,
    collapse_collinear,
    cross_validate,
    feature_table,
    importance_table,
    plot_importance,
    render_markdown,
    vif_table,
)

SURFACES = ["none", "success", "service_unavailable", "blocked", "tool_error"]


def make_calls(n_scenarios: int = 40, per: int = 20, seed: int = 0) -> pd.DataFrame:
    """The label depends mainly on the rolling 503 rate; tokens grow with the step index."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_scenarios):
        tokens = 0
        for step in range(1, per + 1):
            rolling = float(rng.integers(0, 6)) / 5
            tokens += int(rng.integers(60, 140))
            p = 1 / (1 + np.exp(-(-2.5 + 4.0 * rolling)))
            violation = int(rng.random() < p)
            rows.append(
                {
                    "scenario_id": f"S{s:02d}",
                    "rolling_503_rate": rolling,
                    "retry_since_success": float(rng.integers(0, 4)),
                    "step_idx": step,
                    "reasoning_tokens_cum": tokens,
                    "error_surface": SURFACES[int(rng.integers(0, len(SURFACES)))],
                    "is_violation": violation,
                    "escalated_above_prior": int(violation and step > 1),
                }
            )
    return pd.DataFrame(rows)


# ---- the feature table ---------------------------------------------------------------------


def test_feature_table_one_hots_the_error_surface_with_none_as_the_base() -> None:
    table = feature_table(make_calls(2, 5))
    assert list(table.X.columns) == [
        "rolling_503_rate",
        "retry_since_success",
        "step_idx",
        "reasoning_tokens_cum",
        "surface_success",
        "surface_service_unavailable",
        "surface_blocked",
        "surface_tool_error",
    ]
    surfaces = table.X.filter(like="surface_").sum(axis=1)
    assert set(surfaces) <= {0.0, 1.0}  # a row is at most one surface, "none" is all zeros
    assert len(table.X) == len(table.y) == len(table.groups) == 10


def test_labels_primary_and_secondary() -> None:
    calls = make_calls(3, 6)
    assert feature_table(calls, "primary").y.tolist() == calls["is_violation"].tolist()
    assert feature_table(calls, "secondary").y.tolist() == calls["escalated_above_prior"].tolist()


def test_feature_table_validates_its_input() -> None:
    calls = make_calls(2, 3)
    with pytest.raises(ValueError, match="label must be"):
        feature_table(calls, "other")
    with pytest.raises(ValueError, match="no column"):
        feature_table(calls.drop(columns=["step_idx"]))
    with pytest.raises(ValueError, match="unknown error_surface"):
        feature_table(calls.assign(error_surface="weird"))
    with pytest.raises(ValueError, match="no calls"):
        feature_table(calls.iloc[0:0])


# ---- overlapping features ------------------------------------------------------------------


def test_vif_is_one_for_independent_columns_and_large_for_near_duplicates() -> None:
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=500), rng.normal(size=500)
    independent = vif_table(pd.DataFrame({"a": a, "b": b}))
    assert independent["vif"].max() < 1.1
    near = vif_table(pd.DataFrame({"a": a, "b": a + rng.normal(0, 0.05, 500), "c": b}))
    vif = dict(zip(near["feature"], near["vif"], strict=True))
    assert vif["a"] > 100 and vif["b"] > 100 and vif["c"] < 1.1


def test_collapse_replaces_overlapping_features_and_drops_constants() -> None:
    rng = np.random.default_rng(2)
    a = rng.normal(size=300)
    frame = pd.DataFrame(
        {
            "a": a,
            "b": 2 * a + rng.normal(0, 0.05, 300),
            "c": rng.normal(size=300),
            "const": np.zeros(300),
        }
    )
    result = collapse_collinear(frame)
    assert result.dropped_constant == ("const",)
    assert set(result.collapsed) == {"a", "b"}
    assert list(result.X.columns) == ["c", COMPONENT]
    assert result.explained_variance is not None and result.explained_variance > 0.95
    assert np.corrcoef(result.X[COMPONENT], frame["a"])[0, 1] > 0.9  # sign is fixed, positive


def test_nothing_is_collapsed_when_features_are_independent() -> None:
    rng = np.random.default_rng(3)
    frame = pd.DataFrame(rng.normal(size=(200, 3)), columns=["x", "y", "z"])
    result = collapse_collinear(frame)
    assert result.collapsed == () and list(result.X.columns) == ["x", "y", "z"]
    assert result.explained_variance is None


# ---- calibration and cross-validation ------------------------------------------------------


def test_calibration_table_known_values() -> None:
    p = np.array([0.05, 0.05, 0.95, 0.95])
    y = np.array([0, 0, 1, 0])
    table = calibration_table(p, y)
    assert table["bin"].tolist() == [0, 9]
    assert table["observed_rate"].tolist() == [0.0, 0.5]
    assert table["n"].tolist() == [2, 2]
    assert table["mean_predicted"].tolist() == pytest.approx([0.05, 0.95])


def test_cross_validation_finds_the_signal_and_reports_every_fold() -> None:
    result = cross_validate(feature_table(make_calls()))
    assert result.auc is not None and result.auc > 0.7
    assert result.n_splits == 5 and len(result.fold_auc) == 5
    assert (result.n_rows, result.n_scenarios) == (800, 40)
    assert 0 < result.brier < 0.25
    assert result.calibration["n"].sum() == 800


def test_cross_validation_never_trains_on_a_scenario_it_tests() -> None:
    # The scenario number is a feature and the label is random per scenario. If a scenario could
    # sit in both train and test, the model would learn the number and score far above 0.5.
    rng = np.random.default_rng(4)
    scenario = np.repeat(np.arange(40), 10)
    labels = np.repeat(rng.integers(0, 2, 40), 10)
    table = Table(
        X=pd.DataFrame({"scenario_number": scenario.astype(float)}),
        y=labels,
        groups=np.array([f"S{s}" for s in scenario]),
    )
    result = cross_validate(table)
    assert result.auc is not None and 0.3 < result.auc < 0.7


def test_cross_validation_needs_two_scenarios_and_both_classes_in_training() -> None:
    one = Table(X=pd.DataFrame({"x": [0.0, 1.0]}), y=np.array([0, 1]), groups=np.array(["a", "a"]))
    with pytest.raises(ValueError, match="two scenarios"):
        cross_validate(one)
    flat = make_calls(10, 5).assign(is_violation=0)
    with pytest.raises(ValueError, match="class"):
        cross_validate(feature_table(flat))


# ---- importance ----------------------------------------------------------------------------


def test_importance_ranks_the_true_driver_first_and_agrees_with_shap() -> None:
    table = feature_table(make_calls())
    importance = importance_table(table)
    assert importance.sort_values("rank")["feature"].iloc[0] == "rolling_503_rate"
    assert importance["rank"].min() == 1
    # the closed form used inside the bootstrap equals what shap.LinearExplainer returns
    from privilege_drift.analysis.predictors import _fit

    coef, scaled = _fit(table.X.to_numpy(dtype=float), table.y)
    assert _mean_abs_shap(coef, scaled) == pytest.approx(importance["mean_abs_shap"].to_numpy())


def test_bootstrap_is_repeatable_and_keeps_the_true_driver_on_top() -> None:
    table = feature_table(make_calls())
    first, skipped = bootstrap_importance(table, seed=1, n_boot=100)
    again, _ = bootstrap_importance(table, seed=1, n_boot=100)
    assert first.equals(again) and skipped == 0
    driver = first[first.feature == "rolling_503_rate"].iloc[0]
    assert driver["rank_ci_low"] == 1 and driver["rank_ci_high"] <= 2
    assert (first["imp_ci_low"] <= first["imp_ci_high"]).all()


def test_bootstrap_skips_and_counts_replicates_with_a_single_class() -> None:
    rng = np.random.default_rng(5)
    groups = np.repeat([f"S{i}" for i in range(10)], 6)
    y = np.zeros(60, dtype=int)
    y[:6] = rng.integers(0, 2, 6)
    y[0], y[1] = 1, 0  # only the first scenario ever has a positive
    table = Table(X=pd.DataFrame({"x": rng.normal(size=60)}), y=y, groups=groups)
    _, skipped = bootstrap_importance(table, seed=2, n_boot=100)
    assert 0 < skipped < 100


# ---- the report ----------------------------------------------------------------------------


def test_report_end_to_end(tmp_path: Path) -> None:
    report = build_rq3(make_calls(), seed=1, n_boot=50)
    # tokens grow with the step index, so the two are collapsed into one component
    assert set(report.collapse.collapsed) == {"step_idx", "reasoning_tokens_cum"}
    assert COMPONENT in set(report.importance["feature"])
    assert report.importance["feature"].iloc[0] == "rolling_503_rate"
    assert report.cv.auc is not None and report.cv.auc > 0.7
    text = render_markdown(report)
    for heading in (
        "# RQ3",
        "## Predictive performance",
        "### Calibration",
        "## Overlapping features",
        "## Importance",
    ):
        assert heading in text
    figure = plot_importance(report, tmp_path / "out" / "rq3.png")
    assert figure.is_file() and figure.stat().st_size > 0


def test_report_uses_the_secondary_label_when_asked() -> None:
    report = build_rq3(make_calls(), seed=1, label="secondary", n_boot=20)
    assert report.label == "secondary"
    assert "secondary label" in render_markdown(report)
