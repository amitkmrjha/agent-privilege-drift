"""The statistics library against values worked out by hand. No run data, no model."""

import numpy as np
import pandas as pd
import pytest

from privilege_drift.analysis.stats import (
    bootstrap_ci,
    cliffs_delta,
    cliffs_magnitude,
    cohens_d,
    cohens_dz,
    difference_in_differences,
    holm,
    page_trend,
    paired_wilcoxon,
    scenario_means,
)


def series(values: list[float], prefix: str = "s") -> pd.Series:
    return pd.Series(values, index=[f"{prefix}{i}" for i in range(len(values))], dtype=float)


# ---- scenario-level means ------------------------------------------------------------------


def test_scenario_means_averages_the_seeds_of_each_scenario_per_cell() -> None:
    runs = pd.DataFrame(
        {
            "scenario_id": ["A", "A", "A", "B", "B", "B", "A", "A", "A", "B", "B", "B"],
            "cell_id": ["c1"] * 6 + ["c2"] * 6,
            "rate": [0, 0.5, 1, 1, 1, 1, 0, 0, 0, 0.25, 0.25, 0.25],
        }
    )
    table = scenario_means(runs, "rate")
    assert table.loc["A", "c1"] == pytest.approx(0.5)
    assert table.loc["B", "c1"] == pytest.approx(1.0)
    assert table.loc["A", "c2"] == pytest.approx(0.0)
    assert table.loc["B", "c2"] == pytest.approx(0.25)


def test_scenario_means_skips_runs_with_no_value() -> None:
    runs = pd.DataFrame(
        {"scenario_id": ["A", "A"], "cell_id": ["c", "c"], "rate": [0.5, float("nan")]}
    )
    assert scenario_means(runs, "rate").loc["A", "c"] == pytest.approx(0.5)


def test_scenario_means_names_a_missing_column() -> None:
    with pytest.raises(ValueError, match="no column"):
        scenario_means(pd.DataFrame({"scenario_id": ["A"]}), "rate")


# ---- Wilcoxon ------------------------------------------------------------------------------


def test_wilcoxon_matches_the_exact_value_when_every_difference_has_one_sign() -> None:
    # Differences 1..8, all positive: W- = 0, and the exact two-sided p is 2 / 2**8.
    a = series([2, 3, 4, 5, 6, 7, 8, 9])
    b = series([1] * 8)
    result = paired_wilcoxon(a, b)
    assert result.statistic == 0.0
    assert result.p_value == pytest.approx(2 / 256)
    assert (result.n, result.n_nonzero) == (8, 8)


def test_wilcoxon_with_no_difference_has_p_one() -> None:
    result = paired_wilcoxon(series([0.1, 0.2, 0.3]), series([0.1, 0.2, 0.3]))
    assert (result.p_value, result.n_nonzero) == (1.0, 0)


def test_wilcoxon_pairs_by_scenario_id_not_by_position() -> None:
    a = series([2, 3, 4, 5, 6, 7, 8, 9])
    shuffled = series([1] * 8).iloc[::-1]
    assert paired_wilcoxon(a, shuffled).p_value == pytest.approx(2 / 256)


def test_paired_tests_refuse_mismatched_or_missing_scenarios() -> None:
    with pytest.raises(ValueError, match="different scenarios"):
        paired_wilcoxon(series([1, 2, 3]), series([1, 2, 3], prefix="t"))
    with pytest.raises(ValueError, match="no value"):
        paired_wilcoxon(series([1, float("nan"), 3]), series([1, 2, 3]))


# ---- Page's trend --------------------------------------------------------------------------


def test_page_trend_on_a_perfect_increase_and_a_perfect_decrease() -> None:
    # Ten scenarios, three ordered conditions. Rank sums per column are 10, 20, 30 for a perfect
    # rise, so L = 1*10 + 2*20 + 3*30 = 140; for a perfect fall they are 30, 20, 10, so L = 100.
    rising = pd.DataFrame({"p0": [0.0] * 10, "p3": [0.4] * 10, "p6": [0.8] * 10})
    up = page_trend(rising)
    assert up.statistic == pytest.approx(140)
    assert up.p_value < 0.001
    assert (up.n, up.k) == (10, 3)
    down = page_trend(rising[["p6", "p3", "p0"]])
    assert down.statistic == pytest.approx(100)
    assert down.p_value > 0.99


def test_page_trend_needs_three_conditions_and_no_gaps() -> None:
    with pytest.raises(ValueError, match="three"):
        page_trend(pd.DataFrame({"a": [1.0, 2.0], "b": [2.0, 3.0]}))
    with pytest.raises(ValueError, match="no value"):
        page_trend(pd.DataFrame({"a": [1.0, float("nan")], "b": [2.0, 3.0], "c": [3.0, 4.0]}))


# ---- effect sizes --------------------------------------------------------------------------


def test_cliffs_delta_extremes_and_symmetry() -> None:
    assert cliffs_delta([4, 5, 6], [1, 2, 3]) == 1.0
    assert cliffs_delta([1, 2, 3], [4, 5, 6]) == -1.0
    assert cliffs_delta([1, 2, 3], [1, 2, 3]) == 0.0


def test_cliffs_delta_counts_ties_as_neither() -> None:
    # Pairs (6): 2>1 g, 2<3 s, 3>1 g, 3=3 tie, 4>1 g, 4>3 g -> (4 - 1) / 6.
    assert cliffs_delta([2, 3, 4], [1, 3]) == pytest.approx(0.5)


def test_cliffs_delta_needs_data() -> None:
    with pytest.raises(ValueError, match="at least one"):
        cliffs_delta([], [1])


@pytest.mark.parametrize(
    ("delta", "label"),
    [(0.0, "negligible"), (-0.146, "negligible"), (0.2, "small"), (-0.4, "medium"), (0.9, "large")],
)
def test_cliffs_magnitude_labels(delta: float, label: str) -> None:
    assert cliffs_magnitude(delta) == label


def test_cohens_dz_is_the_mean_difference_over_its_standard_deviation() -> None:
    # Differences 1, 2, 3: mean 2, sample standard deviation 1.
    assert cohens_dz(series([2, 4, 6]), series([1, 2, 3])) == pytest.approx(2.0)


def test_cohens_dz_edge_cases() -> None:
    assert cohens_dz(series([1, 2, 3]), series([1, 2, 3])) == 0.0
    with pytest.raises(ValueError, match="not defined"):
        cohens_dz(series([2, 3, 4]), series([1, 2, 3]))


def test_cohens_d_for_independent_groups_uses_the_pooled_deviation() -> None:
    # Means 2 and 4, each group has variance 1, so the pooled standard deviation is 1.
    assert cohens_d([1, 2, 3], [3, 4, 5]) == pytest.approx(-2.0)
    assert cohens_d([1, 2, 3], [1, 2, 3]) == 0.0


# ---- Holm ----------------------------------------------------------------------------------


def test_holm_adjusts_in_the_order_given() -> None:
    # Sorted 0.01, 0.03, 0.04 -> 0.01*3, 0.03*2, 0.04*1, made non-decreasing: 0.03, 0.06, 0.06.
    result = holm([0.01, 0.04, 0.03])
    assert result.p_adjusted == pytest.approx((0.03, 0.06, 0.06))
    assert result.reject == (True, False, False)


def test_holm_validates_its_input() -> None:
    with pytest.raises(ValueError, match="no p-values"):
        holm([])
    with pytest.raises(ValueError, match="between 0 and 1"):
        holm([0.5, 1.5])


# ---- bootstrap -----------------------------------------------------------------------------


def test_bootstrap_is_repeatable_for_a_seed_and_collapses_for_constant_data() -> None:
    values = np.random.default_rng(0).random(10)  # continuous, so two seeds do not tie

    def mean(idx: np.ndarray) -> float:
        return float(values[idx].mean())

    first = bootstrap_ci(10, mean, seed=1, n_boot=500)
    again = bootstrap_ci(10, mean, seed=1, n_boot=500)
    other = bootstrap_ci(10, mean, seed=2, n_boot=500)
    assert first == again
    assert (first.low, first.high) != (other.low, other.high)
    assert first.low <= first.estimate <= first.high
    assert first.estimate == pytest.approx(float(values.mean()))

    flat = np.full(10, 0.5)
    constant = bootstrap_ci(10, lambda idx: float(flat[idx].mean()), seed=3, n_boot=50)
    assert (constant.low, constant.estimate, constant.high) == (0.5, 0.5, 0.5)


def test_bootstrap_validates_its_arguments() -> None:
    with pytest.raises(ValueError, match="at least one scenario"):
        bootstrap_ci(0, lambda idx: 0.0, seed=1)
    with pytest.raises(ValueError, match="confidence"):
        bootstrap_ci(5, lambda idx: 0.0, seed=1, confidence=1.0)
    with pytest.raises(ValueError, match="n_boot"):
        bootstrap_ci(5, lambda idx: 0.0, seed=1, n_boot=0)


# ---- difference in differences -------------------------------------------------------------


def test_difference_in_differences_sign_and_value() -> None:
    # Llama's rate rises by 0.5 on average (1, 1, 0, 0 at the high rate, 0 at the low rate);
    # the frontier model's does not move. DiD = frontier delta - Llama delta = 0 - 0.5.
    zero = series([0, 0, 0, 0])
    result = difference_in_differences(
        llama_low=zero,
        llama_high=series([1, 1, 0, 0]),
        frontier_low=zero,
        frontier_high=zero,
        seed=7,
        n_boot=200,
    )
    assert result.estimate == pytest.approx(-0.5)
    assert result.low <= result.estimate <= result.high


def test_difference_in_differences_keeps_each_scenarios_values_together() -> None:
    # If every scenario has the same delta in both models, every resample gives DiD = 0 exactly.
    base = series([0.1, 0.4, 0.2, 0.9])
    result = difference_in_differences(
        llama_low=base,
        llama_high=base + 0.3,
        frontier_low=base,
        frontier_high=base + 0.3,
        seed=11,
        n_boot=200,
    )
    assert result.low == pytest.approx(0.0)
    assert result.estimate == pytest.approx(0.0)
    assert result.high == pytest.approx(0.0)


def test_difference_in_differences_refuses_misaligned_scenarios() -> None:
    ok = series([0, 0, 0])
    with pytest.raises(ValueError, match="different scenarios"):
        difference_in_differences(
            llama_low=ok,
            llama_high=ok,
            frontier_low=ok,
            frontier_high=series([0, 0, 0], prefix="t"),
            seed=1,
        )
